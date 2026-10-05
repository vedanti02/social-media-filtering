"""Covers the "Instant alert vs weekly digest" board card:

- Parent.alert_frequency + PATCH /parents/{id}/alert-frequency
- create_message() holds alerts back for weekly-digest parents
- build_weekly_digest / POST /parents/{id}/digest
"""
from datetime import timedelta

import main
from models import Alert, utcnow

SEVERE_TEXT = "I will kill you"


def post_message(client, child_id, text, sender):
    return client.post("/messages", json={"child_id": child_id, "text": text, "sender": sender})


def patch_notifiers(monkeypatch):
    """Spy on both senders; returns (alert_calls, digest_calls)."""
    alert_calls, digest_calls = [], []
    monkeypatch.setattr(main, "send_alert_notification", lambda p, a: alert_calls.append(a.id))
    monkeypatch.setattr(main, "send_digest_notification", lambda p, d: digest_calls.append(d))
    return alert_calls, digest_calls


def set_frequency(client, parent_id, frequency):
    return client.patch(f"/parents/{parent_id}/alert-frequency", json={"frequency": frequency})


def test_alert_frequency_defaults_to_instant(client, parent_and_child):
    parent, _ = parent_and_child
    assert client.get(f"/parents/{parent.id}").json()["alert_frequency"] == "instant"


def test_update_alert_frequency(client, parent_and_child):
    parent, _ = parent_and_child
    res = set_frequency(client, parent.id, "weekly")
    assert res.status_code == 200
    assert res.json()["alert_frequency"] == "weekly"
    assert client.get(f"/parents/{parent.id}").json()["alert_frequency"] == "weekly"


def test_update_alert_frequency_rejects_unknown_value(client, parent_and_child):
    parent, _ = parent_and_child
    assert set_frequency(client, parent.id, "hourly").status_code == 400


def test_update_alert_frequency_for_other_parent_is_404(client, parent_and_child):
    parent, _ = parent_and_child
    assert set_frequency(client, parent.id + 1, "weekly").status_code == 404


def test_weekly_mode_records_alert_without_notifying(client, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    alert_calls, _ = patch_notifiers(monkeypatch)
    set_frequency(client, parent.id, "weekly")

    post_message(client, child.id, SEVERE_TEXT, "bully1")

    alerts = client.get(f"/alerts/{parent.id}").json()
    assert len(alerts) == 1
    assert alerts[0]["notified"] is False
    assert alert_calls == []


def test_switching_back_to_instant_notifies_again(client, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    alert_calls, _ = patch_notifiers(monkeypatch)
    set_frequency(client, parent.id, "weekly")
    post_message(client, child.id, SEVERE_TEXT, "bully1")

    set_frequency(client, parent.id, "instant")
    post_message(client, child.id, SEVERE_TEXT, "bully1")

    # Not throttled: the weekly-mode alert never counted as a sent notification.
    assert len(alert_calls) == 1


def test_digest_counts_last_seven_days_per_sender(client, session, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    _, digest_calls = patch_notifiers(monkeypatch)
    now = utcnow()
    for sender, age in [("bully1", 1), ("bully1", 2), ("bully2", 3), ("old", 8)]:
        session.add(
            Alert(
                child_id=child.id,
                sender=sender,
                category="high_toxicity",
                severity_score=0.9,
                created_at=now - timedelta(days=age),
            )
        )
    session.commit()

    res = client.post(f"/parents/{parent.id}/digest")

    assert res.status_code == 200
    body = res.json()
    assert body["sent"] is True
    assert body["total_alerts"] == 3
    assert body["senders"] == [{"sender": "bully1", "count": 2}, {"sender": "bully2", "count": 1}]
    assert len(digest_calls) == 1


def test_empty_digest_is_not_sent(client, parent_and_child, monkeypatch):
    parent, _ = parent_and_child
    _, digest_calls = patch_notifiers(monkeypatch)

    body = client.post(f"/parents/{parent.id}/digest").json()

    assert body["sent"] is False
    assert body["total_alerts"] == 0
    assert digest_calls == []


def test_digest_for_other_parent_is_404(client, parent_and_child):
    parent, _ = parent_and_child
    assert client.post(f"/parents/{parent.id + 1}/digest").status_code == 404


def test_digest_skips_already_notified_and_not_a_concern(client, session, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    patch_notifiers(monkeypatch)
    for sender, notified, not_concern in [
        ("held", False, False),  # weekly mode: the digest is its only notification
        ("sent", True, False),  # already notified instantly, before switching to weekly
        ("fine", False, True),  # parent said it wasn't a problem
    ]:
        session.add(
            Alert(
                child_id=child.id,
                sender=sender,
                category="high_toxicity",
                severity_score=0.9,
                notified=notified,
                not_concern=not_concern,
            )
        )
    session.commit()

    body = client.post(f"/parents/{parent.id}/digest").json()

    assert body["senders"] == [{"sender": "held", "count": 1}]
