"""
Follows router — AC20-AC24.

Endpoints:
  POST   /users/{user_id}/follow              → 200  (400 self-follow, 404, 409 duplicate)
  DELETE /users/{user_id}/follow              → 200  (404 if relationship not found)
  GET    /users/{user_id}/followers           → 200 List[UserOut]
  GET    /users/{user_id}/following           → 200 List[UserOut]
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query

from twitter_app import storage
from twitter_app.models import FollowRequest, UserOut

router = APIRouter(prefix="/users", tags=["follows"])


# ── Helper ─────────────────────────────────────────────────────────────────────

def _get_user_or_404(user_id: str) -> dict:
    """Return a stored user dict or raise 404."""
    user = storage.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return user


def _build_user_out(user: dict) -> UserOut:
    """Build a UserOut with computed counts from a stored user dict."""
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


# ── POST /users/{user_id}/follow ───────────────────────────────────────────────

@router.post("/{user_id}/follow", status_code=200)
def follow_user(user_id: str, body: FollowRequest) -> dict:
    """
    Follow another user.

    - Returns 400 if user tries to follow themselves.
    - Returns 404 if either user does not exist.
    - Returns 409 if already following.
    """
    _get_user_or_404(user_id)
    target_id = body.target_user_id
    _get_user_or_404(target_id)

    if user_id == target_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Initialise sets defensively (should already exist from user creation)
    storage.following.setdefault(user_id, set())
    storage.followers.setdefault(target_id, set())

    if target_id in storage.following[user_id]:
        raise HTTPException(
            status_code=409,
            detail=f"Already following user '{target_id}'",
        )

    storage.following[user_id].add(target_id)
    storage.followers[target_id].add(user_id)

    return {"detail": f"Now following '{target_id}'"}


# ── DELETE /users/{user_id}/follow ─────────────────────────────────────────────

@router.delete("/{user_id}/follow", status_code=200)
def unfollow_user(
    user_id: str,
    target_user_id: str = Query(..., description="ID of the user to unfollow"),
) -> dict:
    """
    Unfollow a user.

    target_user_id is passed as a query parameter.
    Returns 404 if either user does not exist or the follow relationship does not exist.
    """
    _get_user_or_404(user_id)
    _get_user_or_404(target_user_id)

    if target_user_id not in storage.following.get(user_id, set()):
        raise HTTPException(
            status_code=404,
            detail=f"Not following user '{target_user_id}'",
        )

    storage.following[user_id].discard(target_user_id)
    storage.followers[target_user_id].discard(user_id)

    return {"detail": f"Unfollowed '{target_user_id}'"}


# ── GET /users/{user_id}/followers ─────────────────────────────────────────────

@router.get("/{user_id}/followers", response_model=List[UserOut])
def get_followers(user_id: str) -> List[UserOut]:
    """
    List all users who follow the specified user.

    Returns 404 if the user does not exist.
    """
    _get_user_or_404(user_id)
    follower_ids = storage.followers.get(user_id, set())
    result = []
    for fid in follower_ids:
        u = storage.users.get(fid)
        if u:
            result.append(_build_user_out(u))
    return result


# ── GET /users/{user_id}/following ─────────────────────────────────────────────

@router.get("/{user_id}/following", response_model=List[UserOut])
def get_following(user_id: str) -> List[UserOut]:
    """
    List all users that the specified user follows.

    Returns 404 if the user does not exist.
    """
    _get_user_or_404(user_id)
    following_ids = storage.following.get(user_id, set())
    result = []
    for fid in following_ids:
        u = storage.users.get(fid)
        if u:
            result.append(_build_user_out(u))
    return result
