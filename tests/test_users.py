"""
Test suite: Users
Tests POST /users, GET /users/{id}, PUT /users/{id}, GET /users/{id}/tweets
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_user(
    client: TestClient,
    username: str = "alice",
    display_name: str = "Alice",
    bio: str | None = None,
) -> dict:
    payload: dict = {"username": username, "display_name": display_name}
    if bio is not None:
        payload["bio"] = bio
    r = client.post("/users", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _create_tweet(client: TestClient, user_id: str, content: str = "Hello!") -> dict:
    r = client.post("/tweets", json={"user_id": user_id, "content": content})
    assert r.status_code == 201, r.text
    return r.json()


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestCreateUser:
    def test_create_user_returns_201(self, client: TestClient) -> None:
        """POST /users with valid data returns 201."""
        r = client.post(
            "/users",
            json={"username": "alice", "display_name": "Alice", "bio": "Hi!"},
        )
        assert r.status_code == 201

    def test_create_user_response_shape(self, client: TestClient) -> None:
        """Response contains id, username, display_name, bio, created_at and zero counts."""
        r = client.post(
            "/users",
            json={"username": "bob", "display_name": "Bob", "bio": "Bio here"},
        )
        data = r.json()
        assert "id" in data
        assert data["username"] == "bob"
        assert data["display_name"] == "Bob"
        assert data["bio"] == "Bio here"
        assert "created_at" in data
        assert data["followers_count"] == 0
        assert data["following_count"] == 0
        assert data["tweet_count"] == 0

    def test_create_user_bio_optional(self, client: TestClient) -> None:
        """Bio field is optional; defaults to None when omitted."""
        r = client.post("/users", json={"username": "charlie", "display_name": "Charlie"})
        assert r.status_code == 201
        assert r.json()["bio"] is None

    def test_create_user_duplicate_username_409(self, client: TestClient) -> None:
        """POST /users with a duplicate username returns 409."""
        _create_user(client, "alice")
        r = client.post("/users", json={"username": "alice", "display_name": "Alice2"})
        assert r.status_code == 409

    def test_create_user_duplicate_username_case_insensitive(self, client: TestClient) -> None:
        """Duplicate detection is case-insensitive (ALICE == alice)."""
        _create_user(client, "alice")
        r = client.post("/users", json={"username": "ALICE", "display_name": "Alice Upper"})
        assert r.status_code == 409

    def test_create_user_empty_username_422(self, client: TestClient) -> None:
        """POST /users with empty username returns 422."""
        r = client.post("/users", json={"username": "", "display_name": "Alice"})
        assert r.status_code == 422

    def test_create_user_empty_display_name_422(self, client: TestClient) -> None:
        """POST /users with empty display_name returns 422."""
        r = client.post("/users", json={"username": "alice", "display_name": ""})
        assert r.status_code == 422

    def test_create_user_whitespace_username_422(self, client: TestClient) -> None:
        """Whitespace-only username is treated as empty and rejected with 422."""
        r = client.post("/users", json={"username": "   ", "display_name": "Alice"})
        assert r.status_code == 422


class TestGetUser:
    def test_get_user_200(self, client: TestClient) -> None:
        """GET /users/{id} returns 200 with correct data."""
        user = _create_user(client, "dave", "Dave")
        r = client.get(f"/users/{user['id']}")
        assert r.status_code == 200
        assert r.json()["username"] == "dave"

    def test_get_user_404(self, client: TestClient) -> None:
        """GET /users/{id} returns 404 for a nonexistent ID."""
        r = client.get("/users/nonexistent-user-id")
        assert r.status_code == 404

    def test_get_user_counts_reflect_tweets(self, client: TestClient) -> None:
        """tweet_count increments when tweets are created."""
        user = _create_user(client, "eve", "Eve")
        _create_tweet(client, user["id"], "Tweet 1")
        _create_tweet(client, user["id"], "Tweet 2")
        r = client.get(f"/users/{user['id']}")
        assert r.json()["tweet_count"] == 2


class TestUpdateUser:
    def test_update_display_name_200(self, client: TestClient) -> None:
        """PUT /users/{id} with display_name returns 200 and updated value."""
        user = _create_user(client, "frank", "Frank")
        r = client.put(f"/users/{user['id']}", json={"display_name": "Franklin"})
        assert r.status_code == 200
        assert r.json()["display_name"] == "Franklin"

    def test_update_bio_200(self, client: TestClient) -> None:
        """PUT /users/{id} with bio returns 200 and updated bio."""
        user = _create_user(client, "grace", "Grace")
        r = client.put(f"/users/{user['id']}", json={"bio": "New bio text"})
        assert r.status_code == 200
        assert r.json()["bio"] == "New bio text"

    def test_update_both_fields(self, client: TestClient) -> None:
        """PUT /users/{id} can update display_name and bio in one request."""
        user = _create_user(client, "heidi", "Heidi")
        r = client.put(
            f"/users/{user['id']}",
            json={"display_name": "Heidi Updated", "bio": "Updated bio"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["display_name"] == "Heidi Updated"
        assert data["bio"] == "Updated bio"

    def test_update_user_not_found_404(self, client: TestClient) -> None:
        """PUT /users/{id} returns 404 for a nonexistent user ID."""
        r = client.put("/users/nonexistent-id", json={"display_name": "Nobody"})
        assert r.status_code == 404


class TestUserTweets:
    def test_get_user_tweets_200(self, client: TestClient) -> None:
        """GET /users/{id}/tweets returns 200 with all user tweets."""
        user = _create_user(client, "ivan", "Ivan")
        _create_tweet(client, user["id"], "First post")
        _create_tweet(client, user["id"], "Second post")
        r = client.get(f"/users/{user['id']}/tweets")
        assert r.status_code == 200
        tweets = r.json()
        assert len(tweets) == 2

    def test_get_user_tweets_newest_first(self, client: TestClient) -> None:
        """GET /users/{id}/tweets returns tweets sorted newest-first."""
        user = _create_user(client, "judy", "Judy")
        _create_tweet(client, user["id"], "Older tweet")
        _create_tweet(client, user["id"], "Newer tweet")
        r = client.get(f"/users/{user['id']}/tweets")
        tweets = r.json()
        # Newest tweet should be first; created_at is ISO string — lexicographic sort works
        assert tweets[0]["content"] == "Newer tweet"
        assert tweets[1]["content"] == "Older tweet"

    def test_get_user_tweets_empty(self, client: TestClient) -> None:
        """GET /users/{id}/tweets returns empty list when user has no tweets."""
        user = _create_user(client, "ken", "Ken")
        r = client.get(f"/users/{user['id']}/tweets")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_user_tweets_404_nonexistent_user(self, client: TestClient) -> None:
        """GET /users/{id}/tweets returns 404 for a nonexistent user."""
        r = client.get("/users/ghost-user/tweets")
        assert r.status_code == 404
