"""
Test suite: Retweets & Quote Tweets
Tests POST /tweets/{id}/retweet and POST /tweets/{id}/quote
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_user(client: TestClient, username: str = "alice", display_name: str = "Alice") -> dict:
    r = client.post("/users", json={"username": username, "display_name": display_name})
    assert r.status_code == 201, r.text
    return r.json()


def _create_tweet(client: TestClient, user_id: str, content: str = "Original tweet") -> dict:
    r = client.post("/tweets", json={"user_id": user_id, "content": content})
    assert r.status_code == 201, r.text
    return r.json()


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestRetweet:
    def test_retweet_returns_201(self, client: TestClient) -> None:
        """POST /tweets/{id}/retweet returns 201."""
        author = _create_user(client, "author", "Author")
        retweeter = _create_user(client, "retweeter", "Retweeter")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/retweet",
            json={"user_id": retweeter["id"]},
        )
        assert r.status_code == 201

    def test_retweet_type_is_retweet(self, client: TestClient) -> None:
        """Retweet response has type='retweet'."""
        author = _create_user(client, "author", "Author")
        retweeter = _create_user(client, "retweeter", "Retweeter")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/retweet",
            json={"user_id": retweeter["id"]},
        )
        data = r.json()
        assert data["type"] == "retweet"

    def test_retweet_content_is_none(self, client: TestClient) -> None:
        """Pure retweet has content=None."""
        author = _create_user(client, "author", "Author")
        retweeter = _create_user(client, "retweeter", "Retweeter")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/retweet",
            json={"user_id": retweeter["id"]},
        )
        assert r.json()["content"] is None

    def test_retweet_original_tweet_id_set(self, client: TestClient) -> None:
        """Retweet response has original_tweet_id pointing to the source tweet."""
        author = _create_user(client, "author", "Author")
        retweeter = _create_user(client, "retweeter", "Retweeter")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/retweet",
            json={"user_id": retweeter["id"]},
        )
        assert r.json()["original_tweet_id"] == tweet["id"]

    def test_retweet_nonexistent_tweet_404(self, client: TestClient) -> None:
        """POST /tweets/bad-id/retweet returns 404 when tweet does not exist."""
        user = _create_user(client)
        r = client.post("/tweets/nonexistent-tweet/retweet", json={"user_id": user["id"]})
        assert r.status_code == 404

    def test_retweet_nonexistent_user_404(self, client: TestClient) -> None:
        """POST /tweets/{id}/retweet returns 404 when the retweeting user does not exist."""
        author = _create_user(client, "author", "Author")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/retweet",
            json={"user_id": "nonexistent-user-id"},
        )
        assert r.status_code == 404

    def test_retweet_increments_retweet_count(self, client: TestClient) -> None:
        """Original tweet's retweet_count increases after a retweet."""
        author = _create_user(client, "author", "Author")
        retweeter = _create_user(client, "retweeter", "Retweeter")
        tweet = _create_tweet(client, author["id"], "Viral content")
        client.post(
            f"/tweets/{tweet['id']}/retweet",
            json={"user_id": retweeter["id"]},
        )
        r = client.get(f"/tweets/{tweet['id']}")
        assert r.json()["retweet_count"] == 1

    def test_multiple_retweets_count_correctly(self, client: TestClient) -> None:
        """retweet_count reflects the correct number of retweets."""
        author = _create_user(client, "author", "Author")
        rt1 = _create_user(client, "rt1", "RT One")
        rt2 = _create_user(client, "rt2", "RT Two")
        tweet = _create_tweet(client, author["id"])
        client.post(f"/tweets/{tweet['id']}/retweet", json={"user_id": rt1["id"]})
        client.post(f"/tweets/{tweet['id']}/retweet", json={"user_id": rt2["id"]})
        r = client.get(f"/tweets/{tweet['id']}")
        assert r.json()["retweet_count"] == 2


class TestQuoteTweet:
    def test_quote_returns_201(self, client: TestClient) -> None:
        """POST /tweets/{id}/quote returns 201."""
        author = _create_user(client, "author", "Author")
        quoter = _create_user(client, "quoter", "Quoter")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/quote",
            json={"user_id": quoter["id"], "content": "My commentary"},
        )
        assert r.status_code == 201

    def test_quote_type_is_quote(self, client: TestClient) -> None:
        """Quote tweet response has type='quote'."""
        author = _create_user(client, "author", "Author")
        quoter = _create_user(client, "quoter", "Quoter")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/quote",
            json={"user_id": quoter["id"], "content": "My commentary"},
        )
        assert r.json()["type"] == "quote"

    def test_quote_content_is_set(self, client: TestClient) -> None:
        """Quote tweet response carries the provided content."""
        author = _create_user(client, "author", "Author")
        quoter = _create_user(client, "quoter", "Quoter")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/quote",
            json={"user_id": quoter["id"], "content": "Great insight!"},
        )
        assert r.json()["content"] == "Great insight!"

    def test_quote_original_tweet_id_set(self, client: TestClient) -> None:
        """Quote tweet has original_tweet_id pointing to the source tweet."""
        author = _create_user(client, "author", "Author")
        quoter = _create_user(client, "quoter", "Quoter")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/quote",
            json={"user_id": quoter["id"], "content": "Commentary"},
        )
        assert r.json()["original_tweet_id"] == tweet["id"]

    def test_quote_increments_quote_count(self, client: TestClient) -> None:
        """Original tweet's quote_count increases after a quote tweet."""
        author = _create_user(client, "author", "Author")
        quoter = _create_user(client, "quoter", "Quoter")
        tweet = _create_tweet(client, author["id"])
        client.post(
            f"/tweets/{tweet['id']}/quote",
            json={"user_id": quoter["id"], "content": "Good one"},
        )
        r = client.get(f"/tweets/{tweet['id']}")
        assert r.json()["quote_count"] == 1

    def test_quote_content_over_280_chars(self, client: TestClient) -> None:
        """POST /tweets/{id}/quote with content > 280 chars returns 400 or 422."""
        author = _create_user(client, "author", "Author")
        quoter = _create_user(client, "quoter", "Quoter")
        tweet = _create_tweet(client, author["id"])
        long_content = "q" * 281
        r = client.post(
            f"/tweets/{tweet['id']}/quote",
            json={"user_id": quoter["id"], "content": long_content},
        )
        assert r.status_code in (400, 422)

    def test_quote_nonexistent_tweet_404(self, client: TestClient) -> None:
        """POST /tweets/bad-id/quote returns 404 when original tweet does not exist."""
        user = _create_user(client)
        r = client.post(
            "/tweets/nonexistent-tweet/quote",
            json={"user_id": user["id"], "content": "Commentary"},
        )
        assert r.status_code == 404

    def test_quote_nonexistent_user_404(self, client: TestClient) -> None:
        """POST /tweets/{id}/quote returns 404 when the quoting user does not exist."""
        author = _create_user(client, "author", "Author")
        tweet = _create_tweet(client, author["id"])
        r = client.post(
            f"/tweets/{tweet['id']}/quote",
            json={"user_id": "ghost-user-id", "content": "My comment"},
        )
        assert r.status_code == 404

    def test_retweet_and_quote_counts_are_independent(self, client: TestClient) -> None:
        """retweet_count and quote_count track separately."""
        author = _create_user(client, "author", "Author")
        rt = _create_user(client, "rt", "Retweeter")
        qt = _create_user(client, "qt", "Quoter")
        tweet = _create_tweet(client, author["id"])
        client.post(f"/tweets/{tweet['id']}/retweet", json={"user_id": rt["id"]})
        client.post(
            f"/tweets/{tweet['id']}/quote",
            json={"user_id": qt["id"], "content": "Commentary"},
        )
        data = client.get(f"/tweets/{tweet['id']}").json()
        assert data["retweet_count"] == 1
        assert data["quote_count"] == 1
