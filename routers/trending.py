"""
Trending router — AC32-AC33.

Endpoints:
  GET /trending  → 200 List[TrendingItem]  top 10 hashtags by tweet count, descending.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter

from twitter_app import storage
from twitter_app.models import TrendingItem

router = APIRouter(tags=["trending"])


# ── GET /trending ──────────────────────────────────────────────────────────────

@router.get("/trending", response_model=List[TrendingItem])
def get_trending() -> List[TrendingItem]:
    """
    Return the top 10 trending hashtags ranked by number of tweets that use them.

    Only counts tweets that currently exist in storage (deleted tweets excluded).
    Returns an empty list if no hashtags have been used.
    """
    # Compute live counts (respects deleted tweets)
    counts: dict[str, int] = {}
    for tag, tweet_ids in storage.hashtag_index.items():
        live_count = sum(1 for tid in tweet_ids if tid in storage.tweets)
        if live_count > 0:
            counts[tag] = live_count

    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return [TrendingItem(hashtag=tag, count=cnt) for tag, cnt in ranked]
