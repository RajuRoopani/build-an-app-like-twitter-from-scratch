"""
In-memory storage for the Twitter Microblogging App.

All stores are module-level dicts/sets. Call reset_storage() between tests.

Storage layout:
  users         : Dict[user_id, user_dict]
  usernames     : Dict[username_lower, user_id]   — uniqueness + mention lookups
  tweets        : Dict[tweet_id, tweet_dict]       — type: 'tweet'|'retweet'|'quote'
  followers     : Dict[user_id, Set[user_id]]      — who follows THIS user
  following     : Dict[user_id, Set[user_id]]      — who THIS user follows
  likes         : Dict[tweet_id, Set[user_id]]     — users who liked this tweet
  hashtag_index : Dict[hashtag_lower, List[tweet_id]]
"""

from typing import Dict, List, Set

# ── Core stores ────────────────────────────────────────────────────────────────

users: Dict[str, dict] = {}
usernames: Dict[str, str] = {}          # lowercase_username → user_id

tweets: Dict[str, dict] = {}

followers: Dict[str, Set[str]] = {}     # user_id → set of follower user_ids
following: Dict[str, Set[str]] = {}     # user_id → set of user_ids this user follows

likes: Dict[str, Set[str]] = {}         # tweet_id → set of user_ids

hashtag_index: Dict[str, List[str]] = {}  # lowercase_hashtag → [tweet_id, ...]


# ── Reset ──────────────────────────────────────────────────────────────────────

def reset_storage() -> None:
    """Clear all in-memory stores. Used between test runs."""
    users.clear()
    usernames.clear()
    tweets.clear()
    followers.clear()
    following.clear()
    likes.clear()
    hashtag_index.clear()
