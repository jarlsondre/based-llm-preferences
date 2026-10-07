# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright"]
# ///
"""Fetch a page the built-in fetch cannot get (login wall, bot block) and print it as text.

Usage: uv run tools/fetch.py URL [--max-chars N] [--depth N] [--limit N]
       uv run tools/fetch.py --login URL   # opens a window; log in, then press Enter

The page loads in headless Firefox. The profile in ~/.local/share/jarl-fetch
keeps logins: one --login per site per machine. Reddit threads print as one
line per comment, other pages as their visible text. --depth (reply levels) and
--limit (comments fetched) apply to Reddit threads only. Once per machine:
uv run --with playwright playwright install firefox
"""

import argparse
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import (  # type: ignore  # uv script dep
    BrowserContext,
    sync_playwright,
)

PROFILE = Path.home() / ".local/share/jarl-fetch"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:128.0) Gecko/20100101 Firefox/128.0"


def reddit_text(ctx: BrowserContext, url: str, depth: int, limit: int) -> str:
    api = (
        url.split("?")[0].rstrip("/") + f".json?limit={limit}&depth={depth}&raw_json=1"
    )
    resp = ctx.request.get(api)
    if not resp.ok:
        sys.exit(
            f"fetch.py: reddit returned {resp.status} for {api}; on 403, run: uv run tools/fetch.py --login URL"
        )
    listing = resp.json()
    post = listing[0]["data"]["children"][0]["data"]
    lines = [f"# {post['title']} [{post['score']}] r/{post['subreddit']}"]
    if post.get("selftext"):
        lines.append(post["selftext"].strip())
    lines.append("")

    def walk(children: list[dict[str, Any]], level: int) -> None:
        for child in children:
            if child["kind"] != "t1":
                continue
            d = child["data"]
            body = " ".join(d.get("body", "").split())
            if body in ("[deleted]", "[removed]"):
                continue
            lines.append(
                f"{'  ' * level}[{d.get('score', 0)}] {d.get('author', '?')}: {body}"
            )
            replies = d.get("replies")
            if isinstance(replies, dict):
                walk(replies["data"]["children"], level + 1)

    walk(listing[1]["data"]["children"], 0)
    return "\n".join(lines)


def page_text(ctx: BrowserContext, url: str) -> str:
    page = ctx.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)
    text = page.inner_text("body")
    page.close()
    return "\n".join(line for line in (ln.strip() for ln in text.splitlines()) if line)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("url")
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--max-chars", type=int, default=30000)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()
    with sync_playwright() as pw:
        ctx = pw.firefox.launch_persistent_context(
            PROFILE, headless=not args.login, user_agent=UA
        )
        if args.login:
            ctx.new_page().goto(args.url)
            input("Log in in the browser window, then press Enter here: ")
            ctx.close()
            return
        is_reddit = "reddit.com/r/" in args.url and "/comments/" in args.url
        out = (
            reddit_text(ctx, args.url, args.depth, args.limit)
            if is_reddit
            else page_text(ctx, args.url)
        )
        ctx.close()
    if len(out) > args.max_chars:
        out = (
            out[: args.max_chars]
            + f"\n[truncated at {args.max_chars} chars; raise --max-chars]"
        )
    print(out)


if __name__ == "__main__":
    main()
