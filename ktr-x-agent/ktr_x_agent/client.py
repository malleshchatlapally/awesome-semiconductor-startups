from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

API_BASE = "https://api.x.com/2"
DEFAULT_HANDLES = ("KTRBRS", "KTRoffice")


@dataclass(frozen=True)
class Post:
    id: str
    text: str
    created_at: str | None
    url: str
    like_count: int | None
    retweet_count: int | None
    reply_count: int | None


class XApiError(RuntimeError):
    pass


def _bearer_token() -> str:
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    if not token:
        raise XApiError(
            "Missing X_BEARER_TOKEN. Copy ktr-x-agent/.env.example, set your Bearer Token "
            "from https://developer.x.com/, then export X_BEARER_TOKEN or use a .env loader."
        )
    return token


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_bearer_token()}"}


def _get_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(
        f"{API_BASE}{path}",
        headers=_headers(),
        params=params or {},
        timeout=30,
    )
    if response.status_code >= 400:
        detail = response.text.strip() or response.reason
        raise XApiError(f"X API {response.status_code}: {detail}")
    return response.json()


def resolve_handles() -> list[str]:
    raw = os.environ.get("KTR_HANDLES", "").strip()
    if not raw:
        return list(DEFAULT_HANDLES)
    return [h.strip().lstrip("@") for h in raw.split(",") if h.strip()]


def lookup_user_id(username: str) -> tuple[str, str]:
    data = _get_json(
        f"/users/by/username/{username}",
        {"user.fields": "name,username,description"},
    )
    user = data.get("data")
    if not user:
        raise XApiError(f"No user found for @{username}")
    return user["id"], user.get("name") or username


def fetch_recent_posts(username: str, limit: int = 10) -> tuple[str, list[Post]]:
    user_id, display_name = lookup_user_id(username)
    params: dict[str, Any] = {
        "max_results": min(max(limit, 5), 100),
        "tweet.fields": "created_at,public_metrics",
        "exclude": "retweets,replies",
    }
    data = _get_json(f"/users/{user_id}/tweets", params)
    posts: list[Post] = []
    for item in data.get("data", [])[:limit]:
        metrics = item.get("public_metrics") or {}
        post_id = item["id"]
        posts.append(
            Post(
                id=post_id,
                text=item.get("text", ""),
                created_at=item.get("created_at"),
                url=f"https://x.com/{username}/status/{post_id}",
                like_count=metrics.get("like_count"),
                retweet_count=metrics.get("retweet_count"),
                reply_count=metrics.get("reply_count"),
            )
        )
    return display_name, posts
