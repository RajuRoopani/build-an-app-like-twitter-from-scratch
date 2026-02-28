"""
Likes router — AC25-AC27.

Endpoints:
  POST   /tweets/{tweet_id}/like   → 200          (404 tweet, 409 double-like)
  DELETE /tweets/{tweet_id}/like   → 200          (404 if not found)
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from twitter_app import storage
from twitter_app.models import LikeRequest

router = APIRouter(prefix="/tweets", tags=["likes"])


# ── Helper ─────────────────────────────────────────────────────────────────────

def _get_tweet_or_404(tweet_id: str) -> dict:
    """Return a stored tweet dict or raise 404."""
    tweet = storage.tweets.get(tweet_id)
    if not tweet:
        raise HTTPException(status_code=404, detail=f"Tweet '{tweet_id}' not found")
    return tweet


# ── POST /tweets/{tweet_id}/like ───────────────────────────────────────────────

@router.post("/{tweet_id}/like", status_code=200)
def like_tweet(tweet_id: str, body: LikeRequest) -> dict:
    """
    Like a tweet.

    - Returns 404 if the tweet does not exist.
    - Returns 409 if the user has already liked this tweet.
    """
    _get_tweet_or_404(tweet_id)

    likers = storage.likes.setdefault(tweet_id, set())

    if body.user_id in likers:
        raise HTTPException(
            status_code=409,
            detail=f"User '{body.user_id}' has already liked tweet '{tweet_id}'",
        )

    likers.add(body.user_id)
    return {"detail": "Tweet liked", "like_count": len(likers)}


# ── DELETE /tweets/{tweet_id}/like ────────────────────────────────────────────

@router.delete("/{tweet_id}/like", status_code=200)
def unlike_tweet(
    tweet_id: str,
    user_id: str = Query(..., description="ID of the user unliking the tweet"),
) -> dict:
    """
    Unlike a tweet.

    user_id is passed as a query parameter.
    Returns 404 if the tweet does not exist or the user had not liked it.
    """
    _get_tweet_or_404(tweet_id)

    likers = storage.likes.get(tweet_id, set())
    if user_id not in likers:
        raise HTTPException(
            status_code=404,
            detail=f"User '{user_id}' has not liked tweet '{tweet_id}'",
        )

    likers.discard(user_id)
    return {"detail": "Tweet unliked", "like_count": len(likers)}
