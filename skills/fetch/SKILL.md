---
name: fetch
description:
  "Reads pages the built-in web tools cannot: Reddit threads and searches, bot
  blocks (403, Cloudflare), login walls. Use when a search or fetch is blocked,
  or when the target is on reddit.com."
compatibility: "Requires uv and a Playwright Firefox, one install per machine."
---

# Fetch

The script loads a page in a headless Firefox with a saved profile and prints it
as text. Guard 12 in hooks.md points here when a site blocks a built-in web
tool.

## When to use it

- Reddit, always: the built-in search and fetch cannot read reddit.com.
- A result that is a bot block or a login wall. The signs: HTTP 401 or 403,
  "Access denied", a Cloudflare "Just a moment" page, "log in to continue". The
  script gets past some of these, not all. If the site blocks the script too,
  report the page as unreachable and move on.

## Commands

<!-- prettier-ignore -->
```
uv run ${CLAUDE_SKILL_DIR}/scripts/fetch.py URL                                          # the page as text
uv run ${CLAUDE_SKILL_DIR}/scripts/fetch.py "https://www.reddit.com/search.json?q=TERMS"  # one line per thread
uv run ${CLAUDE_SKILL_DIR}/scripts/fetch.py THREAD_URL                                   # one line per comment
```

Reddit's search is weak: use distinctive terms, and `subreddit:name` in the
query to limit it. `--limit` caps threads or comments, `--depth` reply levels,
`--max-chars` the output (default 30000).

## Setup and limits

- Once per machine: `uv run --with playwright playwright install firefox`.
- A login wall needs jarl: `fetch.py --login URL` opens a window, jarl logs in,
  and the profile in `~/.local/share/jarl-fetch` keeps the login. Ask for it in
  For jarl; never enter credentials yourself.
- A page behind a cookie banner may print only the banner.
