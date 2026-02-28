"""
Timeline router — AC28-AC29.

Endpoints:
  GET /users/{user_id}/timeline  → 200 List[TweetOut]  newest first, from followed users.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from twitter_app import storage
from twitter_app.models import TweetOut

router = APIRouter(prefix="/users", tags=["timeline"])


# ── GET /users/{user_id}/timeline ─────────────────────────────────────────────

@router.get("/{user_id}/timeline", response_model=List[TweetOut])
def get_timeline(user_id: str) -> List[TweetOut]:
    """
    Return the personalised timeline for a user.

    Includes all tweets (originals, retweets, quote tweets) from users
    that user_id follows, sorted newest-first.
    Returns an empty list if the user follows nobody.
    Returns 404 if the user does not exist.
    """
    if user_id not in storage.users:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    # Import here to avoid circular imports
    from twitter_app.routers.tweets import _build_tweet_out

    followed_ids = storage.following.get(user_id, set())
    if not followed_ids:
        return []

    feed_tweets = [
        t for t in storage.tweets.values()
        if t["user_id"] in followed_ids
    ]
    feed_tweets.sort(key=lambda t: t["created_at"], reverse=True)
    return [_build_tweet_out(t) for t in feed_tweets]
