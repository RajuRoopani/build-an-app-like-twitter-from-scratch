"""
Tests for the Trending API — GET /trending.

Covers:
  - Top hashtags returned by tweet count, descending order
  - Empty list when no hashtags exist
  - Deleted tweets reduce count (and drop hashtag from trending if count hits 0)
  - Maximum 10 items returned even when more hashtags exist
  - TrendingItem shape: {hashtag, count}
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


def test_trending_returns_empty_when_no_hashtags(client: TestClient) -> None:
    """GET /trending returns [] when no tweets with hashtags exist."""
    r = client.get("/trending")
    assert r.status_code == 200
    assert r.json() == []


def test_trending_returns_hashtags_descending(client: TestClient) -> None:
    """GET /trending returns hashtags sorted by count, highest first."""
    user_id = _create_user(client, "alice", "Alice")
    # #popular used 3 times, #medium 2 times, #rare once
    for i in range(3):
        _create_tweet(client, user_id, f"Tweet {i} #popular")
    for i in range(2):
        _create_tweet(client, user_id, f"Tweet {i} #medium")
    _create_tweet(client, user_id, "Only one #rare")

    r = client.get("/trending")
    assert r.status_code == 200
    items = r.json()

    # Extract hashtag names in order
    tags = [item["hashtag"] for item in items]
    assert tags[0] == "popular"
    assert tags[1] == "medium"
    assert tags[2] == "rare"

    # Verify counts
    counts = {item["hashtag"]: item["count"] for item in items}
    assert counts["popular"] == 3
    assert counts["medium"] == 2
    assert counts["rare"] == 1


def test_trending_response_shape(client: TestClient) -> None:
    """Each trending item has 'hashtag' (str) and 'count' (int) fields."""
    user_id = _create_user(client, "bob", "Bob")
    _create_tweet(client, user_id, "Hello #shape")

    r = client.get("/trending")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    item = items[0]
    assert "hashtag" in item
    assert "count" in item
    assert isinstance(item["hashtag"], str)
    assert isinstance(item["count"], int)


def test_trending_respects_deleted_tweets(client: TestClient) -> None:
    """A deleted tweet's hashtag is not counted in trending."""
    user_id = _create_user(client, "carol", "Carol")
    # Two tweets with #going, then delete one of them
    t1 = _create_tweet(client, user_id, "Tweet one #going")
    t2 = _create_tweet(client, user_id, "Tweet two #going")

    r = client.get("/trending")
    assert r.status_code == 200
    counts = {i["hashtag"]: i["count"] for i in r.json()}
    assert counts["going"] == 2

    # Delete one tweet
    client.delete(f"/tweets/{t1}")

    r = client.get("/trending")
    counts = {i["hashtag"]: i["count"] for i in r.json()}
    assert counts["going"] == 1


def test_trending_drops_hashtag_when_all_tweets_deleted(client: TestClient) -> None:
    """A hashtag disappears from trending entirely when all its tweets are deleted."""
    user_id = _create_user(client, "dave", "Dave")
    tweet_id = _create_tweet(client, user_id, "Gone #vanished")

    r = client.get("/trending")
    tags = [i["hashtag"] for i in r.json()]
    assert "vanished" in tags

    client.delete(f"/tweets/{tweet_id}")

    r = client.get("/trending")
    tags = [i["hashtag"] for i in r.json()]
    assert "vanished" not in tags


def test_trending_max_10_items(client: TestClient) -> None:
    """GET /trending returns at most 10 hashtags even if more exist."""
    user_id = _create_user(client, "eve", "Eve")
    # Create 15 unique hashtags, each with 1 tweet
    for i in range(15):
        _create_tweet(client, user_id, f"Tweet about #tag{i:02d}")

    r = client.get("/trending")
    assert r.status_code == 200
    assert len(r.json()) <= 10


def test_trending_single_hashtag(client: TestClient) -> None:
    """GET /trending with exactly one hashtag returns exactly one item."""
    user_id = _create_user(client, "frank", "Frank")
    _create_tweet(client, user_id, "Hello #solo")

    r = client.get("/trending")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["hashtag"] == "solo"
    assert items[0]["count"] == 1
