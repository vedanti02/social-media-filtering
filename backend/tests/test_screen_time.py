"""Covers the Time control epic: /screen-time endpoints in main.py.

Time is pinned by monkeypatching main.utcnow, so lock windows and heartbeat
spacing are deterministic.
"""
from datetime import datetime, timedelta, timezone

import pytest

import main
from models import Child, Parent

# 12:00 UTC on a fixed day.
NOON_UTC = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def clock(monkeypatch):
    """A settable clock: clock.now is what main.utcnow() returns."""

    class Clock:
        now = NOON_UTC

        def advance(self, **kwargs):
            self.now += timedelta(**kwargs)

    c = Clock()
    monkeypatch.setattr(main, "utcnow", lambda: c.now)
    return c


def put_rules(client, child_id, **rules):
    body = {"daily_limit_minutes": None, "allowed_start": None, "allowed_end": None, "timezone": "UTC"}
    body.update(rules)
    return client.put(f"/screen-time/{child_id}", json=body)


def heartbeat(client, child_id):
    return client.post(f"/screen-time/{child_id}/heartbeat").json()


def test_no_rules_means_unlocked(client, parent_and_child, clock):
    _, child = parent_and_child
    status = client.get(f"/screen-time/{child.id}").json()
    assert status["locked"] is False
    assert status["minutes_used"] == 0
    assert status["minutes_remaining"] is None


def test_rules_round_trip(client, parent_and_child, clock):
    _, child = parent_and_child
    res = put_rules(
        client, child.id, daily_limit_minutes=60, allowed_start="07:00", allowed_end="21:00",
        timezone="America/New_York",
    )
    assert res.status_code == 200
    status = client.get(f"/screen-time/{child.id}").json()
    assert status["daily_limit_minutes"] == 60
    assert status["allowed_start"] == "07:00"
    assert status["allowed_end"] == "21:00"
    assert status["timezone"] == "America/New_York"
    assert status["minutes_remaining"] == 60


@pytest.mark.parametrize(
    "rules",
    [
        {"daily_limit_minutes": 0},
        {"daily_limit_minutes": 24 * 60 + 1},
        {"allowed_start": "07:00"},
        {"allowed_start": "7:00", "allowed_end": "21:00"},
        {"allowed_start": "24:00", "allowed_end": "21:00"},
        {"allowed_start": "09:00", "allowed_end": "09:00"},
        {"timezone": "Not/AZone"},
        {"timezone": "utc"},  # only exact IANA names
    ],
)
def test_invalid_rules_are_rejected(client, parent_and_child, clock, rules):
    _, child = parent_and_child
    assert put_rules(client, child.id, **rules).status_code == 400


def test_heartbeat_counts_a_minute(client, parent_and_child, clock):
    _, child = parent_and_child
    assert heartbeat(client, child.id)["minutes_used"] == 1
    clock.advance(seconds=60)
    assert heartbeat(client, child.id)["minutes_used"] == 2


def test_heartbeat_too_soon_is_ignored(client, parent_and_child, clock):
    _, child = parent_and_child
    heartbeat(client, child.id)
    clock.advance(seconds=10)  # e.g. a second open tab
    assert heartbeat(client, child.id)["minutes_used"] == 1


def test_reaching_daily_limit_locks(client, parent_and_child, clock):
    _, child = parent_and_child
    put_rules(client, child.id, daily_limit_minutes=2)

    heartbeat(client, child.id)
    clock.advance(seconds=60)
    status = heartbeat(client, child.id)

    assert status["minutes_remaining"] == 0
    assert status["locked"] is True
    assert status["lock_reason"] == "daily_limit"


def test_heartbeat_while_locked_does_not_count(client, parent_and_child, clock):
    _, child = parent_and_child
    put_rules(client, child.id, daily_limit_minutes=1)
    heartbeat(client, child.id)
    clock.advance(seconds=60)
    assert heartbeat(client, child.id)["minutes_used"] == 1


def test_usage_resets_on_a_new_local_day(client, parent_and_child, clock):
    _, child = parent_and_child
    put_rules(client, child.id, daily_limit_minutes=1)
    heartbeat(client, child.id)
    clock.advance(days=1)
    status = client.get(f"/screen-time/{child.id}").json()
    assert status["minutes_used"] == 0
    assert status["locked"] is False


def test_outside_allowed_hours_locks(client, parent_and_child, clock):
    _, child = parent_and_child
    status = put_rules(client, child.id, allowed_start="07:00", allowed_end="11:00").json()
    assert status["locked"] is True
    assert status["lock_reason"] == "outside_hours"


def test_inside_allowed_hours_is_unlocked(client, parent_and_child, clock):
    _, child = parent_and_child
    status = put_rules(client, child.id, allowed_start="07:00", allowed_end="21:00").json()
    assert status["locked"] is False


def test_allowed_hours_use_the_childs_timezone(client, parent_and_child, clock):
    _, child = parent_and_child
    # 12:00 UTC is 08:00 in New York (EDT), before a 09:00 start.
    status = put_rules(
        client, child.id, allowed_start="09:00", allowed_end="21:00", timezone="America/New_York"
    ).json()
    assert status["lock_reason"] == "outside_hours"


def test_overnight_window_wraps_past_midnight(client, parent_and_child, clock):
    _, child = parent_and_child
    # Allowed 20:00-02:00: noon is outside, 23:00 and 01:00 are inside.
    assert put_rules(client, child.id, allowed_start="20:00", allowed_end="02:00").json()["locked"] is True
    clock.advance(hours=11)
    assert client.get(f"/screen-time/{child.id}").json()["locked"] is False
    clock.advance(hours=2)
    assert client.get(f"/screen-time/{child.id}").json()["locked"] is False


def test_clearing_rules_unlocks(client, parent_and_child, clock):
    _, child = parent_and_child
    put_rules(client, child.id, allowed_start="07:00", allowed_end="11:00")
    assert put_rules(client, child.id).json()["locked"] is False


def test_other_parents_child_is_404(client, session, parent_and_child, clock):
    other = Parent(name="Other", email="other@example.com")
    session.add(other)
    session.commit()
    session.refresh(other)
    other_child = Child(name="Kid", parent_id=other.id)
    session.add(other_child)
    session.commit()
    session.refresh(other_child)

    assert client.get(f"/screen-time/{other_child.id}").status_code == 404
    assert put_rules(client, other_child.id, daily_limit_minutes=5).status_code == 404
    assert client.post(f"/screen-time/{other_child.id}/heartbeat").status_code == 404


def test_cors_allows_put_from_frontend(client, parent_and_child):
    # The browser preflights PUT; TestClient only does so when told to.
    res = client.options(
        f"/screen-time/{parent_and_child[1].id}",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "PUT"},
    )
    assert res.status_code == 200
