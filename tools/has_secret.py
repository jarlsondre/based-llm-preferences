#!/usr/bin/env python3
"""Say whether a secret is configured, without ever showing its value.

Usage: has_secret NAME [NAME ...]

tools/machine.py links this file to ~/.local/bin/has_secret. It is the only way
an agent may check a secret. It prints one line per name, "NAME: set (where)"
or "NAME: missing", and exits 1 when any is missing. It looks in the
environment, in .env and .envrc from the current folder up to the home folder,
and in ~/.secrets*. There is no flag that prints a value.
"""

import os
import re
import sys
from pathlib import Path

NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


def secret_files() -> list[Path]:
    home = Path.home()
    folders = [Path.cwd(), *Path.cwd().parents]
    if home in folders:
        folders = folders[: folders.index(home) + 1]
    files = [folder / name for folder in folders for name in (".env", ".envrc")]
    files += sorted(home.glob(".secrets*"))
    return [file for file in files if file.is_file()]


def names_in(file: Path) -> set[str]:
    """The names a file gives a non-empty value. Values are read and dropped."""
    found = set()
    for line in file.read_text(errors="replace").splitlines():
        match = ASSIGNMENT.match(line)
        if match and match[2].strip().strip("'\""):
            found.add(match[1])
    return found


def main() -> None:
    names = sys.argv[1:]
    if not names or not all(NAME.fullmatch(name) for name in names):
        sys.exit("usage: has_secret NAME [NAME ...]")
    files = {file: names_in(file) for file in secret_files()}
    missing = False
    for name in names:
        places = ["the environment"] if os.environ.get(name) else []
        places += [
            str(file).replace(str(Path.home()), "~")
            for file, found in files.items()
            if name in found
        ]
        missing = missing or not places
        print(f"{name}: set ({', '.join(places)})" if places else f"{name}: missing")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
