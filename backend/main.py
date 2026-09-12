"""FastAPI entrypoint.

Run with:  uvicorn main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine

from classifier import classify  # noqa: F401  (TODO: use in POST /messages)
from models import Alert, BlockedWord, Child, Message, Parent  # noqa: F401

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

app = FastAPI(title="Child Safety Messaging API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # TODO: replace with Alembic migrations if schema changes become frequent
    SQLModel.metadata.create_all(engine)


@app.post("/messages")
def create_message(payload: dict):
    # TODO: validate payload, run classify(), persist Message, create Alert if flagged
    return {"id": 1, "text": "", "sender": "", "score": 0.0, "status": "pending"}


@app.get("/messages/{child_id}")
def list_messages(child_id: int):
    # TODO: query Message rows for child_id
    return []


@app.get("/reports/weekly/{child_id}")
def weekly_report(child_id: int):
    # TODO: aggregate messages/alerts from the last 7 days for child_id
    return {"child_id": child_id, "total_messages": 0, "flagged": 0, "blocked": 0}


@app.get("/alerts/{parent_id}")
def list_alerts(parent_id: int):
    # TODO: query Alert rows for parent_id
    return []


@app.post("/blocklist")
def add_blocked_word(payload: dict):
    # TODO: persist BlockedWord for the given parent
    return {"word": payload.get("word", ""), "added": True}


@app.delete("/blocklist/{word}")
def remove_blocked_word(word: str):
    # TODO: delete BlockedWord matching word
    return {"word": word, "removed": True}
