# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build the card proposal jarl picks from; conventions in anki.md.

Usage: uv run tools/anki_proposal.py anki/proposals/NAME.json

Writes NAME.md and NAME.html beside the data file. The data file holds
{"name": NAME, "title": page name, "rows": [...]} with optional "subtitle",
"new_per_day" (new cards a day per subdeck, for the days estimate) and "groups"
({label: meaning}, in the order they should be picked). A row is
{"id": stable-slug, "subdeck": ..., "asks": one line, "cards": count} with
optional "group" (a label from groups), "exam" (the past exam or test question
behind it) and "material" ({source: [pages or locations]}).

In Claude Code, publish NAME.html with the Artifact tool, declaring the db
capability. jarl's choices are saved in the page's database: collection
"review", document NAME, holding the dropped ids, the notes per row, and a
general comment. Without Claude Code, jarl marks rows in NAME.md.
"""

import html
import json
import re
import sys
from pathlib import Path
from typing import Any

TEMPLATE = Path(__file__).with_suffix(".html")
REQUIRED = ("id", "subdeck", "asks", "cards")
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def validate(data: dict[str, Any], stem: str) -> list[str]:
    errors = []
    if data.get("name") != stem or not NAME.match(stem):
        errors.append(
            f'"name" must equal the file name ({stem}): lowercase letters, digits, -'
        )
    if not data.get("title"):
        errors.append('"title" is missing')
    groups = data.get("groups", {})
    seen: set[str] = set()
    for i, row in enumerate(data.get("rows", [])):
        where = row.get("id", f"row {i}")
        errors += [f"{where}: missing {key}" for key in REQUIRED if key not in row]
        if row.get("id") in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(row.get("id", ""))
        cards = row.get("cards")
        if "cards" in row and (not isinstance(cards, int) or cards < 1):
            errors.append(f"{where}: cards must be a whole number, 1 or more")
        if groups and row.get("group") not in groups:
            errors.append(f"{where}: group must be one of {', '.join(groups)}")
        if not groups and "group" in row:
            errors.append(f'{where}: has a group, but the file defines no "groups"')
    if not data.get("rows"):
        errors.append('"rows" is missing or empty')
    return errors


def material(row: dict[str, Any]) -> str:
    sources = row.get("material") or {}
    if isinstance(sources, str):
        return sources
    parts = []
    for source, places in sources.items():
        places = places if isinstance(places, list) else [places]
        if places:
            parts.append(f"{source} {', '.join(str(p) for p in places)}")
    return " · ".join(parts) or "NOT IN MATERIAL"


def cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def markdown(data: dict[str, Any]) -> str:
    rows = data["rows"]
    groups = data.get("groups", {})
    total = sum(row["cards"] for row in rows)
    intro = (
        f"{len(rows)} rows, {total} cards. Each row is what the card would ask."
        ' To drop a row, change its "yes" to "no".'
    )
    lines = [f"# {data['title']}", "", intro]
    if groups:
        lines += ["", *(f"- {label}: {meaning}" for label, meaning in groups.items())]
    for subdeck in dict.fromkeys(row["subdeck"] for row in rows):
        lines += ["", f"## {subdeck}"]
        for label in groups or [None]:
            chosen = [
                r for r in rows if r["subdeck"] == subdeck and r.get("group") == label
            ]
            if not chosen:
                continue
            if label:
                lines += ["", f"### {label}: {groups[label]}"]
            lines += [
                "",
                "| keep | id | the card asks | cards | past exam or test | in the material |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
            lines += [
                f"| yes | {cell(r['id'])} | {cell(r['asks'])} | {r['cards']} "
                f"| {cell(r.get('exam') or 'none')} | {cell(material(r))} |"
                for r in chosen
            ]
    return "\n".join(lines) + "\n"


def page(data: dict[str, Any]) -> str:
    # "<" escaped so card text cannot close the script tag holding the data.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    template = TEMPLATE.read_text()
    return template.replace("__TITLE__", html.escape(data["title"])).replace(
        "__DATA__", payload
    )


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: uv run tools/anki_proposal.py anki/proposals/NAME.json")
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    errors = validate(data, path.stem)
    if errors:
        sys.exit("anki_proposal.py: invalid proposal:\n" + "\n".join(errors))
    path.with_suffix(".md").write_text(markdown(data))
    path.with_suffix(".html").write_text(page(data))
    total = sum(row["cards"] for row in data["rows"])
    print(f"{len(data['rows'])} rows, {total} cards")
    print(f"wrote {path.with_suffix('.md')}")
    print(f"wrote {path.with_suffix('.html')}")
    print(
        "Claude Code: publish the .html with the Artifact tool, capabilities"
        f' {{"db": {{}}}}; read jarl\'s choices from collection "review",'
        f' document "{path.stem}".'
    )


if __name__ == "__main__":
    main()
