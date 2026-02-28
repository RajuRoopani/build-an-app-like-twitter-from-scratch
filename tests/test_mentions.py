"""
Tests for the Mentions API — GET /users/{id}/mentions.

Covers:
  - 200 returns tweets that @mention the user
  - 404 for nonexistent user
  - Empty list if no tweets mention the user
  - Case-insensitive matching (@Alice vs @alice vs @ALICE)
  - Self-mentions are included
  - Multiple tweets mentioning the same user are all returned
  - Mentions sorted newest-first
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


def _create_tweet(client: TestClient, user_id: str, content: str) -> str:
    """Create a tweet and return its ID."""
    r = client.post("/tweets", json={"user_id": user_id, "content": content})
    assert r.status_code == 201
    return r.json()["id"]


# ── Tests ────────────────────────────────────────────────────────────────────


def test_mentions_returns_tweets_mentioning_user(client: TestClient) -> None:
    """GET /users/{id}/mentions returns tweets that contain @username."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")

    tweet_id = _create_tweet(client, bob_id, "Hey @alice, check this out!")

    r = client.get(f"/users/{alice_id}/mentions")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert tweet_id in ids


def test_mentions_returns_404_for_nonexistent_user(client: TestClient) -> None:
    """GET /users/{id}/mentions returns 404 when user does not exist."""
    r = client.get("/users/nonexistent-id/mentions")
    assert r.status_code == 404


def test_mentions_returns_empty_when_no_tweets_mention_user(client: TestClient) -> None:
    """GET /users/{id}/mentions returns [] when nobody has mentioned the user."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")

    # Bob tweets but doesn't mention Alice
    _create_tweet(client, bob_id, "Nothing to see here")

    r = client.get(f"/users/{alice_id}/mentions")
    assert r.status_code == 200
    assert r.json() == []


def test_mentions_case_insensitive_lowercase_mention(client: TestClient) -> None:
    """@alice mention is found for user with username 'Alice' (case-insensitive)."""
    alice_id = _create_user(client, "Alice", "Alice Real")
    bob_id = _create_user(client, "bob", "Bob")

    # Mention uses lowercase
    tweet_id = _create_tweet(client, bob_id, "shoutout to @alice today")

    r = client.get(f"/users/{alice_id}/mentions")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert tweet_id in ids


def test_mentions_case_insensitive_uppercase_mention(client: TestClient) -> None:
    """@ALICE mention is found for user with lowercase username 'alice'."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")

    tweet_id = _create_tweet(client, bob_id, "Hello @ALICE!")

    r = client.get(f"/users/{alice_id}/mentions")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert tweet_id in ids


def test_mentions_multiple_tweets_all_returned(client: TestClient) -> None:
    """All tweets mentioning a user are returned, not just the most recent."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")
    carol_id = _create_user(client, "carol", "Carol")

    t1 = _create_tweet(client, bob_id, "First mention @alice")
    t2 = _create_tweet(client, carol_id, "Second mention @alice")
    t3 = _create_tweet(client, bob_id, "Third mention @alice too")

    r = client.get(f"/users/{alice_id}/mentions")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert t1 in ids
    assert t2 in ids
    assert t3 in ids


def test_mentions_sorted_newest_first(client: TestClient) -> None:
    """Mentions are returned newest-first."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")

    t1 = _create_tweet(client, bob_id, "First @alice mention")
    t2 = _create_tweet(client, bob_id, "Second @alice mention")
    t3 = _create_tweet(client, bob_id, "Third @alice mention")

    r = client.get(f"/users/{alice_id}/mentions")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert ids.index(t3) < ids.index(t2) < ids.index(t1)


def test_mentions_does_not_include_non_mentioned_tweets(client: TestClient) -> None:
    """Tweets that don't mention the user are excluded from results."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")

    mention_tweet_id = _create_tweet(client, bob_id, "Hey @alice!")
    unrelated_tweet_id = _create_tweet(client, bob_id, "Nothing personal here")

    r = client.get(f"/users/{alice_id}/mentions")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert mention_tweet_id in ids
    assert unrelated_tweet_id not in ids
