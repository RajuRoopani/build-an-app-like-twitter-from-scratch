# Twitter Microblogging App — Architecture

## Overview

A Twitter-like microblogging REST API built with FastAPI and in-memory storage.
A single-page frontend will be served from `GET /`. All business data lives in
module-level Python dicts; `reset_storage()` provides a clean-slate for tests.
Nine routers cover the full feature surface: users, tweets, retweets, follows,
likes, timeline, hashtags, trending, and mentions.

---

## Components

| Component | File | Role |
|---|---|---|
| App entry | `main.py` | FastAPI instance, router mounting, static file serving |
| Storage | `storage.py` | Module-level in-memory stores + `reset_storage()` |
| Models | `models.py` | Pydantic v2 request/response shapes |
| Users router | `routers/users.py` | User CRUD + user tweet list |
| Tweets router | `routers/tweets.py` | Tweet CRUD, hashtag/mention extraction, shared helpers |
| Retweets router | `routers/retweets.py` | Retweet + quote tweet creation |
| Follows router | `routers/follows.py` | Follow/unfollow, followers/following lists |
| Likes router | `routers/likes.py` | Like/unlike a tweet |
| Timeline router | `routers/timeline.py` | Personalised feed from followed users |
| Hashtags router | `routers/hashtags.py` | Tweets by hashtag |
| Trending router | `routers/trending.py` | Top-10 hashtags by tweet count |
| Mentions router | `routers/mentions.py` | Tweets that @mention a user |
| Frontend | `static/index.html` | Placeholder; full SPA built by UX engineer |
| Test config | `tests/conftest.py` | `reset` autouse fixture + `client` fixture |

---

## Data Flow

```
Client
  │
  ▼
FastAPI (main.py)
  ├── GET /           → FileResponse(static/index.html)
  ├── /users          → users.py, follows.py, timeline.py, mentions.py
  ├── /tweets         → tweets.py, retweets.py, likes.py
  ├── /hashtags       → hashtags.py
  └── /trending       → trending.py
          │
          ▼
     storage.py   (module-level dicts — shared by all routers)
     ┌────────────────────────────────────────────────┐
     │  users{}         usernames{}                   │
     │  tweets{}                                      │
     │  followers{}     following{}                   │
     │  likes{}                                       │
     │  hashtag_index{}                               │
     └────────────────────────────────────────────────┘
```

---

## API Contracts

### Users

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| POST | `/users` | `{username, display_name, bio?}` | 201 UserOut | 409 duplicate username |
| GET | `/users/{user_id}` | — | 200 UserOut | 404 |
| PUT | `/users/{user_id}` | `{display_name?, bio?}` | 200 UserOut | 404 |
| GET | `/users/{user_id}/tweets` | — | 200 List[TweetOut] | 404 |

### Tweets

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| POST | `/tweets` | `{user_id, content}` | 201 TweetOut | 400 >280 chars, 404 user |
| GET | `/tweets/{tweet_id}` | — | 200 TweetOut | 404 |
| DELETE | `/tweets/{tweet_id}` | — | 204 | 404 |

### Retweets & Quotes

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| POST | `/tweets/{tweet_id}/retweet` | `{user_id}` | 201 TweetOut | 404 tweet/user |
| POST | `/tweets/{tweet_id}/quote` | `{user_id, content}` | 201 TweetOut | 400 >280, 404 tweet/user |

### Follows

| Method | Path | Body/Query | Success | Errors |
|---|---|---|---|---|
| POST | `/users/{user_id}/follow` | body: `{target_user_id}` | 200 | 400 self-follow, 404, 409 duplicate |
| DELETE | `/users/{user_id}/follow` | query: `target_user_id=` | 200 | 404 |
| GET | `/users/{user_id}/followers` | — | 200 List[UserOut] | 404 |
| GET | `/users/{user_id}/following` | — | 200 List[UserOut] | 404 |

### Likes

| Method | Path | Body/Query | Success | Errors |
|---|---|---|---|---|
| POST | `/tweets/{tweet_id}/like` | body: `{user_id}` | 200 | 404 tweet, 409 double-like |
| DELETE | `/tweets/{tweet_id}/like` | query: `user_id=` | 200 | 404 |

### Timeline

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/users/{user_id}/timeline` | 200 List[TweetOut] newest-first | 404 |

### Hashtags

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/hashtags/{tag}/tweets` | 200 List[TweetOut] newest-first | — (empty list) |

### Trending

| Method | Path | Success |
|---|---|---|
| GET | `/trending` | 200 List[TrendingItem{hashtag, count}] top-10 |

### Mentions

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/users/{user_id}/mentions` | 200 List[TweetOut] newest-first | 404 |

---

## Data Model

### `users` dict (keyed by user_id)
```
{
  "id":           str (uuid4),
  "username":     str,
  "display_name": str,
  "bio":          str | None,
  "created_at":   str (ISO 8601 UTC)
}
```
Derived counts (not stored): `followers_count`, `following_count`, `tweet_count`

### `tweets` dict (keyed by tweet_id)
```
{
  "id":                str (uuid4),
  "type":              "tweet" | "retweet" | "quote",
  "user_id":           str,
  "content":           str | None   (None for pure retweets),
  "created_at":        str (ISO 8601 UTC),
  "hashtags":          List[str]    (lowercase),
  "mentions":          List[str]    (as-typed, case-insensitive on lookup),
  "original_tweet_id": str | None
}
```
Derived counts: `like_count` (from `likes`), `retweet_count`, `quote_count` (scan `tweets`)

### `followers` / `following` (keyed by user_id, value: Set[str])
Dual index maintained in sync: mutation in `follows.py` writes to both.

### `likes` (keyed by tweet_id, value: Set[user_id])

### `hashtag_index` (keyed by lowercase hashtag, value: List[tweet_id])
Tweets append on creation; removed on deletion. Trending uses this index with
a live-count pass to exclude deleted tweets.

### `usernames` (keyed by lowercase username, value: user_id)
Enables O(1) uniqueness checks and O(1) mention lookups.

---

## Non-Functional Considerations

### Security
- All IDs are UUIDv4 — not guessable or sequential
- Username uniqueness enforced case-insensitively
- Content length validated at both Pydantic model layer AND router layer
- No authentication in v1 (in-memory, single-process scope — auth is out-of-scope)

### Performance
- All lookups are O(1) dict access; counts are O(n) scans (acceptable for in-memory)
- Sorting is O(n log n) on `created_at` string — ISO 8601 sorts lexicographically correctly
- `_build_tweet_out` depth guard prevents runaway recursion on nested tweet chains

### Scalability
- In-memory store is single-process; swap for Redis/PostgreSQL when persistence is needed
- Hashtag index and follow sets can be moved to sorted sets (Redis) with minimal API change
- All counts are computed dynamically — no counter drift risk

### Testability
- `reset_storage()` clears all stores atomically
- `autouse` fixture in `conftest.py` ensures test isolation
- No global state leaks between tests
