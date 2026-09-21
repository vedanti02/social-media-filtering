"""FastAPI entrypoint.

Run with:  uvicorn main:app --reload
"""
import os
from datetime import timedelta, timezone
from typing import Iterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlmodel import Session, SQLModel, create_engine, select

from auth import hash_password, new_token, verify_password
from classifier import classify
from models import (  # noqa: F401
    Alert,
    AuthToken,
    BlockedSender,
    BlockedWord,
    Child,
    Message,
    Parent,
    utcnow,
)
from notifications import send_alert_notification

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# How long to wait before re-notifying a parent about the same (child, sender)
# pair. The Alert row is still recorded every time; this only throttles the
# notification send, so repeat messages from one sender don't spam the parent.
ALERT_THROTTLE_MINUTES = int(os.environ.get("ALERT_THROTTLE_MINUTES", "15"))
NOTIFY_CHANNELS = ("email", "push")

app = FastAPI(title="Child Safety Messaging API")

# Comma-separated list of allowed frontend origins. Set ALLOWED_ORIGINS in
# production (e.g. "https://your-app.vercel.app"); defaults to the Vite dev server.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_parent(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> Parent:
    """Resolve the logged-in parent from the "Authorization: Bearer <token>" header."""
    unauthorized = HTTPException(status_code=401, detail="Not authenticated")
    if credentials is None:
        raise unauthorized
    row = session.exec(select(AuthToken).where(AuthToken.token == credentials.credentials)).first()
    parent = session.get(Parent, row.parent_id) if row else None
    if parent is None:
        raise unauthorized
    return parent


def get_owned_child(session: Session, parent: Parent, child_id: int) -> Child:
    """Fetch a child, treating one that belongs to another parent as not found."""
    child = session.get(Child, child_id)
    if child is None or child.parent_id != parent.id:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


@app.on_event("startup")
def on_startup() -> None:
    # TODO: replace with Alembic migrations if schema changes become frequent
    SQLModel.metadata.create_all(engine)


# --- Request/response schemas -------------------------------------------------


class MessageCreate(SQLModel):
    child_id: int
    text: str
    sender: str


# --- Auth ---------------------------------------------------------------------


class ParentPublic(SQLModel):
    id: int
    name: str
    email: str
    notify_channel: str


class SignupRequest(SQLModel):
    name: str
    email: str
    password: str
    child_name: str


class LoginRequest(SQLModel):
    email: str
    password: str


class AuthUser(SQLModel):
    parent_id: int
    parent_name: str
    child_id: int
    child_name: str


class AuthSession(AuthUser):
    token: str


def _child_for(session: Session, parent: Parent) -> Child:
    child = session.exec(select(Child).where(Child.parent_id == parent.id)).first()
    if child is None:
        child = Child(name="My child", parent_id=parent.id)
        session.add(child)
        session.commit()
        session.refresh(child)
    return child


def _auth_user(session: Session, parent: Parent) -> AuthUser:
    child = _child_for(session, parent)
    return AuthUser(
        parent_id=parent.id, parent_name=parent.name, child_id=child.id, child_name=child.name
    )


def _start_session(session: Session, parent: Parent) -> AuthSession:
    token = new_token()
    session.add(AuthToken(token=token, parent_id=parent.id))
    session.commit()
    return AuthSession(**_auth_user(session, parent).model_dump(), token=token)


@app.post("/auth/signup", response_model=AuthSession, status_code=201)
def signup(payload: SignupRequest, session: Session = Depends(get_session)):
    name = payload.name.strip()
    email = payload.email.strip().lower()
    child_name = payload.child_name.strip()
    if not name or not child_name:
        raise HTTPException(status_code=400, detail="Name and child name are required")
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if session.exec(select(Parent).where(Parent.email == email)).first() is not None:
        raise HTTPException(status_code=409, detail="An account with that email already exists")

    parent = Parent(name=name, email=email, password_hash=hash_password(payload.password))
    session.add(parent)
    session.commit()
    session.refresh(parent)
    session.add(Child(name=child_name, parent_id=parent.id))
    session.commit()
    return _start_session(session, parent)


@app.post("/auth/login", response_model=AuthSession)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    parent = session.exec(
        select(Parent).where(Parent.email == payload.email.strip().lower())
    ).first()
    # Same error for "no such email" and "wrong password" so the response
    # doesn't reveal which emails have accounts.
    if parent is None or not verify_password(payload.password, parent.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return _start_session(session, parent)


@app.post("/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    _: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    for row in session.exec(select(AuthToken).where(AuthToken.token == credentials.credentials)).all():
        session.delete(row)
    session.commit()
    return {"logged_out": True}


@app.get("/auth/me", response_model=AuthUser)
def me(parent: Parent = Depends(get_current_parent), session: Session = Depends(get_session)):
    return _auth_user(session, parent)


# --- Messages -----------------------------------------------------------------


@app.post("/messages", response_model=Message, status_code=201)
def create_message(
    payload: MessageCreate,
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    child = get_owned_child(session, parent, payload.child_id)

    # TODO: check text against the parent's BlockedWord list before/after classification
    result = classify(payload.text)
    score = float(result["score"])
    level = result["label"]  # "low" | "medium" | "high"

    # A blocked sender always lands as "high", regardless of what this
    # particular message says.
    is_blocked_sender = (
        session.exec(
            select(BlockedSender).where(
                BlockedSender.child_id == child.id,
                BlockedSender.sender == payload.sender,
            )
        ).first()
        is not None
    )
    if is_blocked_sender:
        level = "high"

    is_severe = level == "high"

    message = Message(
        child_id=child.id,
        text=payload.text,
        sender=payload.sender,
        score=score,
        status=level,
    )
    session.add(message)

    # A high-toxicity message is the only thing that raises an alert. The
    # alert intentionally carries no message text and no reference to the
    # Message row -- see the Alert docstring in models.py.
    alert = None
    if is_severe:
        last_notified = session.exec(
            select(Alert)
            .where(
                Alert.child_id == child.id,
                Alert.sender == payload.sender,
                Alert.notified == True,  # noqa: E712
            )
            .order_by(Alert.created_at.desc())
        ).first()
        # SQLite drops timezone info, so a round-tripped created_at may come
        # back naive; treat anything without a tzinfo as UTC (see parseUtc in
        # frontend/src/pages/Alerts.jsx for the same issue on the frontend).
        throttled = False
        if last_notified is not None:
            last_notified_at = last_notified.created_at
            if last_notified_at.tzinfo is None:
                last_notified_at = last_notified_at.replace(tzinfo=timezone.utc)
            throttled = utcnow() - last_notified_at < timedelta(minutes=ALERT_THROTTLE_MINUTES)

        alert = Alert(
            child_id=child.id,
            sender=payload.sender,
            # TODO: derive a harm-type category (e.g. "threat", "harassment")
            # once the classifier detects categories, not just severity.
            category="high_toxicity",
            severity_score=score,
            notified=not throttled,
        )
        session.add(alert)

    session.commit()
    session.refresh(message)

    if alert is not None:
        session.refresh(alert)
        if alert.notified:
            send_alert_notification(parent, alert)

    return message


@app.get("/messages/{child_id}", response_model=list[Message])
def list_messages(
    child_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    get_owned_child(session, parent, child_id)

    statement = (
        select(Message)
        .where(Message.child_id == child_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    )
    return session.exec(statement).all()


# --- Reports ------------------------------------------------------------------


def _count_messages(
    session: Session,
    child_id: int,
    start,
    end,
    statuses: Optional[tuple[str, ...]] = None,
) -> int:
    """Count Message rows for child_id in [start, end), optionally filtered by status."""
    statement = select(func.count(Message.id)).where(
        Message.child_id == child_id,
        Message.created_at >= start,
        Message.created_at < end,
    )
    if statuses:
        statement = statement.where(Message.status.in_(statuses))
    return session.exec(statement).one()


@app.get("/reports/weekly/{child_id}")
def weekly_report(
    child_id: int,
    period: str = Query(default="weekly", pattern="^(daily|weekly)$"),
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    """Aggregate messages/alerts for child_id over the requested period.

    period="daily" looks at the last 1 day, period="weekly" (default) the last
    7 days. trend_pct compares the current period's flagged-message count to
    the immediately preceding period of the same length -- e.g. "flags up 20%
    this week" on the board. trend_pct is null when there's no prior-period
    activity to compare against (rather than dividing by zero).
    """
    get_owned_child(session, parent, child_id)

    period_days = 1 if period == "daily" else 7
    now = utcnow()
    current_start = now - timedelta(days=period_days)
    previous_start = now - timedelta(days=2 * period_days)

    flagged_statuses = ("medium", "high")
    blocked_statuses = ("high",)  # high-toxicity messages are auto-hidden from the child

    total_messages = _count_messages(session, child_id, current_start, now)
    flagged = _count_messages(session, child_id, current_start, now, flagged_statuses)
    blocked = _count_messages(session, child_id, current_start, now, blocked_statuses)
    previous_flagged = _count_messages(session, child_id, previous_start, current_start, flagged_statuses)

    if previous_flagged > 0:
        trend_pct = round((flagged - previous_flagged) / previous_flagged * 100, 1)
    elif flagged > 0:
        trend_pct = None  # new activity, no prior-period baseline to compare against
    else:
        trend_pct = 0.0

    return {
        "child_id": child_id,
        "period": period,
        "period_days": period_days,
        "total_messages": total_messages,
        "flagged": flagged,
        "blocked": blocked,
        "trend_pct": trend_pct,
    }


# --- Alerts -------------------------------------------------------------------


@app.get("/alerts/{parent_id}", response_model=list[Alert])
def list_alerts(
    parent_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    if parent_id != parent.id:
        raise HTTPException(status_code=404, detail="Parent not found")

    statement = (
        select(Alert)
        .join(Child, Alert.child_id == Child.id)
        .where(Child.parent_id == parent_id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(limit)
    )
    return session.exec(statement).all()


@app.patch("/alerts/{alert_id}/read", response_model=Alert)
def mark_alert_read(
    alert_id: int,
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    alert = session.get(Alert, alert_id)
    if alert is None or session.get(Child, alert.child_id).parent_id != parent.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


# --- Notification preferences --------------------------------------------------


class NotifyChannelUpdate(SQLModel):
    channel: str


@app.get("/parents/{parent_id}", response_model=ParentPublic)
def get_parent(parent_id: int, parent: Parent = Depends(get_current_parent)):
    if parent_id != parent.id:
        raise HTTPException(status_code=404, detail="Parent not found")
    return parent


@app.patch("/parents/{parent_id}/notify-channel", response_model=ParentPublic)
def update_notify_channel(
    parent_id: int,
    payload: NotifyChannelUpdate,
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    if parent_id != parent.id:
        raise HTTPException(status_code=404, detail="Parent not found")
    if payload.channel not in NOTIFY_CHANNELS:
        raise HTTPException(
            status_code=400, detail=f"channel must be one of {NOTIFY_CHANNELS}"
        )
    parent.notify_channel = payload.channel
    session.add(parent)
    session.commit()
    session.refresh(parent)
    return parent


# --- Blocklist ----------------------------------------------------------------


@app.post("/blocklist")
def add_blocked_word(payload: dict, _: Parent = Depends(get_current_parent)):
    # TODO: persist BlockedWord for the given parent
    return {"word": payload.get("word", ""), "added": True}


@app.delete("/blocklist/{word}")
def remove_blocked_word(word: str, _: Parent = Depends(get_current_parent)):
    # TODO: delete BlockedWord matching word
    return {"word": word, "removed": True}


# --- Blocked senders ------------------------------------------------------------


class BlockedSenderCreate(SQLModel):
    child_id: int
    sender: str


@app.post("/blocked-senders", response_model=BlockedSender, status_code=201)
def block_sender(
    payload: BlockedSenderCreate,
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    get_owned_child(session, parent, payload.child_id)

    existing = session.exec(
        select(BlockedSender).where(
            BlockedSender.child_id == payload.child_id,
            BlockedSender.sender == payload.sender,
        )
    ).first()
    if existing is not None:
        return existing

    blocked = BlockedSender(child_id=payload.child_id, sender=payload.sender)
    session.add(blocked)
    session.commit()
    session.refresh(blocked)
    return blocked


@app.get("/blocked-senders/{child_id}", response_model=list[BlockedSender])
def list_blocked_senders(
    child_id: int,
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    get_owned_child(session, parent, child_id)
    statement = select(BlockedSender).where(BlockedSender.child_id == child_id)
    return session.exec(statement).all()


@app.delete("/blocked-senders/{blocked_id}")
def unblock_sender(
    blocked_id: int,
    parent: Parent = Depends(get_current_parent),
    session: Session = Depends(get_session),
):
    blocked = session.get(BlockedSender, blocked_id)
    if blocked is None or session.get(Child, blocked.child_id).parent_id != parent.id:
        raise HTTPException(status_code=404, detail="Blocked sender not found")
    session.delete(blocked)
    session.commit()
    return {"id": blocked_id, "unblocked": True}
