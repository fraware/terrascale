def test_index(client) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "User Service" in r.text


def test_health(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready(client) -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


def test_create_and_get_user_caching(client) -> None:
    create = client.post("/users/", json={"username": "integration_user"})
    assert create.status_code == 201
    body = create.json()
    user_id = body["id"]
    assert body["username"] == "integration_user"

    # POST warms Redis; clear key to exercise DB read path once.
    client.app.state.redis.delete(f"user:{user_id}")

    first = client.get(f"/users/{user_id}")
    assert first.status_code == 200
    assert first.json()["username"] == "integration_user"
    assert first.json()["cached"] is False

    second = client.get(f"/users/{user_id}")
    assert second.status_code == 200
    assert second.json()["cached"] is True


def test_create_user_conflict(client) -> None:
    u = "conflict_user"
    assert client.post("/users/", json={"username": u}).status_code == 201
    dup = client.post("/users/", json={"username": u})
    assert dup.status_code == 409


def test_get_user_not_found(client) -> None:
    r = client.get("/users/999999")
    assert r.status_code == 404
