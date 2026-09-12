"""SQLModel table definitions.

TODO: teammates — review field types/constraints and add relationships as needed.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


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
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: int = Field(foreign_key="parent.id", index=True)
    message_id: int = Field(foreign_key="message.id")
    reason: str
    seen: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BlockedWord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: int = Field(foreign_key="parent.id", index=True)
    word: str = Field(index=True)
