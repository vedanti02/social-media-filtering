"""SQLModel table definitions.

TODO: teammates — review field types/constraints and add relationships as needed.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Parent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    # TODO: password hash / auth fields


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
    status: str = "pending"  # TODO: enum — e.g. "safe" | "flagged" | "blocked"
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
    created_at: datetime = Field(default_factory=utcnow, index=True)


class BlockedWord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: int = Field(foreign_key="parent.id", index=True)
    word: str = Field(index=True)
