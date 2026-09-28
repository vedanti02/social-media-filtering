"""Covers the word-blocklist board card: adding/removing a word must persist
(the endpoints used to return fake success without touching the database),
and a blocked word should force a message to "high" just like a blocked
sender already does.
"""


def test_add_blocked_word_persists_and_lists(client, parent_and_child):
    res = client.post("/blocklist", json={"word": "Meanie"})
    assert res.status_code == 201
    assert res.json()["word"] == "meanie"  # stored lowercase

    listed = client.get("/blocklist").json()
    assert [w["word"] for w in listed] == ["meanie"]


def test_adding_the_same_word_twice_does_not_duplicate(client, parent_and_child):
    client.post("/blocklist", json={"word": "meanie"})
    client.post("/blocklist", json={"word": "MEANIE"})

    listed = client.get("/blocklist").json()
    assert len(listed) == 1


def test_remove_blocked_word_persists(client, parent_and_child):
    client.post("/blocklist", json={"word": "meanie"})

    res = client.delete("/blocklist/meanie")
    assert res.status_code == 200
    assert res.json()["removed"] is True
    assert client.get("/blocklist").json() == []


def test_removing_a_word_that_was_never_blocked_reports_no_match(client, parent_and_child):
    res = client.delete("/blocklist/never-added")
    assert res.status_code == 200
    assert res.json()["removed"] is False


def test_message_containing_a_blocked_word_is_forced_high(client, parent_and_child):
    _, child = parent_and_child
    client.post("/blocklist", json={"word": "meanie"})

    res = client.post(
        "/messages", json={"child_id": child.id, "text": "you're such a meanie", "sender": "friend1"}
    )
    assert res.status_code == 201
    assert res.json()["status"] == "high"


def test_blocklist_is_scoped_per_parent(anon_client):
    from tests.test_auth import auth, signup

    a = signup(anon_client).json()
    b = signup(anon_client, email="other@example.com", child_name="Riley").json()

    anon_client.post("/blocklist", json={"word": "meanie"}, headers=auth(a["token"]))

    assert anon_client.get("/blocklist", headers=auth(b["token"])).json() == []
