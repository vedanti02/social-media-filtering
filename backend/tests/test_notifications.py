"""Unit tests for the notification stand-in itself (not mocked here --
this is the one place that exercises the real function body)."""
from models import Alert, Parent
from notifications import send_alert_notification


def test_send_alert_notification_logs_email_channel(capsys):
    parent = Parent(id=1, name="Sam", email="sam@example.com", notify_channel="email")
    alert = Alert(id=7, child_id=1, sender="bully1", category="high_toxicity", severity_score=0.9)

    send_alert_notification(parent, alert)

    out = capsys.readouterr().out
    assert "[notify:email]" in out
    assert "parent 1" in out
    assert "high_toxicity" in out
    assert "bully1" in out


def test_send_alert_notification_logs_push_channel(capsys):
    parent = Parent(id=2, name="Sam", email="sam@example.com", notify_channel="push")
    alert = Alert(id=8, child_id=1, sender="bully2", category="high_toxicity", severity_score=0.9)

    send_alert_notification(parent, alert)

    assert "[notify:push]" in capsys.readouterr().out
