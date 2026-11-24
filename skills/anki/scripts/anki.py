# /// script
# requires-python = ">=3.11"
# dependencies = ["genanki==0.13.1", "pymupdf==2.1"]
#
# [tool.uv]
# exclude-newer = "2026-11-13T00:00:00Z"
# ///
"""Validate cards and build Anki decks; conventions in this skill's SKILL.md.

Usage: uv run anki.py anki/             # push via AnkiConnect (Anki open)
       uv run anki.py anki/ --check     # validate only
       uv run anki.py anki/ --approval  # write anki/approval.html
       uv run anki.py anki/ --apkg      # write anki/cards.apkg instead
       uv run anki.py --existing DECK   # list the cards already in a deck
       uv run anki.py --figures PDF     # list figure boxes; --page N for one page
       uv run anki.py anki/ --crop PDF PAGE X0,Y0,X1,Y1 NAME  # save a figure
       uv run anki.py --help            # print this text

The directory holds one JSON file per subdeck: {"deck": full deck name,
"cards": [...]}. Ids are unique across all files. A card is
{"id": stable-slug, "front": question, "back": answer},
{"id": stable-slug, "type": "cloze", "text": text with {{c1::...}} deletions},
or {"id": stable-slug, "type": "steps", "intro": claim or title, "steps": [...]}.
A steps card expands to one cloze note per step with ids id-1..id-n: earlier
steps shown, step k blanked, later steps as "hidden" placeholders. It needs at
least 2 steps and takes no cloze markup and no "adopt"; "intro" is optional. A
front that opens with is, are, does, can or a similar verb is rejected as a
yes/no question. All take optional "setting" (definitions the question needs)
and "extra" (footer for the curious).

"kind" is the sort of answer the card wants, in one or two words, shown at the
top right of the card. Every new card has one; the tool does not check this.
In math: "definition", "theorem", "proposition", "example", "notation",
"intuition". Elsewhere: "term", "property", "mechanism", "comparison",
"command".

Math is MathJax \\(...\\) or \\[...\\]; a bare $ outside code is rejected. Code
goes in backticks, inline or as a fenced block. It is escaped and shown
literally, so cloze markup and math inside code are not interpreted.

A figure is ![alt text](media/NAME.svg) in any text field, with the path
relative to the card files' folder; .svg, .png and .jpg work. A PNG or JPEG
shows at half its pixel width, sharp on phone screens. Every figure needs a
source in media/sources.json that names the work, never a file: "media/x.svg":
"Boyd and Vandenberghe, Convex Optimization, page 72, Figure 3.1". A web page
gets its title and URL. The card shows the source under the figure; --crop
writes it. A figure the agent made itself says so and names its basis, such as
"made by the agent: plot of f(x) = x^2 with matplotlib". A push stores each
figure in Anki under
its name plus a hash of its content, so a changed figure never overwrites
another.

--figures prints one line per figure or table in a PDF: page, vector or
raster, the box in points from the page's top left, and the nearest caption
below it. Parts with the same caption, such as the panels of one figure, merge
into one box. --crop saves that box of the page (pages count from 1) to
anki/media/NAME.svg, with the vector shapes and letters as outlines; anything
outside the box is removed first. It saves a PNG instead when the box holds a
raster image or --png is given. --source names the work the PDF holds, such as
"Vaswani et al., Attention Is All You Need (2017)"; --crop adds the page and the
caption's number. The page is the number printed on it when the PDF records
one, otherwise the count from 1. It sizes the figure so its labels show as large
as the card's small text, 16 pixels; --label-px N changes that. Labels are the
median letter size in the box, or on the page when the box holds no text. It
prints the figure syntax and the path of a preview image at the size the card
shows: look at the preview before using the figure.

A card whose entry moves to another file moves to that file's deck on the next
push.

--approval writes the page where jarl approves cards before a push: the cards
not pushed yet (--approval-all: every card), with a tick and a note per card.
--per-day N sets the days estimate (default 4). The page also shows these
optional fields, which a push ignores: "topic" (a heading inside the subdeck),
"where" (the place in the material), and together "asked" ("directly" or
"indirectly") with "exam" (the past exam or test question). A card with neither
counts as never asked.

--existing prints one line per note: Anki note id, card id or NOT IN FILES (a
note this tool did not make), note type, question => answer.

"adopt": Anki note id (the first column of --existing), on a card, converts
that existing note to the shared note type on the next push, keeping its
review history.

pushed.json in the directory records pushed ids: an id pushed before but now
missing from Anki was deleted by jarl in review, and a push never re-adds it.
--apkg ignores pushed.json and "adopt": its import brings back deleted cards
and duplicates an adopted card. Use it only when Anki cannot be reached.
"""

import argparse
import base64
import hashlib
import html
import json
import mimetypes
import re
import statistics
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

ANKI_URL = "http://localhost:8765"
PUSHED = "pushed.json"
BASIC_ID = 1758912001
CLOZE_ID = 1758912002
CSS = """.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 20px; line-height: 1.55; text-align: left;
  max-width: 720px; margin: 0 auto; padding: 24px 20px;
}
.setting {
  font-size: 16px; line-height: 1.5; opacity: .78; margin-top: 18px;
  padding: 8px 14px; border-left: 3px solid rgba(128,128,128,.55);
  background: rgba(128,128,128,.10); border-radius: 0 8px 8px 0;
}
.setting::before, .extra::before {
  display: block; font-size: 11px; font-weight: 600; letter-spacing: .10em;
  text-transform: uppercase; opacity: .75; margin-bottom: 2px;
}
.setting::before { content: "Setting"; }
.extra::before { content: "Extra"; }
.q { font-size: 21px; }
hr#answer { border: 0; border-top: 1px solid rgba(128,128,128,.45); margin: 20px 0 16px; }
.extra {
  font-size: 16px; line-height: 1.5; opacity: .72; margin-top: 18px;
  padding-left: 14px; border-left: 3px solid rgba(128,128,128,.45);
}
.id { font-size: 11px; opacity: .38; margin-top: 26px; letter-spacing: .06em; }
.cloze { font-weight: 600; color: #3b8eea; }
ul, ol { margin: 6px 0 0; padding-left: 26px; }
li { margin: 6px 0; }
li.hidden { opacity: .4; font-style: italic; }
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .88em; padding: 1px 5px; border-radius: 4px;
  background: rgba(128,128,128,.14);
}
pre {
  margin: 10px 0; padding: 10px 14px; overflow-x: auto; line-height: 1.4;
  border-radius: 8px; background: rgba(128,128,128,.12);
}
pre code { padding: 0; background: none; font-size: .85em; }
.kind {
  display: block; margin: -10px 0 4px; text-align: right; font-size: 12px;
  font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
  opacity: .8;
}
mjx-container[display="true"] { margin: 10px 0 !important; }
img {
  display: block; max-width: 100%; height: auto; margin: 10px 0;
  background: #fff; border-radius: 6px; cursor: zoom-in;
}
.source { font-size: 12px; opacity: .6; margin: -4px 0 12px; }
.zoom {
  position: fixed; inset: 0; z-index: 1000; cursor: zoom-out;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,.6);
}
.zoom img {
  width: min(90vw, 900px); max-width: none; max-height: 85vh; margin: 0;
  object-fit: contain; padding: 12px; box-sizing: border-box;
  border-radius: 10px; box-shadow: 0 8px 32px rgba(0,0,0,.4);
}
"""
# The guard keeps one listener: Anki reuses the page and reruns the script per card.
ZOOM = """<script>
if (!window.figureZoom) {
  window.figureZoom = true;
  document.addEventListener("click", function (event) {
    var open = document.querySelector(".zoom");
    if (open) { open.remove(); return; }
    if (event.target.tagName !== "IMG") return;
    var overlay = document.createElement("div");
    overlay.className = "zoom";
    overlay.appendChild(event.target.cloneNode());
    event.target.parentNode.appendChild(overlay);
  });
}
</script>"""
SETTING = '{{#Setting}}<div class="setting">{{Setting}}</div>{{/Setting}}' + ZOOM
FOOTER = (
    '{{#Extra}}<div class="extra">{{Extra}}</div>{{/Extra}}<div class="id">{{Id}}</div>'
)
BASIC_FRONT = '<div class="q">{{Front}}</div>' + SETTING
BASIC_BACK = '{{FrontSide}}<hr id="answer">{{Back}}' + FOOTER
CLOZE_FRONT = "{{cloze:Text}}" + SETTING
CLOZE_BACK = CLOZE_FRONT + FOOTER
FIELDS = {
    "jarl-basic": ["Id", "Setting", "Front", "Back", "Extra"],
    "jarl-cloze": ["Id", "Setting", "Text", "Extra"],
}
TEMPLATES = {
    "jarl-basic": [{"Name": "Card 1", "Front": BASIC_FRONT, "Back": BASIC_BACK}],
    "jarl-cloze": [{"Name": "Cloze", "Front": CLOZE_FRONT, "Back": CLOZE_BACK}],
}
REQUIRED = {"basic": {"id", "front", "back"}, "cloze": {"id", "text"}}
CONTENT = ("setting", "intro", "front", "back", "text", "extra")
YES_NO = re.compile(
    r"^(is|are|was|were|do|does|did|can|could|will|would|should|has|have)\b",
    re.IGNORECASE,
)
BARE_DOLLAR = re.compile(r"(?<!\\)\$")
MARKUP = re.compile(
    r"```[\w-]*\n?(?P<fenced>.*?)```|`(?P<inline>[^`\n]+)`"
    r"|!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)\)",
    re.DOTALL,
)
FIGURE_TYPES = {".svg", ".png", ".jpg", ".jpeg"}
IMG_SRC = re.compile(r'<img src="([^"]+)"')
SOURCES = "sources.json"
CAPTION = re.compile(r"^(Figure|Fig\.|Table)\s*\d+[.:]", re.IGNORECASE)
LABEL_WORDS = 8  # a text line this short next to a figure is one of its labels
LABEL_PX = 16  # as large as the card's Setting and Extra text
PIXEL_DENSITY = 2  # a PNG figure has two pixels per screen pixel, sharp on phones
TAGS = re.compile(r"<[^>]+>")
CLOZE = re.compile(r"\{\{c\d+::(.*?)(?:::[^}]*)?\}\}", re.DOTALL)
CLOZE_NUMBER = re.compile(r"\{\{c(\d+)::")
APPROVAL_PAGE = Path(__file__).parent.parent / "assets" / "approval.html"
PAGE_KEYS = (
    "id",
    "type",
    "setting",
    "intro",
    "steps",
    "front",
    "back",
    "extra",
    "topic",
    "kind",
    "where",
    "asked",
    "exam",
)


def check_evidence(cards: list[dict[str, Any]]) -> list[str]:
    errors = []
    for card in cards:
        asked = card.get("asked")
        if asked is not None and asked not in ("directly", "indirectly"):
            errors.append(f'{label(card)}: asked must be "directly" or "indirectly"')
        if (asked is None) != ("exam" not in card):
            errors.append(f"{label(card)}: asked and exam go together")
    return errors


def escape_code(code: str) -> str:
    """Make code literal: no HTML, cloze markup, math, or backticks survive."""
    text = html.escape(code, quote=False)
    for char in "{}$`\\":
        text = text.replace(char, f"&#{ord(char)};")
    return text


def figure_name(path: Path) -> str:
    """The figure's name in Anki's media folder: its stem plus a content hash."""
    stem = re.sub(r"[^\w.-]", "-", path.stem)
    return f"{stem}-{hashlib.sha256(path.read_bytes()).hexdigest()[:8]}{path.suffix.lower()}"


def shown_width(path: Path) -> int:
    """The width in screen pixels of a PNG or JPEG figure on the card."""
    import pymupdf  # type: ignore  # uv script dep

    return pymupdf.Pixmap(str(path)).width // PIXEL_DENSITY


def read_sources(cards_dir: Path) -> dict[str, str]:
    path = cards_dir / "media" / SOURCES
    return json.loads(path.read_text()) if path.exists() else {}


def render(
    text: str,
    cards_dir: Path,
    figures: dict[str, Path],
    errors: list[str],
    where: str,
    sources: dict[str, str],
) -> str:
    """Turn code into literal HTML and figure syntax into img tags with sources."""

    def replace(m: re.Match[str]) -> str:
        if m["fenced"] is not None:
            return f"<pre><code>{escape_code(m['fenced'].strip(chr(10)))}</code></pre>"
        if m["inline"] is not None:
            return f"<code>{escape_code(m['inline'])}</code>"
        path = (cards_dir / m["src"]).resolve()
        if not path.is_relative_to(cards_dir.resolve()) or not path.is_file():
            errors.append(f"{where}: no figure {m['src']} inside {cards_dir}")
            return m[0]
        if path.suffix.lower() not in FIGURE_TYPES:
            errors.append(
                f"{where}: {m['src']}: figures are {', '.join(sorted(FIGURE_TYPES))}"
            )
            return m[0]
        key = path.relative_to(cards_dir.resolve()).as_posix()
        if key not in sources:
            errors.append(
                f'{where}: {key} has no source; add "{key}": "<work>, page <n>,'
                f' Figure <n>" to media/{SOURCES}'
            )
            return m[0]
        name = figure_name(path)
        figures[name] = path
        alt = html.escape(m["alt"])
        width = "" if path.suffix.lower() == ".svg" else f' width="{shown_width(path)}"'
        source = html.escape(sources[key])
        return (
            f'<div class="figure"><img src="{name}" alt="{alt}"{width}>'
            f'<div class="source">Source: {source}</div></div>'
        )

    return MARKUP.sub(replace, text)


def load(cards_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    files = sorted(p for p in cards_dir.glob("*.json") if p.name != PUSHED)
    if not files:
        sys.exit(f"anki.py: no card files (*.json) in {cards_dir}")
    cards, errors = [], []
    sources = read_sources(cards_dir)
    for path in files:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            sys.exit(f"anki.py: {path.name}: invalid JSON ({e})")
        if not isinstance(data, dict) or "deck" not in data or "cards" not in data:
            sys.exit(f'anki.py: {path.name}: needs a "deck" and a "cards" key')
        for raw in data["cards"]:
            card = dict(raw) | {"deck": data["deck"], "file": path.name}
            figures: dict[str, Path] = {}
            where = label(card)
            for key in CONTENT:
                if isinstance(card.get(key), str):
                    card[key] = render(
                        card[key], cards_dir, figures, errors, where, sources
                    )
            if isinstance(card.get("steps"), list):
                card["steps"] = [
                    render(str(step), cards_dir, figures, errors, where, sources)
                    for step in card["steps"]
                ]
            card["figures"] = figures
            cards.append(card)
    return cards, errors


def label(card: dict[str, Any]) -> str:
    return f"{card['file']}: {card.get('id', '<no id>')}"


def expand_steps(
    cards: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Expand each steps card into one cloze note per step."""
    out: list[dict[str, Any]] = []
    errors = []
    for card in cards:
        if card.get("type") != "steps":
            out.append(card)
            continue
        steps = card.get("steps")
        if "id" not in card or not isinstance(steps, list) or len(steps) < 2:
            errors.append(f"{label(card)}: steps card needs an id and at least 2 steps")
            continue
        if "adopt" in card:
            errors.append(f"{label(card)}: a steps card cannot adopt an existing card")
            continue
        if any("{{c" in step for step in steps):
            errors.append(
                f"{label(card)}: steps must not contain cloze markup; the tool adds it"
            )
            continue
        for k in range(len(steps)):
            items = [f"<li>{s}</li>" for s in steps[:k]]
            items.append(f"<li>{{{{c1::{steps[k]}}}}}</li>")
            items += ['<li class="hidden">hidden</li>'] * (len(steps) - k - 1)
            out.append(
                {
                    "id": f"{card['id']}-{k + 1}",
                    "type": "cloze",
                    "text": card.get("intro", "") + "<ol>" + "".join(items) + "</ol>",
                    "setting": card.get("setting", ""),
                    "extra": card.get("extra", ""),
                    "kind": card.get("kind", ""),
                    "deck": card["deck"],
                    "file": card["file"],
                    "figures": card["figures"],
                }
            )
    return out, errors


def validate(cards: list[dict[str, Any]]) -> list[str]:
    errors = []
    seen: dict[str, str] = {}
    for card in cards:
        kind = card.get("type", "basic")
        if kind not in REQUIRED:
            errors.append(
                f"{label(card)}: unknown type {kind}; omit it, or use cloze or steps"
            )
            continue
        for field in sorted(REQUIRED[kind] - card.keys()):
            errors.append(f"{label(card)}: missing field {field}")
        cid = card.get("id")
        if cid in seen:
            errors.append(f"{label(card)}: duplicate id, also in {seen[cid]}")
        elif cid:
            seen[cid] = card["file"]
        if kind == "cloze" and "{{c" not in card.get("text", ""):
            errors.append(
                f"{label(card)}: cloze card without a {{{{c1::...}}}} deletion"
            )
        if kind == "basic" and YES_NO.match(card.get("front", "")):
            errors.append(
                f"{label(card)}: yes/no question; rephrase open-ended (SKILL.md)"
            )
        if not isinstance(card.get("kind", ""), str):
            errors.append(f'{label(card)}: kind must be text, such as "definition"')
        if "adopt" in card and not isinstance(card["adopt"], int):
            errors.append(f"{label(card)}: adopt must be the Anki note id, a number")
        if any(BARE_DOLLAR.search(str(card.get(key, ""))) for key in CONTENT):
            errors.append(
                rf"{label(card)}: bare $ outside code; math is MathJax \(...\),"
                " code goes in backticks (SKILL.md)"
            )
    return errors


def model_for(card: dict[str, Any]) -> str:
    return "jarl-cloze" if card.get("type") == "cloze" else "jarl-basic"


def fields_for(card: dict[str, Any]) -> dict[str, str]:
    common = {
        "Id": card["id"],
        "Setting": card.get("setting", ""),
        "Extra": card.get("extra", ""),
    }
    kind = card.get("kind", "").strip()
    shown = f'<div class="kind">{html.escape(kind)}</div>' if kind else ""
    if card.get("type") == "cloze":
        return common | {"Text": shown + card["text"]}
    return common | {"Front": shown + card["front"], "Back": card["back"]}


def invoke(action: str, **params: object) -> Any:  # AnkiConnect returns arbitrary JSON
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    try:
        with urllib.request.urlopen(
            urllib.request.Request(ANKI_URL, payload), timeout=15
        ) as resp:
            data = json.load(resp)
    except OSError as err:
        sys.exit(f"anki.py: AnkiConnect unreachable ({err}); open Anki, or use --apkg")
    if data.get("error"):
        sys.exit(f"anki.py: {action}: {data['error']}")
    return data["result"]


def sync_note_type(name: str) -> None:
    """Create the note type, or bring an existing one up to the shared style."""
    if name not in invoke("modelNames"):
        invoke(
            "createModel",
            modelName=name,
            inOrderFields=FIELDS[name],
            css=CSS,
            isCloze=name == "jarl-cloze",
            cardTemplates=TEMPLATES[name],
        )
        return
    have = invoke("modelFieldNames", modelName=name)
    for index, field in enumerate(FIELDS[name]):
        if field not in have:
            invoke("modelFieldAdd", modelName=name, fieldName=field, index=index)
    invoke("updateModelStyling", model={"name": name, "css": CSS})
    templates = {
        t["Name"]: {"Front": t["Front"], "Back": t["Back"]} for t in TEMPLATES[name]
    }
    invoke("updateModelTemplates", model={"name": name, "templates": templates})


def move_to_decks(targets: dict[str, list[int]]) -> int:
    """Move the cards of existing notes into the deck their file names."""
    moved = 0
    for deck, note_ids in targets.items():
        query = "nid:" + ",".join(str(note_id) for note_id in note_ids)
        current = invoke("getDecks", cards=invoke("findCards", query=query))
        misplaced = [c for name, ids in current.items() if name != deck for c in ids]
        if misplaced:
            invoke("changeDeck", cards=misplaced, deck=deck)
            moved += len(misplaced)
    return moved


def adopt(card: dict[str, Any]) -> None:
    """Convert a card made outside the files to the shared note type, in place."""
    info = invoke("notesInfo", notes=[card["adopt"]])
    if not info or not info[0].get("noteId"):
        sys.exit(f"anki.py: {label(card)}: no Anki note {card['adopt']} to adopt")
    invoke(
        "updateNoteModel",
        note={
            "id": card["adopt"],
            "modelName": model_for(card),
            "fields": fields_for(card),
            "tags": info[0].get("tags", []),
        },
    )


def read_pushed(pushed_path: Path) -> set[str]:
    return set(json.loads(pushed_path.read_text())) if pushed_path.exists() else set()


def all_figures(cards: list[dict[str, Any]]) -> dict[str, Path]:
    return {name: path for card in cards for name, path in card["figures"].items()}


def store_figures(cards: list[dict[str, Any]]) -> int:
    """Copy the figures Anki does not have yet into its media folder."""
    figures = all_figures(cards)
    if not figures:
        return 0
    have = set(invoke("getMediaFilesNames", pattern="*"))
    missing = sorted(figures.keys() - have)
    for name in missing:
        data = base64.b64encode(figures[name].read_bytes()).decode()
        invoke("storeMediaFile", filename=name, data=data)
    return len(missing)


def push(cards: list[dict[str, Any]], pushed_path: Path) -> None:
    pushed = read_pushed(pushed_path)
    decks = sorted({card["deck"] for card in cards})
    for deck in decks:
        invoke("createDeck", deck=deck)
    stored = store_figures(cards)
    for name in FIELDS:
        sync_note_type(name)
    added, updated, skipped, adopted = [], [], [], []
    existing: dict[str, list[int]] = {}
    for card in cards:
        cid = card["id"]
        note_ids = invoke("findNotes", query=f'"Id:{cid}"')
        if note_ids:
            invoke(
                "updateNoteFields", note={"id": note_ids[0], "fields": fields_for(card)}
            )
            updated.append(cid)
            existing.setdefault(card["deck"], []).append(note_ids[0])
        elif cid in pushed:
            skipped.append(cid)
        elif "adopt" in card:
            adopt(card)
            adopted.append(cid)
            existing.setdefault(card["deck"], []).append(card["adopt"])
        else:
            invoke(
                "addNote",
                note={
                    "deckName": card["deck"],
                    "modelName": model_for(card),
                    "fields": fields_for(card),
                },
            )
            added.append(cid)
    moved = move_to_decks(existing)
    pushed |= set(added) | set(updated) | set(adopted)
    pushed_path.write_text(json.dumps(sorted(pushed)) + "\n")
    print(
        f"{len(decks)} decks: added {len(added)}, updated {len(updated)}, "
        f"converted {len(adopted)}, moved {moved}, stored {stored} figures"
    )
    if adopted:
        print("converted cards changed note type: Anki asks for a one-way sync once")
    if skipped:
        print(
            "deleted in review, not re-added; remove from the card files: "
            + ", ".join(skipped)
        )


def write_apkg(cards: list[dict[str, Any]], out: Path) -> None:
    import genanki  # type: ignore  # uv script dep

    models = {
        "jarl-basic": genanki.Model(
            BASIC_ID,
            "jarl-basic",
            fields=[{"name": n} for n in FIELDS["jarl-basic"]],
            templates=[{"name": "Card 1", "qfmt": BASIC_FRONT, "afmt": BASIC_BACK}],
            css=CSS,
        ),
        "jarl-cloze": genanki.Model(
            CLOZE_ID,
            "jarl-cloze",
            fields=[{"name": n} for n in FIELDS["jarl-cloze"]],
            templates=[{"name": "Cloze", "qfmt": CLOZE_FRONT, "afmt": CLOZE_BACK}],
            css=CSS,
            model_type=genanki.Model.CLOZE,
        ),
    }
    decks: dict[str, Any] = {}
    for card in cards:
        name = card["deck"]
        if name not in decks:
            deck_id = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)
            decks[name] = genanki.Deck(deck_id, name)
        fields = fields_for(card)
        model = model_for(card)
        note = genanki.Note(
            model=models[model],
            fields=[fields[n] for n in FIELDS[model]],
            guid=genanki.guid_for(card["id"]),
        )
        decks[name].add_note(note)
    figures = all_figures(cards)
    with tempfile.TemporaryDirectory() as staging:
        # genanki names each media file after its path, so copies carry the Anki names.
        media = []
        for name, path in figures.items():
            copy = Path(staging) / name
            copy.write_bytes(path.read_bytes())
            media.append(str(copy))
        package = genanki.Package(list(decks.values()), media_files=media)
        package.write_to_file(str(out))
    print(f"wrote {out} ({len(decks)} decks, {len(cards)} cards, {len(media)} figures)")


def plain(value: str, limit: int) -> str:
    text = " ".join(html.unescape(TAGS.sub(" ", value)).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def list_existing(deck: str) -> None:
    """Print the cards already in a deck, so new cards do not repeat them."""
    note_ids = invoke("findNotes", query=f'"deck:{deck}"')
    notes = invoke("notesInfo", notes=note_ids) if note_ids else []
    outside = 0
    for note in notes:
        ordered = sorted(note["fields"].items(), key=lambda item: item[1]["order"])
        values = {name: field["value"] for name, field in ordered}
        managed = note["modelName"] in FIELDS and values.get("Id")
        outside += not managed
        skipped = ("Id", "Setting", "Extra") if managed else ()
        shown = [v for name, v in values.items() if name not in skipped and v.strip()]
        question = plain(shown[0], 140) if shown else ""
        answer = plain(shown[1], 100) if len(shown) > 1 else ""
        print(
            f"{note['noteId']}  {managed or 'NOT IN FILES'}  [{note['modelName']}]"
            f"  {question}  =>  {answer}"
        )
    print(f"{deck}: {len(notes)} cards, {outside} not in the card files")


def page_title(cards: list[dict[str, Any]]) -> tuple[str, str]:
    """Name the page after the part of the deck path all cards share."""
    paths = [card["deck"].split("::") for card in cards]
    shared = []
    for level in zip(*paths, strict=False):
        if len(set(level)) > 1:
            break
        shared.append(level[0])
    one_deck = len(shared) == len(paths[0]) and len(shared) > 1
    name = shared[-2] if one_deck else shared[-1] if shared else "Anki"
    return f"{name} Card Approval", " / ".join(shared)


def embed_figures(text: str, figures: dict[str, Path]) -> str:
    """Put each figure into the text itself, so the page needs no other files."""

    def data_uri(m: re.Match[str]) -> str:
        path = figures[m[1]]
        kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode()
        return f'<img src="data:{kind};base64,{encoded}"'

    return IMG_SRC.sub(data_uri, text)


def text_lines(page: Any) -> list[tuple[Any, str]]:
    import pymupdf  # type: ignore  # uv script dep

    return [
        (pymupdf.Rect(line["bbox"]), "".join(s["text"] for s in line["spans"]))
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
    ]


def caption_label(page: Any, box: Any) -> str:
    """The figure or table number of the caption right below the box, if any."""
    below = [
        (rect, found[0].rstrip(".:"))
        for rect, text in text_lines(page)
        if (found := CAPTION.match(text))
        and rect.y0 >= box.y1 - 5
        and rect.x1 > box.x0
        and rect.x0 < box.x1
    ]
    nearest = min(below, key=lambda c: c[0].y0, default=None)
    return nearest[1] if nearest else ""


def figure_boxes(pdf: Path, only_page: int | None) -> None:
    """Print each figure: page, vector or raster, box, caption.

    Parts with the same caption below them merge into one figure.
    """
    import pymupdf  # type: ignore  # uv script dep

    doc = pymupdf.open(pdf)
    pages = [doc[only_page - 1]] if only_page else list(doc)
    for page in pages:
        lines = text_lines(page)
        captions = [(rect, text) for rect, text in lines if CAPTION.match(text)]
        labels = [
            rect
            for rect, text in lines
            if len(text.split()) <= LABEL_WORDS and not CAPTION.match(text)
        ]
        found = [("vector", rect) for rect in page.cluster_drawings()]
        found += [
            ("raster", pymupdf.Rect(info["bbox"])) for info in page.get_image_info()
        ]
        figures: list[tuple[str, Any, str]] = []
        for kind, box in found:
            grown = True
            while grown:
                near = [r for r in labels if r.intersects(box + (-8, -8, 8, 8))]
                grown = any(not box.contains(r) for r in near)
                for rect in near:
                    box |= rect
            if box.width < 30 or box.height < 30:
                continue
            below = [c for c in captions if c[0].y0 >= box.y1 - 5]
            caption = min(below, key=lambda c: c[0].y0 - box.y1, default=None)
            text = caption[1] if caption else ""
            same = next(
                (i for i, f in enumerate(figures) if text and f[2] == text), None
            )
            if same is None:
                figures.append((kind, box, text))
            else:
                old_kind, old_box, _ = figures[same]
                merged_kind = "raster" if "raster" in (kind, old_kind) else "vector"
                figures[same] = (merged_kind, old_box | box, text)
        for kind, box, text in figures:
            corners = ",".join(str(round(v)) for v in box + (-4, -4, 4, 4))
            print(f"page {page.number + 1}  {kind}  {corners}  {text}")


def text_size(page: Any, box: Any) -> float:
    """The median letter size in the box; with no text there, on the whole page."""
    for clip in (box, None):
        sizes = [
            span["size"]
            for block in page.get_text("dict", clip=clip)["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
            if span["text"].strip()
        ]
        if sizes:
            return statistics.median(sizes)
    return 10.0


def crop_figure(
    pdf: Path,
    page_number: int,
    corners: str,
    out: Path,
    work: str,
    force_png: bool,
    label_px: int,
) -> None:
    """Save one box of a PDF page as a figure, with everything outside it removed."""
    import pymupdf  # type: ignore  # uv script dep

    page = pymupdf.open(pdf)[page_number - 1]
    box = pymupdf.Rect([float(v) for v in corners.split(",")])
    scale = label_px / text_size(page, box)
    label = caption_label(page, box)
    printed_page = page.get_label() or str(page_number)
    source = f"{work}, page {printed_page}" + (f", {label}" if label else "")
    whole = page.rect
    outside = [
        pymupdf.Rect(whole.x0, whole.y0, whole.x1, box.y0),
        pymupdf.Rect(whole.x0, box.y1, whole.x1, whole.y1),
        pymupdf.Rect(whole.x0, box.y0, box.x0, box.y1),
        pymupdf.Rect(box.x1, box.y0, whole.x1, box.y1),
    ]
    raster = any(
        pymupdf.Rect(info["bbox"]).intersects(box) for info in page.get_image_info()
    )
    for rect in outside:
        if not rect.is_empty:
            page.add_redact_annot(rect, fill=False)
    page.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_PIXELS,
        graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
    )
    page.set_cropbox(box)
    out.parent.mkdir(parents=True, exist_ok=True)
    preview = Path(tempfile.gettempdir()) / f"{out.stem}-preview.png"
    if raster or force_png:
        target = out.with_suffix(".png")
        zoom = scale * PIXEL_DENSITY
        page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(target)
        page.get_pixmap(matrix=pymupdf.Matrix(scale, scale)).save(preview)
    else:
        target = out.with_suffix(".svg")
        svg = page.get_svg_image(text_as_path=True)
        width, height = round(box.width * scale), round(box.height * scale)
        sized = f'width="{width}" height="{height}"'
        svg = re.sub(r'width="[^"]*" height="[^"]*"', sized, svg, count=1)
        target.write_text(svg)
        pymupdf.open(target)[0].get_pixmap(dpi=72).save(preview)
    kind = "raster image in the box" if raster else "chosen" if force_png else "vector"
    shown = f"{round(box.width * scale)}x{round(box.height * scale)}"
    print(
        f"wrote {target} ({target.stat().st_size // 1000} KB, {kind}, shown {shown}px)"
    )
    key = f"{target.parent.name}/{target.name}"
    sources_path = out.parent / SOURCES
    sources = json.loads(sources_path.read_text()) if sources_path.exists() else {}
    sources[key] = source
    sources_path.write_text(json.dumps(sources, indent=2, sort_keys=True) + "\n")
    print(f"source in {sources_path}: {source}")
    print(f"in a card: ![describe it]({key})")
    print(f"look at the preview, at the size the card shows it: {preview}")


def write_approval(
    cards: list[dict[str, Any]], pushed: set[str], out: Path, per_day: int, full: bool
) -> None:
    """Write the approval page."""
    rows = []
    for card in cards:
        steps = card["steps"] if card.get("type") == "steps" else []
        ids = [f"{card['id']}-{k + 1}" for k in range(len(steps))] or [card["id"]]
        if not full and all(cid in pushed for cid in ids):
            continue
        row = {key: card[key] for key in PAGE_KEYS if key in card}
        if card.get("type") == "cloze":
            row["text"] = CLOZE.sub(r'<span class="cloze">\1</span>', card["text"])
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = embed_figures(value, card["figures"])
            elif key == "steps":
                row[key] = [embed_figures(step, card["figures"]) for step in value]
        # Anki makes one card per distinct cloze number, so c1, c1, c2 is two cards.
        numbers = set(CLOZE_NUMBER.findall(card.get("text", "")))
        row |= {
            "subdeck": card["deck"].split("::")[-1],
            "inAnki": "adopt" in card,
            "cards": len(numbers) if card.get("type") == "cloze" else len(ids),
        }
        rows.append(row)
    if not rows:
        sys.exit(
            "anki.py: nothing to approve, every card was pushed before; use --approval-all"
        )
    title, subtitle = page_title(cards)
    data = {"subtitle": subtitle, "per_day": per_day, "rows": rows}
    # "<" escaped so card text cannot close the script tag holding the data.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    page = APPROVAL_PAGE.read_text().replace("__TITLE__", html.escape(title))
    out.write_text(page.replace("__DATA__", payload))
    print(f"wrote {out}: {len(rows)} entries, {sum(r['cards'] for r in rows)} cards")
    print(
        'Claude Code: publish it with the Artifact tool, capabilities {"db": {}}; read'
        ' jarl\'s choices from collection "approval", document "cards": "notes" maps'
        ' card id to note, "dropped" maps card id to true or false.'
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("cards_dir", type=Path, nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apkg", action="store_true")
    ap.add_argument("--approval", action="store_true")
    ap.add_argument("--approval-all", action="store_true")
    ap.add_argument("--per-day", type=int, default=4)
    ap.add_argument("--existing", metavar="DECK")
    ap.add_argument("--figures", metavar="PDF", type=Path)
    ap.add_argument("--page", type=int)
    ap.add_argument("--crop", nargs=4, metavar=("PDF", "PAGE", "X0,Y0,X1,Y1", "NAME"))
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--label-px", type=int, default=LABEL_PX)
    ap.add_argument("--source", metavar="WORK")
    args = ap.parse_args()
    if args.existing:
        list_existing(args.existing)
        return
    if args.figures:
        figure_boxes(args.figures, args.page)
        return
    if args.cards_dir is None or not args.cards_dir.is_dir():
        sys.exit(f"anki.py: pass the anki/ folder; got {args.cards_dir}")
    if args.crop:
        if not args.source:
            sys.exit(
                "anki.py: --crop needs --source, the work the PDF holds, such as"
                ' "Vaswani et al., Attention Is All You Need (2017)"'
            )
        pdf, page, corners, name = args.crop
        out = args.cards_dir / "media" / name
        crop_figure(
            Path(pdf), int(page), corners, out, args.source, args.png, args.label_px
        )
        return
    written, errors = load(args.cards_dir)
    cards, step_errors = expand_steps(written)
    errors += step_errors + validate(cards) + check_evidence(written)
    if errors:
        sys.exit("anki.py: invalid cards:\n" + "\n".join(errors))
    if args.approval or args.approval_all:
        write_approval(
            written,
            read_pushed(args.cards_dir / PUSHED),
            args.cards_dir / "approval.html",
            args.per_day,
            args.approval_all,
        )
    elif args.check:
        print(f"{len(cards)} cards valid")
    elif args.apkg:
        write_apkg(cards, args.cards_dir / "cards.apkg")
    else:
        push(cards, args.cards_dir / PUSHED)


if __name__ == "__main__":
    main()
