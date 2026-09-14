"""FastAPI entrypoint.

Run with:  uvicorn main:app --reload
"""
import os
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, create_engine, select

from classifier import classify
from models import Alert, BlockedWord, Child, Message, Parent  # noqa: F401

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

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


@app.on_event("startup")
def on_startup() -> None:
    # TODO: replace with Alembic migrations if schema changes become frequent
    SQLModel.metadata.create_all(engine)


# --- Request/response schemas -------------------------------------------------


class MessageCreate(SQLModel):
    child_id: int
    text: str
    sender: str


# --- Messages -----------------------------------------------------------------


@app.post("/messages", response_model=Message, status_code=201)
def create_message(payload: MessageCreate, session: Session = Depends(get_session)):
    child = session.get(Child, payload.child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")

    # TODO: check text against the parent's BlockedWord list before/after classification
    result = classify(payload.text)
    score = float(result["score"])
    level = result["label"]  # "low" | "medium" | "high"
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
    if is_severe:
        session.add(
            Alert(
                child_id=child.id,
                sender=payload.sender,
                # TODO: derive a harm-type category (e.g. "threat", "harassment")
                # once the classifier detects categories, not just severity.
                category="high_toxicity",
                severity_score=score,
            )
        )
        # TODO: push notification / email / SMS to the parent would hook in here
        # TODO: throttling / daily digest instead of one alert per message

    session.commit()
    session.refresh(message)
    return message


@app.get("/messages/{child_id}")
def list_messages(child_id: int):
    # TODO: query Message rows for child_id
    return []


# --- Reports ------------------------------------------------------------------


@app.get("/reports/weekly/{child_id}")
def weekly_report(child_id: int):
    # TODO: aggregate messages/alerts from the last 7 days for child_id
    return {"child_id": child_id, "total_messages": 0, "flagged": 0, "blocked": 0}


# --- Alerts -------------------------------------------------------------------


@app.get("/alerts/{parent_id}", response_model=list[Alert])
def list_alerts(
    parent_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_session),
):
    if session.get(Parent, parent_id) is None:
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
def mark_alert_read(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


# --- Blocklist ----------------------------------------------------------------


@app.post("/blocklist")
def add_blocked_word(payload: dict):
    # TODO: persist BlockedWord for the given parent
    return {"word": payload.get("word", ""), "added": True}


@app.delete("/blocklist/{word}")
def remove_blocked_word(word: str):
    # TODO: delete BlockedWord matching word
    return {"word": word, "removed": True}
