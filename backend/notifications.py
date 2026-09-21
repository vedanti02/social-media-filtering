"""Alert notification sender.

Stand-in for a real email/push integration -- same pattern as classifier.py,
which is a rule-based stand-in for a real toxicity model. Logs what would be
sent instead of calling an email/push provider, since no SMTP/FCM
credentials exist in this project yet.

TODO: swap the body of send_alert_notification for a real provider call
(e.g. smtplib/SendGrid for "email", FCM/web-push for "push") without
touching callers.
"""
from models import Alert, Parent


def send_alert_notification(parent: Parent, alert: Alert) -> None:
    print(
        f"[notify:{parent.notify_channel}] parent {parent.id}: "
        f"{alert.category} alert from {alert.sender}"
    )
