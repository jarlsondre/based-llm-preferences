# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Keep the project's runbook.jsonl: one line per Slurm job; rules in SKILL.md.

Usage: uv run runbook.py add JOB_ID --command "..." --what "..." --why "..."
       uv run runbook.py close JOB_ID --outcome "..."
       uv run runbook.py --help

add appends an entry for a job that was just submitted, or, for a job id that
is already in the file, replaces the fields given and keeps the rest. It fills:
  cluster          from `scontrol show config` (--cluster overrides)
  submitted        now, ISO 8601 with timezone
  commit           `git rev-parse HEAD` in the project
  owner            "jarl" (--owner overrides; reporting.md rule 4)
  time_requested   the --time value in the command (--time-requested overrides)
  time_used        "TBD"
  outcome          "TBD"
what is at most 100 characters and why at most 500; longer is refused.

close fills time_used and the job's final state from `sacct -j JOB_ID`, and
outcome from --outcome. It refuses a job id that is not in the file.

Both take --runbook PATH; the default is runbook.jsonl in the git root of the
current folder, or in the current folder outside a git repo.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LIMITS = {"what": 100, "why": 500}
TIME_FLAG = re.compile(r"(?:^|\s)(?:--time[= ]|-t ?)(\S+)")


def run(args: list[str]) -> str:
    """The command's stdout, or an empty string when it is missing or fails."""
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return ""


def git_root() -> Path | None:
    out = run(["git", "rev-parse", "--show-toplevel"]).strip()
    return Path(out) if out else None


def cluster_name() -> str:
    match = re.search(r"ClusterName\s*=\s*(\S+)", run(["scontrol", "show", "config"]))
    return match[1] if match else "unknown"


def read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write(path: Path, entries: list[dict[str, str]]) -> None:
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries))


def add(args: argparse.Namespace, path: Path) -> None:
    for field, limit in LIMITS.items():
        value = getattr(args, field)
        if value is not None and len(value) > limit:
            sys.exit(
                f"runbook.py: {field} is {len(value)} characters; the limit is {limit}"
            )
    entries = read(path)
    old = next((e for e in entries if e["job_id"] == args.job_id), None)
    if old is None and not (args.command and args.what and args.why):
        sys.exit("runbook.py: a new entry needs --command, --what and --why")
    requested = args.time_requested
    if requested is None and args.command:
        match = TIME_FLAG.search(args.command)
        requested = match[1] if match else None
    if old is None and requested is None:
        sys.exit("runbook.py: no --time in the command; pass --time-requested")
    entry = old or {
        "job_id": args.job_id,
        "cluster": args.cluster or cluster_name(),
        "submitted": datetime.now().astimezone().isoformat(timespec="seconds"),
        "commit": run(["git", "rev-parse", "HEAD"]).strip() or "unknown",
        "command": "",
        "owner": "",
        "what": "",
        "why": "",
        "time_requested": "",
        "time_used": "TBD",
        "outcome": "TBD",
    }
    given = {
        "cluster": args.cluster,
        "command": args.command,
        "owner": args.owner if old is None else args.owner_given,
        "what": args.what,
        "why": args.why,
        "time_requested": requested if old is None or args.time_requested else None,
    }
    entry.update({k: v for k, v in given.items() if v is not None})
    if old is None:
        entries.append(entry)
    write(path, entries)
    print(("updated" if old else "added") + f" {args.job_id} in {path}")


def close(args: argparse.Namespace, path: Path) -> None:
    entries = read(path)
    entry = next((e for e in entries if e["job_id"] == args.job_id), None)
    if entry is None:
        sys.exit(f"runbook.py: {args.job_id} is not in {path}; add it first")
    out = run(["sacct", "-j", args.job_id, "-X", "-n", "-P", "--format=Elapsed,State"])
    line = out.strip().splitlines()[0] if out.strip() else ""
    if not line:
        sys.exit(
            f"runbook.py: sacct has no record of {args.job_id}; is the job finished?"
        )
    elapsed, state = line.split("|")[:2]
    entry["time_used"] = elapsed
    entry["outcome"] = f"{state.strip()}: {args.outcome}"
    write(path, entries)
    print(f"closed {args.job_id}: {entry['time_used']} used, {entry['outcome']}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--runbook", type=Path, help="default: runbook.jsonl in the git root"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add", help="record a submitted job")
    p_add.add_argument("job_id")
    p_add.add_argument("--command", help="the submit line, verbatim")
    p_add.add_argument("--what", help="what the job computes; max 100 characters")
    p_add.add_argument("--why", help="why the job is needed; max 500 characters")
    p_add.add_argument("--owner", default="jarl", help="who ran it; default jarl")
    p_add.add_argument(
        "--time-requested", help="walltime, when the command has no --time"
    )
    p_add.add_argument("--cluster", help="default: from scontrol")
    p_close = sub.add_parser("close", help="fill time_used and outcome from sacct")
    p_close.add_argument("job_id")
    p_close.add_argument("--outcome", required=True, help="one line on what came out")
    args = ap.parse_args()
    if args.cmd == "add":
        # An update keeps the old owner unless --owner was typed.
        args.owner_given = args.owner if "--owner" in sys.argv else None
    path = args.runbook or (git_root() or Path.cwd()) / "runbook.jsonl"
    add(args, path) if args.cmd == "add" else close(args, path)


if __name__ == "__main__":
    main()
