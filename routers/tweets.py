"""
Tweets router — AC10-AC15.

Endpoints:
  POST   /tweets                   → 201 TweetOut  (400 >280 chars, 404 user not found)
  GET    /tweets/{tweet_id}        → 200 TweetOut  (404 if not found)
  DELETE /tweets/{tweet_id}        → 204           (404 if not found)
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response

from twitter_app import storage
from twitter_app.models import TweetCreate, TweetOut, UserOut

router = APIRouter(prefix="/tweets", tags=["tweets"])

# Regex patterns for hashtag and mention extraction
_HASHTAG_RE = re.compile(r"#(\w+)")
_MENTION_RE = re.compile(r"@(\w+)")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _extract_hashtags(content: str) -> List[str]:
    """Return a deduplicated list of lowercase hashtags found in content."""
    return list(dict.fromkeys(
        tag.lower() for tag in _HASHTAG_RE.findall(content)
    ))


def _extract_mentions(content: str) -> List[str]:
    """Return a deduplicated list of @mention usernames found in content."""
    return list(dict.fromkeys(_MENTION_RE.findall(content)))


def _index_hashtags(tweet_id: str, hashtags: List[str]) -> None:
    """Add tweet_id to the hashtag index for each hashtag."""
    for tag in hashtags:
        storage.hashtag_index.setdefault(tag, []).append(tweet_id)


def _deindex_hashtags(tweet_id: str, hashtags: List[str]) -> None:
    """Remove tweet_id from the hashtag index (used on tweet deletion)."""
    for tag in hashtags:
        lst = storage.hashtag_index.get(tag, [])
        if tweet_id in lst:
            lst.remove(tweet_id)


def _get_tweet_or_404(tweet_id: str) -> dict:
    """Return a stored tweet dict or raise 404."""
    tweet = storage.tweets.get(tweet_id)
    if not tweet:
        raise HTTPException(status_code=404, detail=f"Tweet '{tweet_id}' not found")
    return tweet


def _build_user_out(user: dict) -> UserOut:
    """Build a UserOut from a stored user dict."""
    uid = user["id"]
    tweet_count = sum(1 for t in storage.tweets.values() if t["user_id"] == uid)
    return UserOut(
        id=uid,
        username=user["username"],
        display_name=user["display_name"],
        bio=user.get("bio"),
        followers_count=len(storage.followers.get(uid, set())),
        following_count=len(storage.following.get(uid, set())),
        tweet_count=tweet_count,
        created_at=user["created_at"],
    )


def _count_retweets(tweet_id: str) -> int:
    """Count tweets of type 'retweet' that reference tweet_id."""
    return sum(
        1 for t in storage.tweets.values()
        if t.get("type") == "retweet" and t.get("original_tweet_id") == tweet_id
    )


def _count_quotes(tweet_id: str) -> int:
    """Count tweets of type 'quote' that reference tweet_id."""
    return sum(
        1 for t in storage.tweets.values()
        if t.get("type") == "quote" and t.get("original_tweet_id") == tweet_id
    )


def _build_tweet_out(tweet: dict, depth: int = 0) -> TweetOut:
    """
    Build a TweetOut from a stored tweet dict.

    depth prevents infinite recursion when building nested original_tweet.
    """
    tid = tweet["id"]
    author_dict = storage.users.get(tweet["user_id"])
    author = _build_user_out(author_dict) if author_dict else None

    original_tweet_out: Optional[TweetOut] = None
    orig_id = tweet.get("original_tweet_id")
    if orig_id and depth == 0:
        orig = storage.tweets.get(orig_id)
        if orig:
            original_tweet_out = _build_tweet_out(orig, depth=1)

    return TweetOut(
        id=tid,
        type=tweet.get("type", "tweet"),
        user_id=tweet["user_id"],
        content=tweet.get("content"),
        created_at=tweet["created_at"],
        hashtags=tweet.get("hashtags", []),
        mentions=tweet.get("mentions", []),
        like_count=len(storage.likes.get(tid, set())),
        retweet_count=_count_retweets(tid),
        quote_count=_count_quotes(tid),
        original_tweet_id=orig_id,
        original_tweet=original_tweet_out,
        author=author,
    )


# ── POST /tweets ───────────────────────────────────────────────────────────────

@router.post("", status_code=201, response_model=TweetOut)
def create_tweet(body: TweetCreate) -> TweetOut:
    """
    Create a new original tweet.

    - **user_id** must exist → 404 if not.
    - **content** max 280 characters → 400 if exceeded.
    - Extracts #hashtags and @mentions automatically.
    """
    if body.user_id not in storage.users:
        raise HTTPException(status_code=404, detail=f"User '{body.user_id}' not found")

    # Length guard (also enforced by Pydantic but kept for clarity)
    if len(body.content) > 280:
        raise HTTPException(status_code=400, detail="Content must not exceed 280 characters")

    tid = str(uuid4())
    now = datetime.utcnow().isoformat()
    hashtags = _extract_hashtags(body.content)
    mentions = _extract_mentions(body.content)

    tweet = {
        "id": tid,
        "type": "tweet",
        "user_id": body.user_id,
        "content": body.content,
        "created_at": now,
        "hashtags": hashtags,
        "mentions": mentions,
        "original_tweet_id": None,
    }

    storage.tweets[tid] = tweet
    storage.likes[tid] = set()
    _index_hashtags(tid, hashtags)

    return _build_tweet_out(tweet)


# ── GET /tweets/{tweet_id} ─────────────────────────────────────────────────────

@router.get("/{tweet_id}", response_model=TweetOut)
def get_tweet(tweet_id: str) -> TweetOut:
    """
    Retrieve a tweet by ID.

    For retweets and quote tweets the original tweet data is embedded.
    Returns 404 if the tweet does not exist.
    """
    tweet = _get_tweet_or_404(tweet_id)
    return _build_tweet_out(tweet)


# ── DELETE /tweets/{tweet_id} ──────────────────────────────────────────────────

@router.delete("/{tweet_id}", status_code=204)
def delete_tweet(tweet_id: str) -> Response:
    """
    Delete a tweet by ID.

    Returns 204 No Content on success. Returns 404 if not found.
    Cleans up the hashtag index and like store.
    """
    tweet = _get_tweet_or_404(tweet_id)

    # Clean up hashtag index
    _deindex_hashtags(tweet_id, tweet.get("hashtags", []))

    # Remove likes store for this tweet
    storage.likes.pop(tweet_id, None)

    del storage.tweets[tweet_id]

    return Response(status_code=204)
