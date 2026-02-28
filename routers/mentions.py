"""
Mentions router — AC34-AC36.

Endpoints:
  GET /users/{user_id}/mentions  → 200 List[TweetOut]  newest first, empty list if none.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from twitter_app import storage
from twitter_app.models import TweetOut

router = APIRouter(prefix="/users", tags=["mentions"])


# ── GET /users/{user_id}/mentions ─────────────────────────────────────────────

@router.get("/{user_id}/mentions", response_model=List[TweetOut])
def get_mentions(user_id: str) -> List[TweetOut]:
    """
    List all tweets where the user's @username was mentioned, newest first.

    Matching is case-insensitive against the stored username.
    Returns 404 if the user does not exist.
    Returns an empty list if no tweets mention this user.
    """
    user = storage.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    from twitter_app.routers.tweets import _build_tweet_out

    username_lower = user["username"].lower()

    mentioned_tweets = [
        t for t in storage.tweets.values()
        if any(m.lower() == username_lower for m in t.get("mentions", []))
    ]
    mentioned_tweets.sort(key=lambda t: t["created_at"], reverse=True)
    return [_build_tweet_out(t) for t in mentioned_tweets]
