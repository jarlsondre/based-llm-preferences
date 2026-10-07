# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Set up Claude Code on this machine the way this repo describes.

Usage: uv run tools/machine.py           # bring this machine up to date
       uv run tools/machine.py --check   # only report; exit code 1 when out of date
       --claude-dir DIR                  # settings and skills folder; default ~/.claude
       --bin-dir DIR                     # where commands are linked; default ~/.local/bin

User settings: every JSON block in hooks.md that follows the line
"Merge into `~/.claude/settings.json`:" is merged into that file: missing hooks
are added, other keys are set to the block's value. An installed hook that
starts with the guards' jq check and is no longer in hooks.md is removed.
Everything else in the file stays as it is.

Skills: every folder in skills/ that holds a SKILL.md is linked into
~/.claude/skills/. A name that is already taken by something else is reported
and left alone.

Commands: tools/has_secret.py is linked to ~/.local/bin/has_secret, and the
tool reports when that folder is not on PATH.

Tools: it reports jq, uv and vale when they are not on PATH.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).parent.parent
SECTION = re.compile(r"^## (.+)$", re.MULTILINE)
BLOCK = re.compile(
    r"Merge into `~/\.claude/settings\.json`:\n\n```json\n(.*?)```", re.DOTALL
)
OURS = "command -v jq >/dev/null || { echo 'hook: jq missing"
NEEDED = {
    "jq": "every guard needs it; a static binary in ~/.local/bin works without sudo",
    "uv": "runs the tools and the lint guard",
    "vale": "language.md section 4 says how to install it",
}
Hook = dict[str, Any]


def wanted() -> tuple[
    dict[tuple[str, str], list[Hook]], dict[str, Any], dict[str, str]
]:
    """What hooks.md asks for: hooks by (event, matcher), plain keys, a name per guard."""
    hooks: dict[tuple[str, str], list[Hook]] = {}
    keys: dict[str, Any] = {}
    names: dict[str, str] = {}
    parts = SECTION.split((REPO / "hooks.md").read_text())
    for heading, body in zip(parts[1::2], parts[2::2], strict=True):
        for block in BLOCK.findall(body):
            for key, value in json.loads(block).items():
                if key != "hooks":
                    keys[key] = value
                    continue
                for event, groups in value.items():
                    for group in groups:
                        entries = hooks.setdefault(
                            (event, group.get("matcher", "")), []
                        )
                        for hook in group["hooks"]:
                            names[hook["command"]] = heading
                            if hook not in entries:
                                entries.append(hook)
    if not hooks:
        sys.exit(
            "machine.py: hooks.md has no JSON block after the line"
            ' "Merge into `~/.claude/settings.json`:"'
        )
    return hooks, keys, names


def merge_settings(settings: dict[str, Any]) -> list[str]:
    """Bring the settings up to date in place; return one line per change."""
    hooks, keys, names = wanted()
    changes = [
        f"settings: set {key}"
        for key, value in keys.items()
        if settings.get(key) != value
    ]
    settings.update(keys)
    current: dict[str, list[Hook]] = settings.setdefault("hooks", {})
    for event, groups in current.items():
        for group in groups:
            keep = hooks.get((event, group.get("matcher", "")), [])
            stale = [
                h
                for h in group["hooks"]
                if h.get("command", "").startswith(OURS) and h not in keep
            ]
            changes += [
                f"settings: remove an outdated guard from {event}" for _ in stale
            ]
            group["hooks"] = [h for h in group["hooks"] if h not in stale]
    for (event, matcher), entries in hooks.items():
        groups = current.setdefault(event, [])
        group: Hook | None = next(
            (g for g in groups if g.get("matcher", "") == matcher), None
        )
        if group is None:
            group = {"hooks": []}
            if matcher:
                group["matcher"] = matcher
            groups.append(group)
        installed: list[Hook] = list(group["hooks"])
        for hook in entries:
            if hook not in installed:
                installed.append(hook)
                changes.append(f"settings: add guard {names[hook['command']]}")
        group["hooks"] = installed
    settings["hooks"] = {e: [g for g in gs if g["hooks"]] for e, gs in current.items()}
    settings["hooks"] = {e: gs for e, gs in settings["hooks"].items() if gs}
    return changes


def link(source: Path, target: Path, label: str, write: bool) -> list[str]:
    """Symlink target -> source unless the name is taken by something else."""
    if target.is_symlink() and target.resolve() == source.resolve():
        return []
    if target.exists() or target.is_symlink():
        return [
            f"{label}: {target} exists and is not this repo's {source.name}; left alone"
        ]
    if write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source.resolve())
    return [f"{label}: link {target.name}"]


def link_skills(target: Path, write: bool) -> list[str]:
    skills = sorted(
        p for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file()
    )
    return [c for s in skills for c in link(s, target / s.name, "skills", write)]


def link_commands(bin_dir: Path, write: bool) -> list[str]:
    changes = link(
        REPO / "tools" / "has_secret.py", bin_dir / "has_secret", "commands", write
    )
    on_path = str(bin_dir.resolve()) in [
        str(Path(p).resolve())
        for p in os.environ.get("PATH", "").split(os.pathsep)
        if p
    ]
    if not on_path:
        changes.append(f"commands: {bin_dir} is not on PATH; add it in the shell rc")
    return changes


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--claude-dir", type=Path, default=Path.home() / ".claude")
    ap.add_argument("--bin-dir", type=Path, default=Path.home() / ".local" / "bin")
    args = ap.parse_args()
    settings_path = args.claude_dir / "settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    changes = merge_settings(settings)
    changes += link_skills(args.claude_dir / "skills", write=not args.check)
    changes += link_commands(args.bin_dir, write=not args.check)
    changes += [
        f"tools: {name} is not on PATH ({why})"
        for name, why in NEEDED.items()
        if not shutil.which(name)
    ]
    if not changes:
        print("this machine is up to date")
        return
    print("\n".join(changes))
    if args.check:
        sys.exit(
            "machine.py: out of date; run without --check, then fix what it still reports"
        )
    args.claude_dir.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    if any(change.startswith("tools:") for change in changes):
        sys.exit(
            "machine.py: settings and skills are set up; install the tools named above"
        )


if __name__ == "__main__":
    main()
