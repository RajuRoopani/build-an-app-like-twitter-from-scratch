"""
Twitter Microblogging App — FastAPI entry point.

Startup:
    uvicorn twitter_app.main:app --reload

Routes served:
    GET  /          → static/index.html
    All API routes via mounted routers (see below)
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from twitter_app.routers import (
    follows,
    hashtags,
    likes,
    mentions,
    retweets,
    timeline,
    trending,
    tweets,
    users,
)

# ── App instance ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Twitter Microblogging API",
    description="A Twitter-like microblogging platform with users, tweets, follows, likes, retweets, timelines, trending hashtags and @mentions.",
    version="1.0.0",
)

# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(users.router)
app.include_router(tweets.router)
app.include_router(retweets.router)
app.include_router(follows.router)
app.include_router(likes.router)
app.include_router(timeline.router)
app.include_router(hashtags.router)
app.include_router(trending.router)
app.include_router(mentions.router)

# ── Static files ───────────────────────────────────────────────────────────────

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Mount /static for any additional assets (CSS, JS) served later
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


# ── Root route — serve frontend ────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    """Serve the single-page frontend application."""
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))
