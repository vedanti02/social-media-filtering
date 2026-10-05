"""SQLModel table definitions.

TODO: teammates — review field types/constraints and add relationships as needed.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Parent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    notify_channel: str = "email"  # "email" | "push"
    # "instant" sends each severe alert as it happens (subject to throttling);
    # "weekly" holds them for the digest -- see build_weekly_digest in main.py.
    alert_frequency: str = "instant"
    password_hash: str = ""  # see auth.py; never return this from an endpoint


class AuthToken(SQLModel, table=True):
    """Login session. One row per login; deleting the row is logout."""

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)
    parent_id: int = Field(foreign_key="parent.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)


class Child(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    parent_id: int = Field(foreign_key="parent.id", index=True)
    # TODO: age, linked social accounts, etc.


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="child.id", index=True)
    text: str
    sender: str
    score: float = 0.0
    status: str = "pending"  # "low" | "medium" | "high" toxicity, set by classify()
    created_at: datetime = Field(default_factory=utcnow)


class Alert(SQLModel, table=True):
    """Raised when a scanned message crosses the SEVERE threshold.

    Deliberately does NOT store the message text or a link back to the Message
    row. The parent sees what kind of thing was caught and who sent it, not
    what it said. Keep it that way.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="child.id", index=True)
    sender: str
    category: str  # classifier label, e.g. "harassment", "threat"
    severity_score: float
    is_read: bool = False
    # False when this alert was throttled -- see ALERT_THROTTLE_MINUTES in
    # main.py. The alert is still recorded either way; this only tracks
    # whether a notification was actually sent for it.
    notified: bool = False
    # True when the parent has explicitly reviewed this alert and confirmed
    # it wasn't actually a problem (distinct from is_read, which just means
    # "seen" -- a parent can read an alert without judging it either way).
    # TODO: once we have enough of these, feed them back into the classifier
    # as false-positive examples instead of just recording them.
    not_concern: bool = False
    created_at: datetime = Field(default_factory=utcnow, index=True)


class BlockedWord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: int = Field(foreign_key="parent.id", index=True)
    word: str = Field(index=True)


class BlockedSender(SQLModel, table=True):
    """A sender a parent has blocked for a specific child, e.g. from the

    Alert popup ("Block sender"). Every future message from this sender for
    this child is force-classified "high", regardless of what classify()
    says -- mirrors the intent of BlockedWord but keyed on sender instead of
    message content, since Alert never stores message text to check against.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="child.id", index=True)
    sender: str = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow)


class ScreenTimeLimit(SQLModel, table=True):
    """A parent's screen-time rules for one child. Either rule may be unset.

    allowed_start/allowed_end are "HH:MM" in `timezone` (an IANA name from the
    parent's browser), so "today" and "allowed hours" follow the family's
    clock rather than the server's UTC. A window with start > end wraps past
    midnight, e.g. 20:00-07:00.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="child.id", index=True, unique=True)
    daily_limit_minutes: Optional[int] = None
    allowed_start: Optional[str] = None
    allowed_end: Optional[str] = None
    timezone: str = "UTC"


class ScreenTimeUsage(SQLModel, table=True):
    """Minutes a child has spent in the app on one local day."""

    __table_args__ = (UniqueConstraint("child_id", "day"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="child.id", index=True)
    day: str = Field(index=True)  # "YYYY-MM-DD" in the child's ScreenTimeLimit.timezone
    minutes: int = 0
    last_heartbeat_at: Optional[datetime] = None
