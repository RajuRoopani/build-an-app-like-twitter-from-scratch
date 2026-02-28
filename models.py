"""
Pydantic models (request / response) for the Twitter Microblogging App.

All models use Pydantic v2 BaseModel.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, field_validator


# ── User models ────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Request body for POST /users."""

    username: str
    display_name: str
    bio: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_nonempty(cls, v: str) -> str:
        """Username must not be blank."""
        v = v.strip()
        if not v:
            raise ValueError("username must not be empty")
        return v

    @field_validator("display_name")
    @classmethod
    def display_name_nonempty(cls, v: str) -> str:
        """Display name must not be blank."""
        v = v.strip()
        if not v:
            raise ValueError("display_name must not be empty")
        return v


class UserUpdate(BaseModel):
    """Request body for PUT /users/{user_id}."""

    display_name: Optional[str] = None
    bio: Optional[str] = None


class UserOut(BaseModel):
    """Response shape for a user resource."""

    id: str
    username: str
    display_name: str
    bio: Optional[str] = None
    followers_count: int
    following_count: int
    tweet_count: int
    created_at: str


# ── Tweet models ───────────────────────────────────────────────────────────────

class TweetCreate(BaseModel):
    """Request body for POST /tweets."""

    user_id: str
    content: str

    @field_validator("content")
    @classmethod
    def content_max_length(cls, v: str) -> str:
        """Tweet content must not exceed 280 characters."""
        if len(v) > 280:
            raise ValueError("content must not exceed 280 characters")
        return v


class TweetOut(BaseModel):
    """Response shape for a tweet resource (original, retweet, or quote)."""

    id: str
    type: str                               # 'tweet' | 'retweet' | 'quote'
    user_id: str
    content: Optional[str] = None
    created_at: str
    hashtags: List[str] = []
    mentions: List[str] = []
    like_count: int = 0
    retweet_count: int = 0
    quote_count: int = 0
    original_tweet_id: Optional[str] = None
    original_tweet: Optional[TweetOut] = None
    author: Optional[UserOut] = None


# Required for self-referential model rebuild (Pydantic v2)
TweetOut.model_rebuild()


# ── Retweet / Quote models ─────────────────────────────────────────────────────

class RetweetCreate(BaseModel):
    """Request body for POST /tweets/{tweet_id}/retweet."""

    user_id: str


class QuoteTweetCreate(BaseModel):
    """Request body for POST /tweets/{tweet_id}/quote."""

    user_id: str
    content: str

    @field_validator("content")
    @classmethod
    def content_max_length(cls, v: str) -> str:
        """Quote content must not exceed 280 characters."""
        if len(v) > 280:
            raise ValueError("content must not exceed 280 characters")
        return v


# ── Follow models ──────────────────────────────────────────────────────────────

class FollowRequest(BaseModel):
    """Request body for POST /users/{user_id}/follow."""

    target_user_id: str


# ── Like models ────────────────────────────────────────────────────────────────

class LikeRequest(BaseModel):
    """Request body for POST /tweets/{tweet_id}/like."""

    user_id: str


# ── Trending models ────────────────────────────────────────────────────────────

class TrendingItem(BaseModel):
    """Single entry in the trending hashtags list."""

    hashtag: str
    count: int
