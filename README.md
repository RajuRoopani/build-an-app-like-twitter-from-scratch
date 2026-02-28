# Twitter-like Microblogging App

A modern, lightweight Twitter clone built with **FastAPI** and **Pydantic v2**. This API provides a complete microblogging platform with users, tweets (280 character limit), retweets, quote tweets, follows, likes, timelines, trending hashtags, and @mentions support.

## Features

- **User Management** — Register, retrieve, and update user profiles
- **Tweets** — Create original tweets with automatic hashtag and @mention extraction (280 char max)
- **Retweets** — Retweet existing tweets with automatic tracking
- **Quote Tweets** — Quote an existing tweet with your own commentary (280 char max)
- **Follows** — Follow/unfollow other users with dual-index follower/following tracking
- **Likes** — Like and unlike tweets with deduplication
- **Personalized Timeline** — View tweets from all users you follow
- **Hashtag Search** — Browse all tweets using a specific hashtag
- **Trending Hashtags** — Discover the top 10 most-used hashtags
- **@Mentions** — View all tweets that mention a specific user
- **Single-Page Frontend** — Responsive HTML/CSS/JavaScript UI for all features

## Tech Stack

- **Python 3.10+**
- **FastAPI 0.110+** — Modern async web framework
- **Pydantic v2** — Data validation and serialization
- **uvicorn 0.29+** — ASGI server
- **pytest 8.0+** — Testing framework
- **httpx 0.27+** — HTTP client for testing
- **python-multipart 0.0.9+** — Form data parsing

## Project Structure

```
twitter_app/
├── __init__.py
├── main.py                          # FastAPI app entry point with routers & static files
├── models.py                        # Pydantic v2 models (request/response schemas)
├── storage.py                       # In-memory storage (users, tweets, follows, likes, etc.)
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
│
├── routers/                         # API endpoint routers (one per resource)
│   ├── __init__.py
│   ├── users.py                     # POST/GET/PUT users, GET user tweets
│   ├── tweets.py                    # POST/GET/DELETE tweets, hashtag extraction
│   ├── retweets.py                  # POST retweets & quote tweets
│   ├── follows.py                   # POST/DELETE follows, GET followers/following
│   ├── likes.py                     # POST/DELETE likes for tweets
│   ├── timeline.py                  # GET personalized timeline
│   ├── hashtags.py                  # GET tweets by hashtag
│   ├── trending.py                  # GET top 10 trending hashtags
│   └── mentions.py                  # GET tweets mentioning a user
│
├── static/
│   └── index.html                   # Single-page frontend (HTML/CSS/JS)
│
├── docs/
│   ├── twitter-api-design.md        # API design document
│   └── adr/
│       └── ADR-001-in-memory-storage-with-dual-index.md
│
└── tests/                           # pytest test suite
    ├── __init__.py
    ├── conftest.py                  # Shared test fixtures
    ├── test_users.py                # User endpoints & auth
    ├── test_tweets.py               # Tweet creation, retrieval, deletion
    ├── test_retweets.py             # Retweets & quote tweets
    ├── test_likes.py                # Like/unlike functionality
    ├── test_timeline.py             # Personalized timeline
    ├── test_hashtags.py             # Hashtag search & extraction
    ├── test_trending.py             # Trending hashtags
    └── test_mentions.py             # @mention functionality
```

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/build-an-app-like-twitter-from-scratch.git
cd build-an-app-like-twitter-from-scratch
```

### 2. Install Dependencies

```bash
pip install -r twitter_app/requirements.txt
```

### 3. Run the Development Server

```bash
uvicorn twitter_app.main:app --reload
```

The API will be available at:
- **API endpoints:** `http://localhost:8000`
- **Interactive API docs (Swagger UI):** `http://localhost:8000/docs`
- **Frontend:** `http://localhost:8000/`

## API Endpoints

All endpoints return JSON responses. Status codes follow REST conventions (200 OK, 201 Created, 204 No Content, 400 Bad Request, 404 Not Found, 409 Conflict).

### Users

| Method | Endpoint | Status Codes | Description |
|--------|----------|--------------|-------------|
| **POST** | `/users` | 201, 409 | Register a new user. Returns 409 if username is taken. |
| **GET** | `/users/{user_id}` | 200, 404 | Retrieve user profile with follower/following counts. |
| **PUT** | `/users/{user_id}` | 200, 404 | Update display_name and/or bio. |
| **GET** | `/users/{user_id}/tweets` | 200, 404 | List all tweets by user (newest first). |

### Tweets

| Method | Endpoint | Status Codes | Description |
|--------|----------|--------------|-------------|
| **POST** | `/tweets` | 201, 400, 404 | Create new tweet (max 280 chars). Extracts #hashtags & @mentions. Returns 404 if user not found. |
| **GET** | `/tweets/{tweet_id}` | 200, 404 | Retrieve tweet with like/retweet/quote counts and author info. |
| **DELETE** | `/tweets/{tweet_id}` | 204, 404 | Delete tweet. Returns 204 No Content. |

### Retweets & Quote Tweets

| Method | Endpoint | Status Codes | Description |
|--------|----------|--------------|-------------|
| **POST** | `/tweets/{tweet_id}/retweet` | 201, 404 | Retweet an existing tweet. |
| **POST** | `/tweets/{tweet_id}/quote` | 201, 400, 404 | Quote a tweet with commentary (max 280 chars). |

### Follows

| Method | Endpoint | Status Codes | Description |
|--------|----------|--------------|-------------|
| **POST** | `/users/{user_id}/follow` | 200, 400, 404, 409 | Follow another user. Returns 400 if self-follow, 409 if already following. |
| **DELETE** | `/users/{user_id}/follow?target_user_id=X` | 200, 404 | Unfollow a user. target_user_id is a query parameter. |
| **GET** | `/users/{user_id}/followers` | 200, 404 | List all users following this user. |
| **GET** | `/users/{user_id}/following` | 200, 404 | List all users this user follows. |

### Likes

| Method | Endpoint | Status Codes | Description |
|--------|----------|--------------|-------------|
| **POST** | `/tweets/{tweet_id}/like` | 200, 404, 409 | Like a tweet. Returns 409 if already liked. |
| **DELETE** | `/tweets/{tweet_id}/like?user_id=X` | 200, 404 | Unlike a tweet. user_id is a query parameter. |

### Timeline & Discover

| Method | Endpoint | Status Codes | Description |
|--------|----------|--------------|-------------|
| **GET** | `/users/{user_id}/timeline` | 200, 404 | Personalized timeline from followed users (newest first). |
| **GET** | `/hashtags/{tag}/tweets` | 200 | All tweets using hashtag (newest first). Tag without # prefix. |
| **GET** | `/trending` | 200 | Top 10 trending hashtags by usage count. |
| **GET** | `/users/{user_id}/mentions` | 200, 404 | All tweets mentioning this user (newest first). |

## Running Tests

Run the full test suite:

```bash
pytest twitter_app/tests/ -v
```

Run a specific test file:

```bash
pytest twitter_app/tests/test_users.py -v
```

Run a specific test:

```bash
pytest twitter_app/tests/test_tweets.py::test_create_tweet -v
```

Show coverage:

```bash
pytest twitter_app/tests/ --cov=twitter_app
```

## Design Decisions

### In-Memory Storage

The app uses **in-memory dictionaries** (not a database) for simplicity:
- `storage.users` — User profiles by user_id
- `storage.usernames` — Username → user_id index (case-insensitive)
- `storage.tweets` — All tweets, retweets, quote tweets by tweet_id
- `storage.followers` — Set of follower IDs per user
- `storage.following` — Set of following IDs per user
- `storage.likes` — Set of user IDs who liked each tweet
- `storage.hashtag_index` — Hashtag → list of tweet IDs

**Rationale:** Fast lookup, simple to understand, ideal for a learning project. A production app would use PostgreSQL with proper indexing.

### Computed Counts

Tweet counts, like counts, retweet counts, and quote counts are **computed on-read** from storage:
- No separate counter fields to keep in sync
- Always accurate even after deletions
- Slightly slower on large datasets, but simpler code

### Dual-Index for Follows

Both `storage.followers` (who follows me) and `storage.following` (who I follow) are maintained:
- O(1) lookups in both directions
- Slightly more memory usage, but faster queries
- Prevents N² scans when checking follower lists

### 280-Character Limit

Enforced at **both Pydantic validation** and **route handler** levels:
- Pydantic catches invalid requests early
- Route handler is defensive against edge cases

### Hashtag & Mention Extraction

Automatic extraction via regex patterns:
- `#hashtag` → lowercase hashtag stored (case-insensitive search)
- `@username` → mention stored as-is (case-insensitive matching on usernames)
- Duplicates removed but order preserved

### Tweet Types

Three tweet types in a single `tweets` table:
- `type="tweet"` — Original tweets with content
- `type="retweet"` — References original_tweet_id, content is null
- `type="quote"` — References original_tweet_id with own content

**Alternative:** Separate tables per type (more normalized, more complex).

### Nested Author & Original Tweet Objects

TweetOut responses include:
- `author` — Full UserOut object (reduces frontend requests)
- `original_tweet` — Nested TweetOut for retweets/quotes (up to depth=1)

**Rationale:** Better UX (fewer API calls), prevents infinite recursion loops.

### Error Responses

Consistent error format:

```json
{
  "detail": "User 'abc123' not found"
}
```

Status codes:
- **400** — Content validation failed (e.g., tweet >280 chars)
- **404** — Resource not found (user, tweet)
- **409** — Conflict (username taken, already following, already liked)

## Example Workflows

### Create a User

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "display_name": "Alice Smith",
    "bio": "Software engineer"
  }'
```

Response:
```json
{
  "id": "uuid-here",
  "username": "alice",
  "display_name": "Alice Smith",
  "bio": "Software engineer",
  "followers_count": 0,
  "following_count": 0,
  "tweet_count": 0,
  "created_at": "2024-01-15T10:30:00.123456"
}
```

### Create a Tweet

```bash
curl -X POST http://localhost:8000/tweets \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid-here",
    "content": "Hello Twitter! #hello @bob"
  }'
```

Response:
```json
{
  "id": "tweet-uuid",
  "type": "tweet",
  "user_id": "uuid-here",
  "content": "Hello Twitter! #hello @bob",
  "created_at": "2024-01-15T10:35:00.123456",
  "hashtags": ["hello"],
  "mentions": ["bob"],
  "like_count": 0,
  "retweet_count": 0,
  "quote_count": 0,
  "original_tweet_id": null,
  "original_tweet": null,
  "author": {
    "id": "uuid-here",
    "username": "alice",
    "display_name": "Alice Smith",
    "bio": "Software engineer",
    "followers_count": 0,
    "following_count": 0,
    "tweet_count": 1,
    "created_at": "2024-01-15T10:30:00.123456"
  }
}
```

### Follow a User

```bash
curl -X POST http://localhost:8000/users/uuid-alice/follow \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": "uuid-bob"
  }'
```

Response:
```json
{
  "detail": "Now following 'uuid-bob'"
}
```

### Get Trending Hashtags

```bash
curl http://localhost:8000/trending
```

Response:
```json
[
  {
    "hashtag": "hello",
    "count": 3
  },
  {
    "hashtag": "fastapi",
    "count": 2
  }
]
```

## Frontend

The single-page app at `http://localhost:8000/` provides:
- **Home** — Timeline view with tweets from followed users
- **Explore** — Trending hashtags and search
- **Profile** — User profile, followers, following
- **Compose** — Create new tweets, retweets, quote tweets
- **Responsive Design** — Works on desktop and mobile

## Deployment

To run in production:

```bash
# Use a production ASGI server (gunicorn + uvicorn)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker twitter_app.main:app
```

Or with Docker:

```bash
docker build -t twitter-app .
docker run -p 8000:8000 twitter-app
```

## Limitations & Future Work

**Current limitations:**
- In-memory storage (lost on server restart)
- No authentication/authorization
- No rate limiting
- No database persistence
- No tweet threads or replies (only retweets/quotes)

**Future improvements:**
- PostgreSQL database with migrations
- JWT authentication
- Rate limiting and spam detection
- Direct messages
- Tweet notifications
- Hashtag trends over time
- Search across all tweets
- Tweet analytics (impressions, engagement)

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Write tests for your feature
3. Ensure all tests pass: `pytest twitter_app/tests/ -v`
4. Commit: `git commit -am 'feat: add my feature'`
5. Push and open a Pull Request

## License

MIT License — see LICENSE file for details.

## Support

For issues or questions, open a GitHub issue or contact the maintainers.

---

**Built with ❤️ using FastAPI**
