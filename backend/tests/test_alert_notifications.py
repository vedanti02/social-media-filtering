"""Covers the two board cards implemented in main.py's create_message():

- "Pick channel: push, email"       -> Parent.notify_channel + /parents endpoints
- "Throttle repeat alerts per thread" -> Alert.notified + ALERT_THROTTLE_MINUTES

send_alert_notification is mocked throughout so these tests assert on *when*
a notification would be sent, not on any real email/push delivery.
"""
import main

SEVERE_TEXT = "I will kill you"
LOW_TEXT = "hey, how's it going"


def post_message(client, child_id, text, sender):
    return client.post("/messages", json={"child_id": child_id, "text": text, "sender": sender})


def patch_notifier(monkeypatch):
    """Replace main.send_alert_notification with a spy; returns the call list."""
    calls = []
    monkeypatch.setattr(
        main, "send_alert_notification", lambda parent, alert: calls.append((parent.id, alert.id))
    )
    return calls


# --- Alert creation & notification on the happy path --------------------------


def test_low_toxicity_message_creates_no_alert_and_no_notification(client, parent_and_child, monkeypatch):
    _, child = parent_and_child
    calls = patch_notifier(monkeypatch)

    res = post_message(client, child.id, LOW_TEXT, "friend1")

    assert res.status_code == 201
    assert client.get(f"/alerts/{child.parent_id}").json() == []
    assert calls == []


def test_high_toxicity_message_creates_alert_and_notifies(client, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    calls = patch_notifier(monkeypatch)

    res = post_message(client, child.id, SEVERE_TEXT, "bully1")
    assert res.status_code == 201
    assert res.json()["status"] == "high"

    alerts = client.get(f"/alerts/{parent.id}").json()
    assert len(alerts) == 1
    assert alerts[0]["notified"] is True
    assert alerts[0]["sender"] == "bully1"

    assert calls == [(parent.id, alerts[0]["id"])]


# --- Throttling: repeat alerts from the same (child, sender) "thread" ---------


def test_second_severe_message_from_same_sender_is_throttled(client, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    calls = patch_notifier(monkeypatch)

    post_message(client, child.id, SEVERE_TEXT, "bully1")
    post_message(client, child.id, SEVERE_TEXT, "bully1")

    alerts = client.get(f"/alerts/{parent.id}").json()
    assert len(alerts) == 2  # both are still recorded for the inbox/audit trail
    notified_flags = sorted(a["notified"] for a in alerts)
    assert notified_flags == [False, True]

    # Only the first alert triggered an actual notification.
    assert len(calls) == 1


def test_third_severe_message_still_throttled_within_window(client, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    calls = patch_notifier(monkeypatch)

    for _ in range(3):
        post_message(client, child.id, SEVERE_TEXT, "bully1")

    alerts = client.get(f"/alerts/{parent.id}").json()
    assert len(alerts) == 3
    assert sum(a["notified"] for a in alerts) == 1
    assert len(calls) == 1


def test_notification_resumes_once_the_throttle_window_elapses(client, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    calls = patch_notifier(monkeypatch)

    post_message(client, child.id, SEVERE_TEXT, "bully1")
    assert len(calls) == 1

    # Simulate the throttle window having elapsed without waiting in real time.
    monkeypatch.setattr(main, "ALERT_THROTTLE_MINUTES", 0)
    post_message(client, child.id, SEVERE_TEXT, "bully1")

    assert len(calls) == 2
    alerts = client.get(f"/alerts/{parent.id}").json()
    assert all(a["notified"] for a in alerts)


def test_different_sender_is_not_throttled(client, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    calls = patch_notifier(monkeypatch)

    post_message(client, child.id, SEVERE_TEXT, "bully1")
    post_message(client, child.id, SEVERE_TEXT, "bully2")

    alerts = client.get(f"/alerts/{parent.id}").json()
    assert all(a["notified"] for a in alerts)
    assert len(calls) == 2


def test_different_child_is_not_throttled(client, parent_and_child, session, monkeypatch):
    from models import Child

    parent, child1 = parent_and_child
    child2 = Child(name="Sibling", parent_id=parent.id)
    session.add(child2)
    session.commit()
    session.refresh(child2)

    calls = patch_notifier(monkeypatch)

    post_message(client, child1.id, SEVERE_TEXT, "bully1")
    post_message(client, child2.id, SEVERE_TEXT, "bully1")

    alerts = client.get(f"/alerts/{parent.id}").json()
    assert all(a["notified"] for a in alerts)
    assert len(calls) == 2


def test_throttled_alert_still_visible_and_markable_as_read(client, parent_and_child, monkeypatch):
    """Throttling only silences the notification -- the alert itself is a
    normal Alert row the parent can still see and act on."""
    parent, child = parent_and_child
    patch_notifier(monkeypatch)

    post_message(client, child.id, SEVERE_TEXT, "bully1")
    post_message(client, child.id, SEVERE_TEXT, "bully1")

    alerts = client.get(f"/alerts/{parent.id}").json()
    throttled = next(a for a in alerts if not a["notified"])

    res = client.patch(f"/alerts/{throttled['id']}/read")
    assert res.status_code == 200
    assert res.json()["is_read"] is True


# --- Notification channel preference -------------------------------------------


def test_get_parent_returns_default_notify_channel(client, parent_and_child):
    parent, _ = parent_and_child
    res = client.get(f"/parents/{parent.id}")
    assert res.status_code == 200
    assert res.json()["notify_channel"] == "email"


def test_get_parent_404_for_unknown_parent(client):
    res = client.get("/parents/999")
    assert res.status_code == 404


def test_update_notify_channel_to_push_persists(client, parent_and_child):
    parent, _ = parent_and_child

    res = client.patch(f"/parents/{parent.id}/notify-channel", json={"channel": "push"})
    assert res.status_code == 200
    assert res.json()["notify_channel"] == "push"

    # Persisted, not just returned -- a fresh GET reflects it too.
    assert client.get(f"/parents/{parent.id}").json()["notify_channel"] == "push"


def test_update_notify_channel_rejects_invalid_value(client, parent_and_child):
    parent, _ = parent_and_child

    res = client.patch(f"/parents/{parent.id}/notify-channel", json={"channel": "sms"})
    assert res.status_code == 400
    # Unchanged.
    assert client.get(f"/parents/{parent.id}").json()["notify_channel"] == "email"


def test_update_notify_channel_404_for_unknown_parent(client):
    res = client.patch("/parents/999/notify-channel", json={"channel": "push"})
    assert res.status_code == 404


def test_notification_uses_the_parents_selected_channel(client, parent_and_child, monkeypatch):
    parent, child = parent_and_child
    channels_used = []
    monkeypatch.setattr(
        main, "send_alert_notification", lambda p, alert: channels_used.append(p.notify_channel)
    )

    client.patch(f"/parents/{parent.id}/notify-channel", json={"channel": "push"})
    post_message(client, child.id, SEVERE_TEXT, "bully1")

    assert channels_used == ["push"]
