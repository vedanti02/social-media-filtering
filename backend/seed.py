"""Dev seed: one parent, one child, and a handful of alerts for the Alerts page.

Run from the backend/ directory:  python seed.py
Safe to re-run -- it reuses the seed parent/child and replaces their alerts.
"""
from datetime import timedelta

from sqlmodel import Session, SQLModel, select

from auth import hash_password
from main import engine
from models import Alert, Child, Parent, utcnow

SEED_PARENT_EMAIL = "parent@example.com"
SEED_PARENT_PASSWORD = "demo1234"


def get_or_create_parent_and_child(session: Session) -> Child:
    parent = session.exec(select(Parent).where(Parent.email == SEED_PARENT_EMAIL)).first()
    if parent is None:
        parent = Parent(name="Sam Parent", email=SEED_PARENT_EMAIL)
    parent.password_hash = hash_password(SEED_PARENT_PASSWORD)
    session.add(parent)
    session.commit()
    session.refresh(parent)

    child = session.exec(select(Child).where(Child.parent_id == parent.id)).first()
    if child is None:
        child = Child(name="Alex", parent_id=parent.id)
        session.add(child)
        session.commit()
        session.refresh(child)
    return child


def seed_alerts(session: Session, child: Child) -> int:
    for old in session.exec(select(Alert).where(Alert.child_id == child.id)).all():
        session.delete(old)

    now = utcnow()
    # (sender, category, score, is_read, age)
    rows = [
        ("unknown_user_42", "threat", 0.97, False, timedelta(minutes=8)),
        ("cool_kid_99", "harassment", 0.88, False, timedelta(hours=2)),
        ("random_acct", "sexual_content", 0.91, False, timedelta(hours=9)),
        ("cool_kid_99", "harassment", 0.83, True, timedelta(days=1, hours=3)),
        ("throwaway_2026", "hate_speech", 0.94, True, timedelta(days=2)),
        ("unknown_user_42", "threat", 0.85, True, timedelta(days=5, hours=6)),
    ]
    for sender, category, score, is_read, age in rows:
        session.add(
            Alert(
                child_id=child.id,
                sender=sender,
                category=category,
                severity_score=score,
                is_read=is_read,
                created_at=now - age,
            )
        )
    session.commit()
    return len(rows)


def main() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        child = get_or_create_parent_and_child(session)
        count = seed_alerts(session, child)
        print(f"Seeded parent_id={child.parent_id} child_id={child.id} with {count} alerts.")
        print(f"Demo login: {SEED_PARENT_EMAIL} / {SEED_PARENT_PASSWORD}")


if __name__ == "__main__":
    main()
