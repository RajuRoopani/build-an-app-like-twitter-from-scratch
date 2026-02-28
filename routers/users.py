"""
Users router — AC6-AC9.

Endpoints:
  POST   /users                    → 201 UserOut  (409 if username taken)
  GET    /users/{user_id}          → 200 UserOut  (404 if not found)
  PUT    /users/{user_id}          → 200 UserOut  (404 if not found)
  GET    /users/{user_id}/tweets   → 200 List[TweetOut]
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from twitter_app import storage
from twitter_app.models import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_user_out(user: dict) -> UserOut:
    """Construct a UserOut from a stored user dict with computed counts."""
    uid = user["id"]
    tweet_count = sum(
        1 for t in storage.tweets.values() if t["user_id"] == uid
    )
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


def _get_user_or_404(user_id: str) -> dict:
    """Return a stored user dict or raise 404."""
    user = storage.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return user


# ── POST /users ────────────────────────────────────────────────────────────────

@router.post("", status_code=201, response_model=UserOut)
def create_user(body: UserCreate) -> UserOut:
    """
    Register a new user.

    - **username** must be unique (case-insensitive). Returns 409 if taken.
    - **display_name** is required.
    - **bio** is optional.
    """
    normalized = body.username.lower()
    if normalized in storage.usernames:
        raise HTTPException(
            status_code=409,
            detail=f"Username '{body.username}' is already taken",
        )

    uid = str(uuid4())
    now = datetime.utcnow().isoformat()

    user = {
        "id": uid,
        "username": body.username,
        "display_name": body.display_name,
        "bio": body.bio,
        "created_at": now,
    }

    storage.users[uid] = user
    storage.usernames[normalized] = uid
    storage.followers[uid] = set()
    storage.following[uid] = set()

    return _build_user_out(user)


# ── GET /users/{user_id} ───────────────────────────────────────────────────────

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str) -> UserOut:
    """
    Retrieve a user by ID.

    Returns 404 if the user does not exist.
    """
    user = _get_user_or_404(user_id)
    return _build_user_out(user)


# ── PUT /users/{user_id} ───────────────────────────────────────────────────────

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: str, body: UserUpdate) -> UserOut:
    """
    Update a user's display_name and/or bio.

    Returns 404 if the user does not exist.
    """
    user = _get_user_or_404(user_id)

    if body.display_name is not None:
        user["display_name"] = body.display_name
    if body.bio is not None:
        user["bio"] = body.bio

    return _build_user_out(user)


# ── GET /users/{user_id}/tweets ────────────────────────────────────────────────

@router.get("/{user_id}/tweets")
def get_user_tweets(user_id: str) -> list:
    """
    List all tweets (originals, retweets, and quote tweets) by a user,
    newest first.

    Returns 404 if the user does not exist.
    """
    _get_user_or_404(user_id)

    # Import here to avoid circular import at module load time
    from twitter_app.routers.tweets import _build_tweet_out

    user_tweets = [
        t for t in storage.tweets.values() if t["user_id"] == user_id
    ]
    user_tweets.sort(key=lambda t: t["created_at"], reverse=True)
    return [_build_tweet_out(t) for t in user_tweets]
