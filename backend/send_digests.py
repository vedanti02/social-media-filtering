"""Send the weekly alert digest to every parent who chose "weekly" alerts.

Run from the backend/ directory once a week, e.g. from cron:
    0 8 * * 1  cd /path/to/backend && python send_digests.py
Parents with no alerts in the last 7 days are skipped.
"""
from sqlmodel import Session, select

from main import build_weekly_digest, engine, on_startup
from models import Parent
from notifications import send_digest_notification


def main() -> None:
    on_startup()  # make sure the schema is current, same as the API server
    with Session(engine) as session:
        parents = session.exec(select(Parent).where(Parent.alert_frequency == "weekly")).all()
        sent = 0
        for parent in parents:
            digest = build_weekly_digest(session, parent)
            if digest["total_alerts"] > 0:
                send_digest_notification(parent, digest)
                sent += 1
    print(f"Sent {sent} digest(s) to {len(parents)} weekly-digest parent(s).")


if __name__ == "__main__":
    main()
