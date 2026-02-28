"""
Tests for the Timeline API — GET /users/{id}/timeline.

Covers:
  - 200 returns tweets from followed users, newest-first
  - Empty timeline when user follows nobody
  - Timeline excludes the requesting user's own tweets
  - Timeline includes retweets from followed users
  - Timeline includes quote tweets from followed users
  - 404 for nonexistent user
"""

from __future__ import annotations

import time

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


def _follow(client: TestClient, follower_id: str, target_id: str) -> None:
    """Have follower_id follow target_id."""
    r = client.post(f"/users/{follower_id}/follow", json={"target_user_id": target_id})
    assert r.status_code == 200


# ── Tests ────────────────────────────────────────────────────────────────────


def test_timeline_returns_tweets_from_followed_users(client: TestClient) -> None:
    """GET /users/{id}/timeline returns tweets authored by users that user follows."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")
    _follow(client, alice_id, bob_id)

    tweet_id = _create_tweet(client, bob_id, "Hello from Bob!")

    r = client.get(f"/users/{alice_id}/timeline")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert tweet_id in ids


def test_timeline_is_empty_when_following_nobody(client: TestClient) -> None:
    """GET /users/{id}/timeline returns [] when user follows nobody."""
    alice_id = _create_user(client, "alice", "Alice")
    # Create a tweet (shouldn't show up since no follows)
    _create_tweet(client, alice_id, "My own tweet")

    r = client.get(f"/users/{alice_id}/timeline")
    assert r.status_code == 200
    assert r.json() == []


def test_timeline_excludes_own_tweets(client: TestClient) -> None:
    """The user's own tweets must NOT appear in their timeline."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")
    _follow(client, alice_id, bob_id)

    # Alice tweets — should NOT appear in her own timeline
    own_tweet_id = _create_tweet(client, alice_id, "Alice's own tweet")
    # Bob tweets — SHOULD appear
    bob_tweet_id = _create_tweet(client, bob_id, "Bob's tweet")

    r = client.get(f"/users/{alice_id}/timeline")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert own_tweet_id not in ids
    assert bob_tweet_id in ids


def test_timeline_sorted_newest_first(client: TestClient) -> None:
    """Tweets in timeline are ordered newest-first."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")
    _follow(client, alice_id, bob_id)

    tweet1_id = _create_tweet(client, bob_id, "Tweet one")
    tweet2_id = _create_tweet(client, bob_id, "Tweet two")
    tweet3_id = _create_tweet(client, bob_id, "Tweet three")

    r = client.get(f"/users/{alice_id}/timeline")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    # Most recently created tweet should appear first
    assert ids.index(tweet3_id) < ids.index(tweet2_id) < ids.index(tweet1_id)


def test_timeline_includes_retweets_from_followed_users(client: TestClient) -> None:
    """Retweets made by followed users appear in the timeline."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")
    carol_id = _create_user(client, "carol", "Carol")
    _follow(client, alice_id, bob_id)

    # Carol posts original; Bob retweets it
    original_tweet_id = _create_tweet(client, carol_id, "Carol's original")
    r = client.post(f"/tweets/{original_tweet_id}/retweet", json={"user_id": bob_id})
    assert r.status_code == 201
    retweet_id = r.json()["id"]

    r = client.get(f"/users/{alice_id}/timeline")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert retweet_id in ids


def test_timeline_includes_quote_tweets_from_followed_users(client: TestClient) -> None:
    """Quote tweets made by followed users appear in the timeline."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")
    carol_id = _create_user(client, "carol", "Carol")
    _follow(client, alice_id, bob_id)

    original_tweet_id = _create_tweet(client, carol_id, "Carol's original")
    r = client.post(
        f"/tweets/{original_tweet_id}/quote",
        json={"user_id": bob_id, "content": "Bob's commentary"},
    )
    assert r.status_code == 201
    quote_id = r.json()["id"]

    r = client.get(f"/users/{alice_id}/timeline")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert quote_id in ids


def test_timeline_nonexistent_user_returns_404(client: TestClient) -> None:
    """GET /users/{id}/timeline with a non-existent user_id returns 404."""
    r = client.get("/users/does-not-exist/timeline")
    assert r.status_code == 404


def test_timeline_aggregates_multiple_followed_users(client: TestClient) -> None:
    """Timeline includes tweets from ALL followed users."""
    alice_id = _create_user(client, "alice", "Alice")
    bob_id = _create_user(client, "bob", "Bob")
    carol_id = _create_user(client, "carol", "Carol")
    _follow(client, alice_id, bob_id)
    _follow(client, alice_id, carol_id)

    bob_tweet_id = _create_tweet(client, bob_id, "Bob speaks")
    carol_tweet_id = _create_tweet(client, carol_id, "Carol speaks")

    r = client.get(f"/users/{alice_id}/timeline")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert bob_tweet_id in ids
    assert carol_tweet_id in ids
