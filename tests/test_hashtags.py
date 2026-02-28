"""
Tests for the Hashtags API — GET /hashtags/{tag}/tweets.

Covers:
  - 200 returns tweets containing the hashtag
  - Case-insensitive matching (#Python vs #python)
  - Returns empty list for unused hashtag
  - Deleted tweets don't appear in results
  - Multiple tweets share same hashtag
  - Tag can be requested with or without trailing spaces (URL encoding handled by FastAPI)
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


def test_hashtag_returns_matching_tweets(client: TestClient) -> None:
    """GET /hashtags/{tag}/tweets returns tweets that contain the hashtag."""
    user_id = _create_user(client, "alice", "Alice")
    tweet_id = _create_tweet(client, user_id, "Hello #world today")

    r = client.get("/hashtags/world/tweets")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert tweet_id in ids


def test_hashtag_case_insensitive_uppercase_tag(client: TestClient) -> None:
    """#Python tweet is found when querying with 'python' (lowercase)."""
    user_id = _create_user(client, "bob", "Bob")
    tweet_id = _create_tweet(client, user_id, "I love #Python")

    r = client.get("/hashtags/python/tweets")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert tweet_id in ids


def test_hashtag_case_insensitive_mixed_case(client: TestClient) -> None:
    """#Python tweet is also found when querying with 'PYTHON' (all caps)."""
    user_id = _create_user(client, "carol", "Carol")
    tweet_id = _create_tweet(client, user_id, "I love #Python")

    r = client.get("/hashtags/PYTHON/tweets")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert tweet_id in ids


def test_hashtag_returns_empty_for_unused_tag(client: TestClient) -> None:
    """GET /hashtags/{tag}/tweets returns [] for a hashtag nobody used."""
    r = client.get("/hashtags/doesnotexist/tweets")
    assert r.status_code == 200
    assert r.json() == []


def test_deleted_tweets_excluded_from_hashtag_results(client: TestClient) -> None:
    """After a tweet is deleted, it no longer appears in hashtag results."""
    user_id = _create_user(client, "dave", "Dave")
    tweet_id = _create_tweet(client, user_id, "Going away #byebye")

    # Confirm it appears before deletion
    r = client.get("/hashtags/byebye/tweets")
    assert tweet_id in [t["id"] for t in r.json()]

    # Delete the tweet
    del_r = client.delete(f"/tweets/{tweet_id}")
    assert del_r.status_code == 204

    # Confirm it no longer appears
    r = client.get("/hashtags/byebye/tweets")
    assert tweet_id not in [t["id"] for t in r.json()]


def test_hashtag_multiple_tweets(client: TestClient) -> None:
    """Multiple tweets sharing a hashtag all appear in the results."""
    user_id = _create_user(client, "eve", "Eve")
    t1 = _create_tweet(client, user_id, "First #tech post")
    t2 = _create_tweet(client, user_id, "Second #tech post")
    t3 = _create_tweet(client, user_id, "Third #tech post")

    r = client.get("/hashtags/tech/tweets")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert t1 in ids
    assert t2 in ids
    assert t3 in ids


def test_hashtag_tweet_not_in_other_hashtag(client: TestClient) -> None:
    """A tweet with #foo does NOT appear in results for #bar."""
    user_id = _create_user(client, "frank", "Frank")
    _create_tweet(client, user_id, "About #foo")

    r = client.get("/hashtags/bar/tweets")
    assert r.status_code == 200
    assert r.json() == []


def test_hashtag_results_sorted_newest_first(client: TestClient) -> None:
    """Hashtag results are returned newest-first."""
    user_id = _create_user(client, "grace", "Grace")
    t1 = _create_tweet(client, user_id, "First #order post")
    t2 = _create_tweet(client, user_id, "Second #order post")
    t3 = _create_tweet(client, user_id, "Third #order post")

    r = client.get("/hashtags/order/tweets")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert ids.index(t3) < ids.index(t2) < ids.index(t1)
