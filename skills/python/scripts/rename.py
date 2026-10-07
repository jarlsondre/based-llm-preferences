# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Rename a symbol everywhere it is used, through ty's language server.

Usage: uv run rename.py FILE:LINE:COL NEW_NAME [--dry-run] [--force] [--root DIR]

LINE and COL are 1-based, as editors and the LSP tool show them, and point at
any occurrence of the symbol. --dry-run prints the edits and writes nothing.
--root names the project directory when it is not the nearest one holding
ty.toml, pyproject.toml or .git.

The edits come from the language server, so comments and same-named symbols of
other classes stay untouched. So do names inside quotes, such as __all__
entries and getattr strings: the tool lists where the old name is still quoted;
fix those by hand.

Two checks guard the rename. It refuses when the new name is already a name in
a file it would change. After writing, it runs ty on the changed files and puts
every file back if there are more errors than before; that catches a partial
rename, such as a symbol defined in a library. --force switches both checks
off; use it only after finding out why the tool refused.

No edit hook fires on the files it writes: run ruff and ty on the files it
prints.
"""

import argparse
import io
import json
import keyword
import os
import re
import subprocess
import sys
import threading
import tokenize
from itertools import pairwise
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

SERVERS = {".py": (["uvx", "ty", "server"], "python")}
SERVERS[".pyi"] = SERVERS[".py"]
ROOT_MARKERS = ("ty.toml", "pyproject.toml", ".git")
SKIPPED = ("node_modules", "__pycache__", "site-packages", "build", "dist")
TIMEOUT_SECONDS = 60
LINE_END = re.compile(r"\r\n|\n|\r")
NAME = re.compile(r"[^\W\d]\w*")


def fail(message: str) -> Any:  # typed Any so callers can use it in expressions
    sys.exit(f"rename.py: {message}")


class Server:
    """A language server on stdio, spoken to one request at a time."""

    def __init__(self, command: list[str]) -> None:
        self.proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.next_id = 0
        self.watchdog = threading.Timer(TIMEOUT_SECONDS, self.proc.kill)
        self.watchdog.start()

    def send(self, message: dict[str, Any]) -> None:
        body = json.dumps({"jsonrpc": "2.0"} | message).encode()
        assert self.proc.stdin is not None
        self.proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
        self.proc.stdin.flush()

    def read(self) -> dict[str, Any]:
        assert self.proc.stdout is not None
        length = 0
        while True:
            header = self.proc.stdout.readline()
            if not header:
                fail(f"the language server stopped or took over {TIMEOUT_SECONDS}s")
            if header.strip() == b"":
                break
            if header.lower().startswith(b"content-length:"):
                length = int(header.split(b":")[1])
        return json.loads(self.proc.stdout.read(length))

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.next_id += 1
        self.send({"id": self.next_id, "method": method, "params": params})
        while True:
            message = self.read()
            if "method" not in message and message.get("id") == self.next_id:
                return message
            if "method" in message and "id" in message:  # the server asks the client
                items = message.get("params", {}).get("items", [])
                asked_config = message["method"] == "workspace/configuration"
                result = [None] * len(items) if asked_config else None
                self.send({"id": message["id"], "result": result})

    def close(self) -> None:
        self.watchdog.cancel()
        self.proc.kill()


def find_root(path: Path) -> Path:
    for folder in path.parents:
        if any((folder / marker).exists() for marker in ROOT_MARKERS):
            return folder
    # A guessed root makes the server miss files, and the rename comes out partial.
    return fail(
        f"no project found above {path.name}: none of {', '.join(ROOT_MARKERS)}."
        " Pass --root DIR"
    )


def units(char: str, encoding: str) -> int:
    if encoding == "utf-16":
        return len(char.encode("utf-16-le")) // 2
    return len(char.encode()) if encoding == "utf-8" else 1


def to_server(line: str, index: int, encoding: str) -> int:
    """Convert a character index in the line to the server's units."""
    return sum(units(char, encoding) for char in line[:index])


def from_server(line: str, character: int, encoding: str) -> int:
    """Convert a server position in the line to a character index."""
    seen = 0
    for index, char in enumerate(line):
        if seen >= character:
            return index
        seen += units(char, encoding)
    return len(line)


def line_starts(text: str) -> list[int]:
    return [0, *(match.end() for match in LINE_END.finditer(text))]


def read(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as handle:  # keep line endings
        return handle.read()


def offset(
    text: str, starts: list[int], position: dict[str, int], encoding: str
) -> int:
    if position["line"] >= len(starts):
        return len(text)
    start = starts[position["line"]]
    end = (
        starts[position["line"] + 1]
        if position["line"] + 1 < len(starts)
        else len(text)
    )
    return start + from_server(text[start:end], position["character"], encoding)


def edits_by_file(result: dict[str, Any]) -> dict[Path, list[dict[str, Any]]]:
    found: dict[Path, list[dict[str, Any]]] = {}
    for uri, edits in (result.get("changes") or {}).items():
        found.setdefault(Path(unquote(urlparse(uri).path)), []).extend(edits)
    for change in result.get("documentChanges") or []:
        if "textDocument" not in change:
            fail(f"the server wants to {change.get('kind')} a file; not supported")
        path = Path(unquote(urlparse(change["textDocument"]["uri"]).path))
        found.setdefault(path, []).extend(change["edits"])
    return found


def rewrite(
    text: str, edits: list[dict[str, Any]], encoding: str
) -> tuple[str, list[int]]:
    """Apply the edits to one file's text; also return the lines they touch."""
    starts = line_starts(text)
    spans = sorted(
        (
            (
                offset(text, starts, edit["range"]["start"], encoding),
                offset(text, starts, edit["range"]["end"], encoding),
                edit["newText"],
                edit["range"]["start"]["line"] + 1,
            )
            for edit in edits
        ),
        reverse=True,
    )
    for (start, _, _, _), (_, earlier_end, _, _) in pairwise(spans):
        if earlier_end > start:
            fail("the server returned overlapping edits")
    for start, end, new_text, _ in spans:
        text = text[:start] + new_text + text[end:]
    return text, sorted({line for _, _, _, line in spans})


def ask(
    server: Server,
    root: Path,
    path: Path,
    line: int,
    col: int,
    new_name: str,
    language: str,
) -> tuple[dict[str, Any], str]:
    """Return the server's rename result and the position encoding it uses."""
    reply = server.request(
        "initialize",
        {
            "processId": None,
            "rootUri": root.as_uri(),
            "workspaceFolders": [{"uri": root.as_uri(), "name": root.name}],
            "capabilities": {
                "general": {"positionEncodings": ["utf-32", "utf-16"]},
                "workspace": {"workspaceEdit": {"documentChanges": True}},
                "textDocument": {"rename": {"prepareSupport": True}},
            },
        },
    )
    capabilities = reply["result"]["capabilities"]
    if not capabilities.get("renameProvider"):
        fail("this language server cannot rename")
    encoding = capabilities.get("positionEncoding", "utf-16")
    text = read(path)
    starts = line_starts(text)
    if line > len(starts):
        fail(f"{path.name} has no line {line}")
    end = starts[line] if line < len(starts) else len(text)
    line_text = text[starts[line - 1] : end]
    if col > len(line_text.rstrip("\r\n")) + 1:
        fail(f"line {line} of {path.name} has no column {col}")
    document = {"uri": path.as_uri()}
    position = {"line": line - 1, "character": to_server(line_text, col - 1, encoding)}
    server.send({"method": "initialized", "params": {}})
    opened = document | {"languageId": language, "version": 1, "text": text}
    server.send({"method": "textDocument/didOpen", "params": {"textDocument": opened}})
    reply = server.request(
        "textDocument/rename",
        {"textDocument": document, "position": position, "newName": new_name},
    )
    if "error" in reply:
        fail(f"the server refused: {reply['error'].get('message', reply['error'])}")
    return reply.get("result") or {}, encoding


def name_at(path: Path, line: int, col: int) -> str:
    """The name under a 1-based position, read from the file itself."""
    text = read(path)
    starts = line_starts(text)
    if line > len(starts):
        fail(f"{path.name} has no line {line}")
    end = starts[line] if line < len(starts) else len(text)
    for match in NAME.finditer(text[starts[line - 1] : end]):
        if match.start() <= col - 1 <= match.end():
            return match[0]
    return fail(f"nothing to rename at line {line}, column {col}; point at a name")


def mentions(texts: dict[Path, str], root: Path, pattern: str) -> list[str]:
    """Every FILE:LINE in texts whose line matches the pattern."""
    found = []
    for file, text in texts.items():
        for number, content in enumerate(LINE_END.split(text), start=1):
            if re.search(pattern, content):
                found.append(f"{file.relative_to(root)}:{number}")
    return found


def uses_of_name(texts: dict[Path, str], root: Path, name: str) -> list[str]:
    """Every FILE:LINE where the name stands as code, not inside a string or comment."""
    found = []
    for file, text in texts.items():
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
        except (tokenize.TokenError, SyntaxError):
            found += mentions({file: text}, root, rf"(?<!\w){re.escape(name)}(?!\w)")
            continue
        lines = {
            t.start[0] for t in tokens if t.type == tokenize.NAME and t.string == name
        }
        found += [f"{file.relative_to(root)}:{number}" for number in sorted(lines)]
    return found


def project_texts(root: Path) -> dict[Path, str]:
    texts = {}
    for folder, folders, names in os.walk(root):
        folders[:] = [f for f in folders if not f.startswith(".") and f not in SKIPPED]
        for name in sorted(names):
            if Path(name).suffix in SERVERS:
                texts[Path(folder) / name] = read(Path(folder) / name)
    return texts


def type_errors(root: Path, files: list[Path]) -> list[str]:
    command = ["uvx", "ty", "check", "--output-format", "concise", *map(str, files)]
    run = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    return [line for line in run.stdout.splitlines() if "error[" in line]


def write(texts: dict[Path, str]) -> None:
    for file, text in texts.items():
        with file.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("target", help="FILE:LINE:COL of any occurrence of the symbol")
    ap.add_argument("new_name")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--root", type=Path)
    args = ap.parse_args()

    parts = args.target.rsplit(":", 2)
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        fail("the target must be FILE:LINE:COL, with LINE and COL counted from 1")
    path, line, col = Path(parts[0]).resolve(), int(parts[1]), int(parts[2])
    if not path.is_file():
        fail(f"no such file: {parts[0]}")
    if path.suffix not in SERVERS:
        fail(f"no language server set up for {path.suffix or 'this'} files")
    if line < 1 or col < 1:
        fail("LINE and COL are counted from 1")
    if not args.new_name.isidentifier() or keyword.iskeyword(args.new_name):
        fail(f"{args.new_name!r} is not a valid name")
    root = (args.root or find_root(path)).resolve()
    if not path.is_relative_to(root):
        fail(f"{path} is not inside the project {root}")

    old_name = name_at(path, line, col)
    command, language = SERVERS[path.suffix]
    server = Server(command)
    try:
        result, encoding = ask(server, root, path, line, col, args.new_name, language)
    finally:
        server.close()

    files = edits_by_file(result)
    if not files:
        fail(f"the server returned no edits for {old_name} at {args.target}")
    outside = sorted(str(p) for p in files if not p.resolve().is_relative_to(root))
    if outside:
        fail("the rename reaches files outside the project:\n" + "\n".join(outside))

    before = {file: read(file) for file in sorted(files)}
    clashes = uses_of_name(before, root, args.new_name)
    if clashes and not args.force:
        fail(
            f"{args.new_name} is already a name in the files to change. Check these"
            " lines, then pass --force:\n" + "\n".join(clashes)
        )
    after, lines = {}, {}
    for file, edits in files.items():
        after[file], lines[file] = rewrite(before[file], edits, encoding)
    total = sum(len(edits) for edits in files.values())
    print(
        f"{'dry run, nothing written: ' if args.dry_run else ''}"
        f"{total} edits in {len(files)} files, {old_name} -> {args.new_name}"
    )
    for file in before:
        shown = ", ".join(str(n) for n in lines[file])
        print(f"{file.relative_to(root)}: lines {shown}")
    if not args.dry_run:
        errors_before = type_errors(root, list(before))
        write(after)
        new_errors = type_errors(root, list(before))
        if len(new_errors) > len(errors_before) and not args.force:
            write(before)
            fail(
                "the type checker reports new errors after the rename, so every file"
                " was put back. Pass --force to keep the rename:\n"
                + "\n".join(e for e in new_errors if e not in errors_before)
            )
    quoted = mentions(project_texts(root), root, rf"""["']{re.escape(old_name)}["']""")
    if quoted:
        print(f"{old_name} still stands inside quotes here, left as it was:")
        print("\n".join(quoted))


if __name__ == "__main__":
    main()
