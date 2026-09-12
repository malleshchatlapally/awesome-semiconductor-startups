from __future__ import annotations

import argparse
import json
import sys

from ktr_x_agent.client import XApiError, fetch_recent_posts, resolve_handles


def _print_posts(handle: str, display_name: str, posts: list) -> None:
    print(f"\n@{handle} — {display_name}")
    print("-" * 72)
    if not posts:
        print("(no posts returned)")
        return
    for index, post in enumerate(posts, start=1):
        when = post.created_at or "unknown time"
        metrics = []
        if post.like_count is not None:
            metrics.append(f"♥ {post.like_count}")
        if post.retweet_count is not None:
            metrics.append(f"↻ {post.retweet_count}")
        if post.reply_count is not None:
            metrics.append(f"💬 {post.reply_count}")
        metric_line = "  ".join(metrics)
        print(f"{index}. [{when}]")
        print(post.text)
        if metric_line:
            print(metric_line)
        print(post.url)
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Show recent posts from KTR-related X accounts (official X API v2)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Posts per account (default: 10, max 100)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of formatted text",
    )
    parser.add_argument(
        "--handle",
        action="append",
        dest="handles",
        metavar="USERNAME",
        help="Override default handles; may be passed multiple times",
    )
    args = parser.parse_args(argv)

    handles = [h.lstrip("@") for h in args.handles] if args.handles else resolve_handles()
    limit = max(1, min(args.limit, 100))

    results: dict[str, object] = {}
    try:
        for handle in handles:
            display_name, posts = fetch_recent_posts(handle, limit=limit)
            if args.json:
                results[handle] = {
                    "display_name": display_name,
                    "posts": [
                        {
                            "id": p.id,
                            "text": p.text,
                            "created_at": p.created_at,
                            "url": p.url,
                            "like_count": p.like_count,
                            "retweet_count": p.retweet_count,
                            "reply_count": p.reply_count,
                        }
                        for p in posts
                    ],
                }
            else:
                _print_posts(handle, display_name, posts)
    except XApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
