# ADR-001: In-Memory Storage with Dual-Index Pattern

**Status:** Accepted
**Date:** 2024-01

---

## Context

The Twitter microblogging app needs to support multiple access patterns across
a shared dataset without a real database:

1. Look up a user by ID (most common path)
2. Check username uniqueness (on registration)
3. Resolve @mentions (case-insensitive username → user_id)
4. Find all tweets by a user
5. Find all followers / following for a user
6. Find all tweets using a hashtag

These patterns would normally be served by database indexes. Without a DB,
we need to pre-compute them in module-level data structures.

---

## Decision

Use module-level Python dicts and sets in `storage.py`. Maintain **dual indexes**
wherever an entity needs two access patterns:

- `users` (user_id → user_dict) + `usernames` (lowercase_username → user_id)
- `followers` (user_id → Set[follower_ids]) + `following` (user_id → Set[following_ids])
- `hashtag_index` (lowercase_hashtag → List[tweet_id])
- `likes` (tweet_id → Set[user_id])

All mutations that affect a dual-index write to **both** structures atomically
(within the same request handler, before returning). This pattern was proven
correct in prior projects (DoorDash dual-cart, Instagram follow dual-index).

`reset_storage()` calls `.clear()` on every structure — safe for test isolation
because it mutates the same objects that all routers hold references to.

---

## Consequences

**✅ Benefits**
- O(1) username uniqueness checks (avoids O(n) scan on every POST /users)
- O(1) mention username resolution
- Hashtag search is O(k) where k = matching tweet count (not total tweet count)
- Follower/following retrieval is O(degree) not O(total users)
- Simple to reason about; no ORM or query planner

**⚠️ Trade-offs**
- Every mutation must write to both indexes — a bug that writes only one breaks
  consistency. Mitigated by keeping mutations co-located in the same router function.
- tweet_count, like_count, retweet_count, quote_count are computed dynamically
  (O(n) scans) — acceptable at dev/demo scale, would need stored counters for production.
- All data is lost on process restart — intentional for this phase; persistence
  would require swapping `storage.py` for a DB-backed implementation.
