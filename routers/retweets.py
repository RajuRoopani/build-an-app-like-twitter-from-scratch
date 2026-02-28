"""
Retweets & Quote Tweets router — AC16-AC19.

Endpoints:
  POST /tweets/{tweet_id}/retweet  → 201 TweetOut  (404 if tweet/user not found)
  POST /tweets/{tweet_id}/quote    → 201 TweetOut  (400 >280 chars, 404 if not found)
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from twitter_app import storage
from twitter_app.models import QuoteTweetCreate, RetweetCreate, TweetOut

router = APIRouter(prefix="/tweets", tags=["retweets"])


# ── POST /tweets/{tweet_id}/retweet ───────────────────────────────────────────

@router.post("/{tweet_id}/retweet", status_code=201, response_model=TweetOut)
def create_retweet(tweet_id: str, body: RetweetCreate) -> TweetOut:
    """
    Retweet an existing tweet.

    Creates a new tweet record of type='retweet' that references original_tweet_id.
    Content is None for pure retweets.
    Returns 404 if the original tweet or the retweeting user does not exist.
    """
    # Validate original tweet exists
    original = storage.tweets.get(tweet_id)
    if not original:
        raise HTTPException(status_code=404, detail=f"Tweet '{tweet_id}' not found")

    # Validate user exists
    if body.user_id not in storage.users:
        raise HTTPException(status_code=404, detail=f"User '{body.user_id}' not found")

    from twitter_app.routers.tweets import _build_tweet_out

    tid = str(uuid4())
    now = datetime.utcnow().isoformat()

    retweet = {
        "id": tid,
        "type": "retweet",
        "user_id": body.user_id,
        "content": None,
        "created_at": now,
        "hashtags": [],
        "mentions": [],
        "original_tweet_id": tweet_id,
    }

    storage.tweets[tid] = retweet
    storage.likes[tid] = set()

    return _build_tweet_out(retweet)


# ── POST /tweets/{tweet_id}/quote ─────────────────────────────────────────────

@router.post("/{tweet_id}/quote", status_code=201, response_model=TweetOut)
def create_quote_tweet(tweet_id: str, body: QuoteTweetCreate) -> TweetOut:
    """
    Quote an existing tweet with additional commentary.

    Creates a new tweet of type='quote' with its own content + original_tweet_id.
    Content max 280 chars → 400 if exceeded.
    Returns 404 if original tweet or user does not exist.
    """
    # Validate original tweet exists
    original = storage.tweets.get(tweet_id)
    if not original:
        raise HTTPException(status_code=404, detail=f"Tweet '{tweet_id}' not found")

    # Validate user exists
    if body.user_id not in storage.users:
        raise HTTPException(status_code=404, detail=f"User '{body.user_id}' not found")

    if len(body.content) > 280:
        raise HTTPException(status_code=400, detail="Content must not exceed 280 characters")

    from twitter_app.routers.tweets import (
        _build_tweet_out,
        _extract_hashtags,
        _extract_mentions,
        _index_hashtags,
    )

    tid = str(uuid4())
    now = datetime.utcnow().isoformat()
    hashtags = _extract_hashtags(body.content)
    mentions = _extract_mentions(body.content)

    quote_tweet = {
        "id": tid,
        "type": "quote",
        "user_id": body.user_id,
        "content": body.content,
        "created_at": now,
        "hashtags": hashtags,
        "mentions": mentions,
        "original_tweet_id": tweet_id,
    }

    storage.tweets[tid] = quote_tweet
    storage.likes[tid] = set()
    _index_hashtags(tid, hashtags)

    return _build_tweet_out(quote_tweet)
