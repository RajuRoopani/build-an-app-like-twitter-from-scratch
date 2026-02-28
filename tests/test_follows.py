"""
Test suite: Follows
Tests POST /users/{id}/follow, DELETE /users/{id}/follow,
GET /users/{id}/followers, GET /users/{id}/following,
and count behaviour.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_user(client: TestClient, username: str = "alice", display_name: str = "Alice") -> dict:
    r = client.post("/users", json={"username": username, "display_name": display_name})
    assert r.status_code == 201, r.text
    return r.json()


def _follow(client: TestClient, follower_id: str, target_id: str) -> None:
    r = client.post(f"/users/{follower_id}/follow", json={"target_user_id": target_id})
    assert r.status_code == 200, r.text


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestFollow:
    def test_follow_returns_200(self, client: TestClient) -> None:
        """POST /users/{id}/follow returns 200 on success."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        r = client.post(f"/users/{alice['id']}/follow", json={"target_user_id": bob["id"]})
        assert r.status_code == 200

    def test_follow_self_returns_400(self, client: TestClient) -> None:
        """POST /users/{id}/follow with own ID returns 400."""
        alice = _create_user(client, "alice", "Alice")
        r = client.post(f"/users/{alice['id']}/follow", json={"target_user_id": alice["id"]})
        assert r.status_code == 400

    def test_follow_nonexistent_follower_404(self, client: TestClient) -> None:
        """POST /users/bad-id/follow returns 404 when the follower user doesn't exist."""
        bob = _create_user(client, "bob", "Bob")
        r = client.post(
            "/users/ghost-follower-id/follow",
            json={"target_user_id": bob["id"]},
        )
        assert r.status_code == 404

    def test_follow_nonexistent_target_404(self, client: TestClient) -> None:
        """POST /users/{id}/follow returns 404 when target user doesn't exist."""
        alice = _create_user(client, "alice", "Alice")
        r = client.post(f"/users/{alice['id']}/follow", json={"target_user_id": "ghost-target"})
        assert r.status_code == 404

    def test_follow_duplicate_returns_409(self, client: TestClient) -> None:
        """POST /users/{id}/follow when already following returns 409."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, alice["id"], bob["id"])
        r = client.post(f"/users/{alice['id']}/follow", json={"target_user_id": bob["id"]})
        assert r.status_code == 409

    def test_follow_increments_following_count(self, client: TestClient) -> None:
        """following_count on the follower increments after follow."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, alice["id"], bob["id"])
        r = client.get(f"/users/{alice['id']}")
        assert r.json()["following_count"] == 1

    def test_follow_increments_followers_count(self, client: TestClient) -> None:
        """followers_count on the target increments after follow."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, alice["id"], bob["id"])
        r = client.get(f"/users/{bob['id']}")
        assert r.json()["followers_count"] == 1

    def test_follow_multiple_users_counts_correctly(self, client: TestClient) -> None:
        """following_count reflects multiple follows."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        carol = _create_user(client, "carol", "Carol")
        _follow(client, alice["id"], bob["id"])
        _follow(client, alice["id"], carol["id"])
        r = client.get(f"/users/{alice['id']}")
        assert r.json()["following_count"] == 2


class TestUnfollow:
    def test_unfollow_returns_200(self, client: TestClient) -> None:
        """DELETE /users/{id}/follow returns 200 on success."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, alice["id"], bob["id"])
        r = client.delete(f"/users/{alice['id']}/follow?target_user_id={bob['id']}")
        assert r.status_code == 200

    def test_unfollow_not_following_404(self, client: TestClient) -> None:
        """DELETE /users/{id}/follow returns 404 when the follow relationship doesn't exist."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        r = client.delete(f"/users/{alice['id']}/follow?target_user_id={bob['id']}")
        assert r.status_code == 404

    def test_unfollow_decrements_following_count(self, client: TestClient) -> None:
        """following_count decrements after unfollow."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, alice["id"], bob["id"])
        client.delete(f"/users/{alice['id']}/follow?target_user_id={bob['id']}")
        r = client.get(f"/users/{alice['id']}")
        assert r.json()["following_count"] == 0

    def test_unfollow_decrements_followers_count(self, client: TestClient) -> None:
        """followers_count decrements after unfollow."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, alice["id"], bob["id"])
        client.delete(f"/users/{alice['id']}/follow?target_user_id={bob['id']}")
        r = client.get(f"/users/{bob['id']}")
        assert r.json()["followers_count"] == 0


class TestFollowersAndFollowingLists:
    def test_get_followers_200(self, client: TestClient) -> None:
        """GET /users/{id}/followers returns 200 with a list of follower UserOut objects."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, bob["id"], alice["id"])  # bob follows alice
        r = client.get(f"/users/{alice['id']}/followers")
        assert r.status_code == 200
        followers = r.json()
        assert isinstance(followers, list)
        assert any(f["username"] == "bob" for f in followers)

    def test_get_followers_empty(self, client: TestClient) -> None:
        """GET /users/{id}/followers returns empty list when user has no followers."""
        alice = _create_user(client, "alice", "Alice")
        r = client.get(f"/users/{alice['id']}/followers")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_following_200(self, client: TestClient) -> None:
        """GET /users/{id}/following returns 200 with a list of followed UserOut objects."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, alice["id"], bob["id"])  # alice follows bob
        r = client.get(f"/users/{alice['id']}/following")
        assert r.status_code == 200
        following = r.json()
        assert isinstance(following, list)
        assert any(f["username"] == "bob" for f in following)

    def test_get_following_empty(self, client: TestClient) -> None:
        """GET /users/{id}/following returns empty list when user follows nobody."""
        alice = _create_user(client, "alice", "Alice")
        r = client.get(f"/users/{alice['id']}/following")
        assert r.status_code == 200
        assert r.json() == []

    def test_followers_list_reflects_unfollow(self, client: TestClient) -> None:
        """After unfollow, the follower no longer appears in the followers list."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, bob["id"], alice["id"])
        client.delete(f"/users/{bob['id']}/follow?target_user_id={alice['id']}")
        r = client.get(f"/users/{alice['id']}/followers")
        assert r.json() == []

    def test_following_list_reflects_unfollow(self, client: TestClient) -> None:
        """After unfollow, the target no longer appears in the following list."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, alice["id"], bob["id"])
        client.delete(f"/users/{alice['id']}/follow?target_user_id={bob['id']}")
        r = client.get(f"/users/{alice['id']}/following")
        assert r.json() == []

    def test_followers_list_userout_shape(self, client: TestClient) -> None:
        """Each entry in the followers list is a valid UserOut with expected fields."""
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        _follow(client, bob["id"], alice["id"])
        followers = client.get(f"/users/{alice['id']}/followers").json()
        assert len(followers) == 1
        follower = followers[0]
        assert "id" in follower
        assert "username" in follower
        assert "display_name" in follower
        assert "followers_count" in follower
        assert "following_count" in follower
        assert "tweet_count" in follower
