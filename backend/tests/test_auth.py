"""Signup / login / logout and route protection. Uses anon_client, which has
no login bypass, so these hit the real auth dependency."""
SIGNUP = {"name": "Sam", "email": "Sam@Example.com", "password": "password123", "child_name": "Alex"}


def signup(client, **overrides):
    return client.post("/auth/signup", json={**SIGNUP, **overrides})


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_signup_creates_account_and_returns_token(anon_client):
    res = signup(anon_client)
    assert res.status_code == 201
    body = res.json()
    assert body["token"]
    assert body["parent_name"] == "Sam"
    assert body["child_name"] == "Alex"

    me = anon_client.get("/auth/me", headers=auth(body["token"]))
    assert me.status_code == 200
    assert me.json()["child_id"] == body["child_id"]


def test_signup_rejects_duplicate_email_case_insensitively(anon_client):
    assert signup(anon_client).status_code == 201
    assert signup(anon_client, email="sam@example.com").status_code == 409


def test_signup_validates_input(anon_client):
    assert signup(anon_client, password="short").status_code == 400
    assert signup(anon_client, email="not-an-email").status_code == 400
    assert signup(anon_client, child_name="  ").status_code == 400


def test_login_with_correct_and_wrong_password(anon_client):
    signup(anon_client)

    ok = anon_client.post("/auth/login", json={"email": "sam@example.com", "password": "password123"})
    assert ok.status_code == 200
    assert ok.json()["token"]

    bad = anon_client.post("/auth/login", json={"email": "sam@example.com", "password": "wrong-password"})
    assert bad.status_code == 401
    unknown = anon_client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert unknown.status_code == 401
    assert unknown.json() == bad.json()


def test_logout_invalidates_token(anon_client):
    token = signup(anon_client).json()["token"]
    assert anon_client.get("/auth/me", headers=auth(token)).status_code == 200

    assert anon_client.post("/auth/logout", headers=auth(token)).status_code == 200
    assert anon_client.get("/auth/me", headers=auth(token)).status_code == 401


def test_protected_routes_require_a_token(anon_client):
    body = signup(anon_client).json()
    child_id, parent_id = body["child_id"], body["parent_id"]

    assert anon_client.get(f"/alerts/{parent_id}").status_code == 401
    assert anon_client.get(f"/messages/{child_id}").status_code == 401
    assert anon_client.post("/messages", json={"child_id": child_id, "text": "hi", "sender": "x"}).status_code == 401
    assert anon_client.get("/auth/me", headers=auth("bogus-token")).status_code == 401


def test_password_hash_is_never_returned(anon_client):
    body = signup(anon_client).json()
    res = anon_client.get(f"/parents/{body['parent_id']}", headers=auth(body["token"]))
    assert res.status_code == 200
    assert "password" not in res.text


def test_parent_cannot_access_another_parents_data(anon_client):
    a = signup(anon_client).json()
    b = signup(anon_client, email="other@example.com", child_name="Riley").json()

    assert anon_client.get(f"/messages/{a['child_id']}", headers=auth(b["token"])).status_code == 404
    assert anon_client.get(f"/alerts/{a['parent_id']}", headers=auth(b["token"])).status_code == 404
    post = anon_client.post(
        "/messages",
        json={"child_id": a["child_id"], "text": "hi", "sender": "x"},
        headers=auth(b["token"]),
    )
    assert post.status_code == 404
    # ...while their own child works fine.
    own = anon_client.get(f"/messages/{b['child_id']}", headers=auth(b["token"]))
    assert own.status_code == 200
