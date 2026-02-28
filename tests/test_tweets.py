"""
Test suite: Tweets
Tests POST /tweets, GET /tweets/{id}, DELETE /tweets/{id},
hashtag extraction, mention extraction, and count behaviour.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_user(client: TestClient, username: str = "alice", display_name: str = "Alice") -> dict:
    r = client.post("/users", json={"username": username, "display_name": display_name})
    assert r.status_code == 201, r.text
    return r.json()


def _create_tweet(client: TestClient, user_id: str, content: str = "Hello world!") -> dict:
    r = client.post("/tweets", json={"user_id": user_id, "content": content})
    assert r.status_code == 201, r.text
    return r.json()


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestCreateTweet:
    def test_create_tweet_returns_201(self, client: TestClient) -> None:
        """POST /tweets with valid data returns 201."""
        user = _create_user(client)
        r = client.post("/tweets", json={"user_id": user["id"], "content": "Hello Twitter!"})
        assert r.status_code == 201

    def test_create_tweet_response_shape(self, client: TestClient) -> None:
        """Response contains id, content, user_id, like_count, retweet_count, quote_count."""
        user = _create_user(client)
        r = client.post("/tweets", json={"user_id": user["id"], "content": "Test tweet"})
        data = r.json()
        assert "id" in data
        assert data["content"] == "Test tweet"
        assert data["user_id"] == user["id"]
        assert data["like_count"] == 0
        assert data["retweet_count"] == 0
        assert data["quote_count"] == 0
        assert "created_at" in data

    def test_create_tweet_nonexistent_user_404(self, client: TestClient) -> None:
        """POST /tweets with a nonexistent user_id returns 404."""
        r = client.post("/tweets", json={"user_id": "bad-user-id", "content": "Hello!"})
        assert r.status_code == 404

    def test_create_tweet_content_over_280_chars(self, client: TestClient) -> None:
        """POST /tweets with content > 280 chars returns 400 or 422."""
        user = _create_user(client)
        long_content = "x" * 281
        r = client.post("/tweets", json={"user_id": user["id"], "content": long_content})
        assert r.status_code in (400, 422)

    def test_create_tweet_exactly_280_chars_accepted(self, client: TestClient) -> None:
        """POST /tweets with exactly 280 chars is accepted (boundary value)."""
        user = _create_user(client)
        content = "a" * 280
        r = client.post("/tweets", json={"user_id": user["id"], "content": content})
        assert r.status_code == 201

    def test_create_tweet_extracts_hashtags(self, client: TestClient) -> None:
        """Hashtags are extracted from content and stored as lowercase list."""
        user = _create_user(client)
        r = client.post(
            "/tweets",
            json={"user_id": user["id"], "content": "Learning #Python and #Coding today!"},
        )
        assert r.status_code == 201
        data = r.json()
        assert "python" in data["hashtags"]
        assert "coding" in data["hashtags"]

    def test_create_tweet_extracts_mentions(self, client: TestClient) -> None:
        """@mentions are extracted from content and stored in mentions list."""
        user = _create_user(client)
        r = client.post(
            "/tweets",
            json={"user_id": user["id"], "content": "Hey @alice and @bob, check this out!"},
        )
        assert r.status_code == 201
        data = r.json()
        assert "alice" in data["mentions"]
        assert "bob" in data["mentions"]

    def test_create_tweet_no_hashtags_or_mentions(self, client: TestClient) -> None:
        """Tweet with no hashtags or mentions has empty lists."""
        user = _create_user(client)
        r = client.post("/tweets", json={"user_id": user["id"], "content": "Plain text tweet."})
        data = r.json()
        assert data["hashtags"] == []
        assert data["mentions"] == []

    def test_create_tweet_type_is_tweet(self, client: TestClient) -> None:
        """Original tweets have type='tweet'."""
        user = _create_user(client)
        r = client.post("/tweets", json={"user_id": user["id"], "content": "Hello!"})
        assert r.json()["type"] == "tweet"


class TestGetTweet:
    def test_get_tweet_200(self, client: TestClient) -> None:
        """GET /tweets/{id} returns 200 with correct data."""
        user = _create_user(client)
        tweet = _create_tweet(client, user["id"], "Fetch me")
        r = client.get(f"/tweets/{tweet['id']}")
        assert r.status_code == 200
        assert r.json()["content"] == "Fetch me"

    def test_get_tweet_includes_counts(self, client: TestClient) -> None:
        """GET /tweets/{id} includes like_count, retweet_count, quote_count."""
        user = _create_user(client)
        tweet = _create_tweet(client, user["id"])
        data = client.get(f"/tweets/{tweet['id']}").json()
        assert "like_count" in data
        assert "retweet_count" in data
        assert "quote_count" in data

    def test_get_tweet_404(self, client: TestClient) -> None:
        """GET /tweets/{id} returns 404 for a nonexistent tweet ID."""
        r = client.get("/tweets/nonexistent-tweet-id")
        assert r.status_code == 404


class TestDeleteTweet:
    def test_delete_tweet_204(self, client: TestClient) -> None:
        """DELETE /tweets/{id} returns 204 on success."""
        user = _create_user(client)
        tweet = _create_tweet(client, user["id"])
        r = client.delete(f"/tweets/{tweet['id']}")
        assert r.status_code == 204

    def test_delete_tweet_removes_from_store(self, client: TestClient) -> None:
        """After DELETE, GET /tweets/{id} returns 404."""
        user = _create_user(client)
        tweet = _create_tweet(client, user["id"])
        client.delete(f"/tweets/{tweet['id']}")
        r = client.get(f"/tweets/{tweet['id']}")
        assert r.status_code == 404

    def test_delete_tweet_404(self, client: TestClient) -> None:
        """DELETE /tweets/{id} returns 404 for a nonexistent tweet ID."""
        r = client.delete("/tweets/no-such-tweet-id")
        assert r.status_code == 404

    def test_delete_tweet_decrements_tweet_count(self, client: TestClient) -> None:
        """Deleting a tweet decrements the author's tweet_count."""
        user = _create_user(client)
        tweet = _create_tweet(client, user["id"])
        client.delete(f"/tweets/{tweet['id']}")
        r = client.get(f"/users/{user['id']}")
        assert r.json()["tweet_count"] == 0


class TestHashtagAndMentionExtraction:
    def test_hashtags_deduplication(self, client: TestClient) -> None:
        """Duplicate hashtags in content appear only once in the list."""
        user = _create_user(client)
        r = client.post(
            "/tweets",
            json={"user_id": user["id"], "content": "#python is great, love #python"},
        )
        data = r.json()
        assert data["hashtags"].count("python") == 1

    def test_hashtags_case_normalised_to_lowercase(self, client: TestClient) -> None:
        """Hashtags are stored in lowercase regardless of original casing."""
        user = _create_user(client)
        r = client.post(
            "/tweets",
            json={"user_id": user["id"], "content": "#Python #CODING"},
        )
        data = r.json()
        assert "python" in data["hashtags"]
        assert "coding" in data["hashtags"]

    def test_mentions_deduplication(self, client: TestClient) -> None:
        """Duplicate @mentions appear only once."""
        user = _create_user(client)
        r = client.post(
            "/tweets",
            json={"user_id": user["id"], "content": "@alice hey @alice!"},
        )
        data = r.json()
        assert data["mentions"].count("alice") == 1
