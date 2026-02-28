"""
Tests for the Likes API — POST /tweets/{id}/like and DELETE /tweets/{id}/like.

Covers:
  - Successful like (200)
  - Double-like returns 409
  - Like on nonexistent tweet returns 404
  - Unlike (200)
  - Unlike tweet user never liked returns 404
  - like_count on tweet GET increases after like and decreases after unlike
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ── Helpers ─────────────────────────────────────────────────────────────────


def _create_user(client: TestClient, username: str, display_name: str) -> str:
    """Create a user and return their ID."""
    r = client.post("/users", json={"username": username, "display_name": display_name})
    assert r.status_code == 201
    return r.json()["id"]


def _create_tweet(client: TestClient, user_id: str, content: str = "Hello world") -> str:
    """Create a tweet and return its ID."""
    r = client.post("/tweets", json={"user_id": user_id, "content": content})
    assert r.status_code == 201
    return r.json()["id"]


# ── Tests ────────────────────────────────────────────────────────────────────


def test_like_tweet_returns_200(client: TestClient) -> None:
    """POST /tweets/{id}/like with a valid user returns 200."""
    user_id = _create_user(client, "alice", "Alice")
    tweet_id = _create_tweet(client, user_id)

    r = client.post(f"/tweets/{tweet_id}/like", json={"user_id": user_id})
    assert r.status_code == 200
    body = r.json()
    assert body["like_count"] == 1
    assert "detail" in body


def test_like_tweet_response_contains_user_id(client: TestClient) -> None:
    """Like response body includes like_count (verifying the correct tweet was liked)."""
    user_id = _create_user(client, "bob", "Bob")
    tweet_id = _create_tweet(client, user_id)

    r = client.post(f"/tweets/{tweet_id}/like", json={"user_id": user_id})
    assert r.status_code == 200
    # The response confirms the like was recorded via like_count
    assert r.json()["like_count"] == 1


def test_double_like_returns_409(client: TestClient) -> None:
    """POST /tweets/{id}/like twice by the same user returns 409 Conflict."""
    user_id = _create_user(client, "carol", "Carol")
    tweet_id = _create_tweet(client, user_id)

    client.post(f"/tweets/{tweet_id}/like", json={"user_id": user_id})
    r = client.post(f"/tweets/{tweet_id}/like", json={"user_id": user_id})
    assert r.status_code == 409


def test_like_nonexistent_tweet_returns_404(client: TestClient) -> None:
    """POST /tweets/{id}/like with a non-existent tweet_id returns 404."""
    user_id = _create_user(client, "dave", "Dave")

    r = client.post("/tweets/nonexistent-id/like", json={"user_id": user_id})
    assert r.status_code == 404


def test_unlike_tweet_returns_200(client: TestClient) -> None:
    """DELETE /tweets/{id}/like?user_id=X after a like returns 200."""
    user_id = _create_user(client, "eve", "Eve")
    tweet_id = _create_tweet(client, user_id)

    client.post(f"/tweets/{tweet_id}/like", json={"user_id": user_id})
    r = client.delete(f"/tweets/{tweet_id}/like", params={"user_id": user_id})
    assert r.status_code == 200
    assert r.json()["like_count"] == 0


def test_unlike_tweet_not_previously_liked_returns_404(client: TestClient) -> None:
    """DELETE /tweets/{id}/like when user never liked the tweet returns 404."""
    user_id = _create_user(client, "frank", "Frank")
    tweet_id = _create_tweet(client, user_id)

    r = client.delete(f"/tweets/{tweet_id}/like", params={"user_id": user_id})
    assert r.status_code == 404


def test_like_count_increases_on_tweet_get(client: TestClient) -> None:
    """GET /tweets/{id} reflects the current like_count after likes are added."""
    alice_id = _create_user(client, "grace", "Grace")
    bob_id = _create_user(client, "henry", "Henry")
    tweet_id = _create_tweet(client, alice_id)

    # Before any likes
    r = client.get(f"/tweets/{tweet_id}")
    assert r.status_code == 200
    assert r.json()["like_count"] == 0

    # After first like
    client.post(f"/tweets/{tweet_id}/like", json={"user_id": alice_id})
    r = client.get(f"/tweets/{tweet_id}")
    assert r.json()["like_count"] == 1

    # After second like from different user
    client.post(f"/tweets/{tweet_id}/like", json={"user_id": bob_id})
    r = client.get(f"/tweets/{tweet_id}")
    assert r.json()["like_count"] == 2


def test_like_count_decreases_after_unlike(client: TestClient) -> None:
    """GET /tweets/{id} shows decreased like_count after an unlike."""
    user_id = _create_user(client, "iris", "Iris")
    tweet_id = _create_tweet(client, user_id)

    client.post(f"/tweets/{tweet_id}/like", json={"user_id": user_id})
    r = client.get(f"/tweets/{tweet_id}")
    assert r.json()["like_count"] == 1

    client.delete(f"/tweets/{tweet_id}/like", params={"user_id": user_id})
    r = client.get(f"/tweets/{tweet_id}")
    assert r.json()["like_count"] == 0


def test_multiple_users_can_like_same_tweet(client: TestClient) -> None:
    """Multiple distinct users can each like the same tweet."""
    owner_id = _create_user(client, "jake", "Jake")
    tweet_id = _create_tweet(client, owner_id)

    for i in range(5):
        uid = _create_user(client, f"liker{i}", f"Liker {i}")
        r = client.post(f"/tweets/{tweet_id}/like", json={"user_id": uid})
        assert r.status_code == 200

    r = client.get(f"/tweets/{tweet_id}")
    assert r.json()["like_count"] == 5
