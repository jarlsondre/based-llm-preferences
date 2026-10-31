# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check guards 11 and 12 from hooks.md against simulated tool calls.

Usage: uv run tools/test_guards.py   # prints only the wrong verdicts; exit code 1 on any

The guard commands come from hooks.md itself, so the test checks what
machine.py installs. Guard 11 (shell edits) gets Bash commands that must be
denied or must pass. Guard 12 (blocked pages) gets WebSearch and WebFetch calls
before the call, and results and errors after it.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ in the repo from the import below
sys.path.insert(0, str(Path(__file__).parent))
from machine import wanted  # ty: ignore[unresolved-import]  # path set above

PREFIX = "# not using Edit because: renaming one flag in 40 files\n"

EDIT_DENY = [
    "sed -i 's/foo/bar/' main.md",
    "sed -i '' -e 's/a/b/' x.py",
    "sed -E -i.bak 's/a/b/' x.py",
    "cd src && sed --in-place 's/a/b/' x.py",
    "perl -pi -e 's/a/b/' x.tex",
    "perl -i.bak -pe 's/a/b/' x.tex",
    "echo 'export X=1' >> ~/.zshrc",
    "cat > notes.md <<'EOF'\nhello\nEOF",
    "printf '%s\\n' 'x' > out.txt",
    "ruff check . | tee lint.log",
    "ls | tee -a log.txt",
    (
        "python3 - <<'EOF'\nfrom pathlib import Path\np=Path('main.md')\n"
        "p.write_text(p.read_text().replace('a','b'))\nEOF"
    ),
    "python -c \"open('x.py','w').write('hi')\"",
    (
        "python3 -c \"import re,pathlib; f=pathlib.Path('a.md'); "
        "f.write_text(re.sub('a','b',f.read_text()))\""
    ),
    "node -e \"require('fs').writeFileSync('a.json', '{}')\"",
    'perl -e \'open(F, ">a.txt"); print F "x"\'',
    "uv run python - <<EOF\nimport shutil; shutil.copy('a','b')\nEOF",
    "awk '{print}' a.txt > b.txt",
    "find . -name '*.md' -exec sed -i 's/a/b/' {} +",
    "grep -rl old src | xargs sed -i 's/old/new/g'",
    "cat > a.md <<'EOF'\njarl's notes\nEOF",
    "python3 - <<'EOF'\n# jarl's file\nopen('a.md', 'w').write('x')\nEOF",
    "python3 -c \"open('a.md', mode='a').write('x')\"",
    # A reason line that is not the exact prefix does not count.
    "# not using Edit because:\nsed -i 's/a/b/' x.py",
    "# not using Edit because:   \nsed -i 's/a/b/' x.py",
    "echo x\n# not using Edit because: late\nsed -i 's/a/b/' x.py",
    "# not using edit because: lowercase\nsed -i 's/a/b/' x.py",
    "# Not using Edit because: capital\nsed -i 's/a/b/' x.py",
    "# NOT using edit because: caps\nsed -i 's/a/b/' x.py",
    "#  not  using  Edit  because:  spaces\nsed -i 's/a/b/' x.py",
    "#not using Edit because: no space\nsed -i 's/a/b/' x.py",
    "# not using the Edit tool because: extra words\nsed -i 's/a/b/' x.py",
    "# not using Edit because no colon\nsed -i 's/a/b/' x.py",
    "# Not using Write because: other tool\nsed -i 's/a/b/' x.py",
    "# I didn't use edit because: reworded\nsed -i 's/a/b/' x.py",
    "// not using Edit because: slashes\nsed -i 's/a/b/' x.py",
]

EDIT_PASS = [
    "sed -n 15,30p code-style.md",
    "sed 's/a/b/' x.py | head",
    "grep -rn 'write_text(' skills/",
    "grep -n 'sed -i' hooks.md",
    "python3 -c \"print(open('x').read())\"",
    "python3 - <<'EOF'\nimport json\nprint(json.load(open('a.json')))\nEOF",
    "uv run tools/machine.py",
    "uv run skills/python/scripts/rename.py old new",
    "git diff > /dev/null 2>&1; echo $?",
    "ls 2>&1 | head",
    "echo hi >&2",
    "make 2> /tmp/err.log",
    "cat a > /private/tmp/claude-501/x/scratchpad/edit-guard/out.txt",
    "cat a > $TMPDIR/out.txt",
    "awk '$3 > 100' data.tsv",
    "git log --oneline -3",
    "ls -la ~/programming/misc",
    "cat hooks.md",
    "echo 'x > y' ",
    "sort a.txt | uniq -c | sort -rn | head",
    "diff <(sort a) <(sort b)",
    "python3 -I - <<'EOF'\nfor l in open('t.jsonl'):\n    print(l)\nEOF",
    "cd x && uv run pytest -q",
    "tee /dev/null < a.txt",
    'grep -rn "sed -i" .',
    'echo "x > y"',
    "python3 -c \"print(open('w').read())\"",
    "python3 -c \"import sys; sys.stdout.write('x')\"",
    PREFIX + "sed -i 's/--old/--new/' $(grep -rl -- --old src)",
    (
        PREFIX + "python3 - <<'EOF'\nfrom pathlib import Path\n"
        "for p in Path('.').rglob('*.md'):\n"
        "    p.write_text(p.read_text().replace('a','b'))\nEOF"
    ),
    "  # not using Edit because: bulk transform jarl approved\necho x > a.md",
]

FETCH_DENY = [
    {"tool_name": "WebSearch", "tool_input": {"query": "reddit ASD-STE100 claude"}},
    {
        "tool_name": "WebSearch",
        "tool_input": {"query": "site:reddit.com slurm time limit"},
    },
    {
        "tool_name": "WebSearch",
        "tool_input": {
            "query": "best anki settings",
            "allowed_domains": ["reddit.com"],
        },
    },
    {
        "tool_name": "WebFetch",
        "tool_input": {
            "url": "https://www.reddit.com/r/ClaudeAI/comments/abc/x/",
            "prompt": "summarize",
        },
    },
    {
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://old.reddit.com/r/slurm", "prompt": "list"},
    },
]

FETCH_PASS = [
    {"tool_name": "WebSearch", "tool_input": {"query": "ASD-STE100 checker github"}},
    {
        "tool_name": "WebFetch",
        "tool_input": {
            "url": "https://github.com/TudorAndrei/ste-cli",
            "prompt": "summarize",
        },
    },
    {"tool_name": "WebSearch", "tool_input": {"query": "how to read it"}},
    # "reddit" in the prompt alone is not a Reddit target.
    {
        "tool_name": "WebFetch",
        "tool_input": {
            "url": "https://github.com/TudorAndrei/ste-cli",
            "prompt": "Summarize; note whether people on reddit liked it",
        },
    },
]

FETCH_NUDGE = [
    {
        "tool_name": "WebFetch",
        "tool_response": "The server returned HTTP 403 Forbidden.\n\nThe response body was not retrieved.",
    },
    {
        "tool_name": "WebSearch",
        "hook_event_name": "PostToolUseFailure",
        "error": "API Error: 400 The following domains are not accessible to our user agent: ['reddit.com']",
    },
    {
        "tool_name": "WebFetch",
        "tool_response": "Just a moment...\nEnable JavaScript and cookies to continue",
    },
    {
        "tool_name": "WebFetch",
        "tool_response": "Access Denied\nYou don't have permission to access this resource.",
    },
    {
        "tool_name": "WebFetch",
        "tool_response": "Please log in to continue reading this article.",
    },
    {
        "tool_name": "WebFetch",
        "hook_event_name": "PostToolUseFailure",
        "error": "Request failed with HTTP 401",
    },
]

FETCH_QUIET = [
    {
        "tool_name": "WebFetch",
        "tool_response": "ste-cli is a deterministic ASD-STE100 checker. The 20 checks are...",
    },
    {
        "tool_name": "WebSearch",
        "tool_response": "Web search results for query: ... blocked ... 404 Not Found",
    },
    # A block phrase deep in an article is not a block.
    {
        "tool_name": "WebFetch",
        "tool_response": "How bot detection works\n\n"
        + "Sites fingerprint the client, score the request and decide what to serve. "
        * 8
        + "A blocked client then sees 'access denied' or an HTTP 403 page.",
    },
    {
        "tool_name": "WebFetch",
        "hook_event_name": "PostToolUseFailure",
        "error": "Request timed out after 30s",
    },
]


def guards() -> dict[str, str]:
    """The three guard commands, by role, as hooks.md defines them."""
    hooks, _, names = wanted()
    out: dict[str, str] = {}
    for (event, _), entries in hooks.items():
        for hook in entries:
            section = names[hook["command"]]
            if section.startswith("11.") and event == "PreToolUse":
                out["edit"] = hook["command"]
            if section.startswith("12.") and event == "PreToolUse":
                out["fetch_pre"] = hook["command"]
            if section.startswith("12.") and event == "PostToolUse":
                out["fetch_post"] = hook["command"]
    missing = {"edit", "fetch_pre", "fetch_post"} - out.keys()
    if missing:
        sys.exit(f"test_guards.py: hooks.md lacks the guard commands {sorted(missing)}")
    return out


def run(hook: str, payload: dict) -> tuple[int, str, str]:
    r = subprocess.run(
        ["bash", "-c", hook],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def main() -> None:
    g = guards()
    wrong: list[str] = []

    def expect(ok: bool, verdict: str, case: str, got: str) -> None:
        if not ok:
            wrong.append(
                f"WRONG, expected {verdict}: {case[:90]!r}\n    got: {got[:160]!r}"
            )

    for cmd in EDIT_DENY:
        code, out, err = run(
            g["edit"], {"tool_name": "Bash", "tool_input": {"command": cmd}}
        )
        expect(code == 2 and "shell-edit guard" in err, "deny", cmd, err + out)
    for cmd in EDIT_PASS:
        code, out, err = run(
            g["edit"], {"tool_name": "Bash", "tool_input": {"command": cmd}}
        )
        expect(code == 0 and not out and not err, "pass", cmd, err + out)
    for p in FETCH_DENY:
        code, out, err = run(g["fetch_pre"], p)
        expect(
            code == 0 and '"deny"' in out and "fetch.py" in out,
            "deny",
            json.dumps(p["tool_input"]),
            err + out,
        )
    for p in FETCH_PASS:
        code, out, err = run(g["fetch_pre"], p)
        expect(
            code == 0 and not out and not err,
            "pass",
            json.dumps(p["tool_input"]),
            err + out,
        )
    for p in FETCH_NUDGE:
        code, out, err = run(g["fetch_post"], p)
        event = p.get("hook_event_name", "PostToolUse")
        ok = code == 0 and "fetch.py" in out
        if ok:
            ok = json.loads(out)["hookSpecificOutput"]["hookEventName"] == event
        expect(ok, "nudge", p.get("tool_response", p.get("error", "")), err + out)
    for p in FETCH_QUIET:
        code, out, err = run(g["fetch_post"], p)
        expect(
            code == 0 and not out and not err,
            "quiet",
            p.get("tool_response", p.get("error", "")),
            err + out,
        )

    total = sum(
        map(
            len,
            (EDIT_DENY, EDIT_PASS, FETCH_DENY, FETCH_PASS, FETCH_NUDGE, FETCH_QUIET),
        )
    )
    print("\n".join(wrong + [f"{total} calls, {len(wrong)} wrong"]))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
