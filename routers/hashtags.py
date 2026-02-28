"""
Hashtags router — AC30-AC31.

Endpoints:
  GET /hashtags/{tag}/tweets  → 200 List[TweetOut]  newest first, empty list if none.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter

from twitter_app import storage
from twitter_app.models import TweetOut

router = APIRouter(prefix="/hashtags", tags=["hashtags"])


# ── GET /hashtags/{tag}/tweets ─────────────────────────────────────────────────

@router.get("/{tag}/tweets", response_model=List[TweetOut])
def get_tweets_by_hashtag(tag: str) -> List[TweetOut]:
    """
    Retrieve all tweets containing the given hashtag, newest first.

    - **tag** should be provided WITHOUT the # prefix.
    - Matching is case-insensitive.
    - Returns an empty list if no tweets use this hashtag.
    """
    from twitter_app.routers.tweets import _build_tweet_out

    tag_lower = tag.lower()
    tweet_ids = storage.hashtag_index.get(tag_lower, [])

    # Filter to tweets that still exist (may have been deleted)
    result = []
    for tid in tweet_ids:
        tweet = storage.tweets.get(tid)
        if tweet:
            result.append(tweet)

    result.sort(key=lambda t: t["created_at"], reverse=True)
    return [_build_tweet_out(t) for t in result]
