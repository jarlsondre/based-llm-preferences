# /// script
# requires-python = ">=3.11"
# dependencies = ["genanki"]
# ///
"""Validate cards and build Anki decks; conventions in this skill's SKILL.md.

Usage: uv run anki.py anki/             # push via AnkiConnect (Anki open)
       uv run anki.py anki/ --check     # validate only
       uv run anki.py anki/ --approval  # write anki/approval.html
       uv run anki.py anki/ --apkg      # write anki/cards.apkg instead
       uv run anki.py --existing DECK   # list the cards already in a deck
       uv run anki.py --help            # print this text

The directory holds one JSON file per subdeck: {"deck": full deck name,
"cards": [...]}. Ids are unique across all files. A card is
{"id": stable-slug, "front": question, "back": answer},
{"id": stable-slug, "type": "cloze", "text": ...}, or
{"id": stable-slug, "type": "steps", "intro": claim or title, "steps": [...]}.
A steps card (a proof, an algorithm, a protocol) expands to one cloze note per
step with ids id-1..id-n: earlier steps shown, step k blanked, later steps as
"hidden" placeholders. All take optional "setting" (definitions the question
needs) and "extra" (footer for the curious).

"kind" says what sort of answer the card wants, in one or two words. It is
shown as a plain label at the top right of the card. In math: "definition", "theorem",
"proposition", "example", "notation", "intuition". Elsewhere: "term",
"property", "mechanism", "comparison", "command".

Code goes in backticks, inline or as a fenced block. It is escaped and shown
literally, so cloze markup and math inside code are not interpreted.

The files decide where a card lives: a card whose entry moves to another file
is moved to that file's deck on the next push.

--approval writes the page where jarl approves cards before a push: the cards
not pushed yet (--approval-all: every card), with a tick and a note per card.
--per-day N sets the days estimate (default 4). The page also shows these
optional fields, which a push ignores: "topic" (a heading inside the subdeck),
"where" (the place in the material), and together "asked" ("directly" or
"indirectly") with "exam" (the past exam or test question). A card with neither
counts as never asked.

"adopt": Anki note id, on a card, converts that existing note to the shared
note type on the next push, keeping its review history. Only after jarl said
yes to converting it.

pushed.json in the directory records pushed ids: an id pushed before but now
missing from Anki was deleted by jarl in review and is never re-added.
"""

import argparse
import hashlib
import html
import json
import re
import sys
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
.extra::before { content: "Note"; }
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
"""
SETTING = '{{#Setting}}<div class="setting">{{Setting}}</div>{{/Setting}}'
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
FENCED = re.compile(r"```[\w-]*\n?(.*?)```", re.DOTALL)
INLINE = re.compile(r"`([^`\n]+)`")
TAGS = re.compile(r"<[^>]+>")
CLOZE = re.compile(r"\{\{c\d+::(.*?)(?:::[^}]*)?\}\}", re.DOTALL)
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


def render_code(text: str) -> str:
    text = FENCED.sub(
        lambda m: f"<pre><code>{escape_code(m[1].strip(chr(10)))}</code></pre>", text
    )
    return INLINE.sub(lambda m: f"<code>{escape_code(m[1])}</code>", text)


def load(cards_dir: Path) -> list[dict[str, Any]]:
    files = sorted(p for p in cards_dir.glob("*.json") if p.name != PUSHED)
    if not files:
        sys.exit(f"anki.py: no card files (*.json) in {cards_dir}")
    cards = []
    for path in files:
        data = json.loads(path.read_text())
        for raw in data["cards"]:
            card = dict(raw) | {"deck": data["deck"], "file": path.name}
            for key in CONTENT:
                if isinstance(card.get(key), str):
                    card[key] = render_code(card[key])
            if isinstance(card.get("steps"), list):
                card["steps"] = [render_code(str(step)) for step in card["steps"]]
            cards.append(card)
    return cards


def label(card: dict[str, Any]) -> str:
    return f"{card['file']}: {card.get('id', '<no id>')}"


def expand_steps(
    cards: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Turn steps cards into one cloze note per step; later steps show as placeholders."""
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
                f"{label(card)}: yes/no question; rephrase open-ended (anki.md)"
            )
        if not isinstance(card.get("kind", ""), str):
            errors.append(f'{label(card)}: kind must be text, such as "definition"')
        if "adopt" in card and not isinstance(card["adopt"], int):
            errors.append(f"{label(card)}: adopt must be the Anki note id, a number")
        if any(BARE_DOLLAR.search(str(card.get(key, ""))) for key in CONTENT):
            errors.append(
                rf"{label(card)}: bare $ outside code; math is MathJax \(...\),"
                " code goes in backticks (anki.md)"
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


def push(cards: list[dict[str, Any]], pushed_path: Path) -> None:
    pushed = read_pushed(pushed_path)
    decks = sorted({card["deck"] for card in cards})
    for deck in decks:
        invoke("createDeck", deck=deck)
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
        f"converted {len(adopted)}, moved {moved}"
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
    genanki.Package(list(decks.values())).write_to_file(str(out))
    print(f"wrote {out} ({len(decks)} decks, {len(cards)} cards)")


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


def write_approval(
    cards: list[dict[str, Any]], pushed: set[str], out: Path, per_day: int, full: bool
) -> None:
    """Write the page where jarl reads, ticks and comments on cards before a push."""
    rows = []
    for card in cards:
        steps = card["steps"] if card.get("type") == "steps" else []
        ids = [f"{card['id']}-{k + 1}" for k in range(len(steps))] or [card["id"]]
        if not full and all(cid in pushed for cid in ids):
            continue
        row = {key: card[key] for key in PAGE_KEYS if key in card}
        if card.get("type") == "cloze":
            row["text"] = CLOZE.sub(r'<span class="cloze">\1</span>', card["text"])
        row |= {
            "subdeck": card["deck"].split("::")[-1],
            "inAnki": "adopt" in card,
            "cards": len(ids),
        }
        rows.append(row)
    if not rows:
        sys.exit(
            "anki.py: nothing to approve, every card is in Anki; try --approval-all"
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
        ' jarl\'s choices from collection "approval", document "cards".'
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
    args = ap.parse_args()
    if args.existing:
        list_existing(args.existing)
        return
    if args.cards_dir is None or not args.cards_dir.is_dir():
        sys.exit(f"anki.py: pass the anki/ folder; got {args.cards_dir}")
    written = load(args.cards_dir)
    cards, errors = expand_steps(written)
    errors += validate(cards) + check_evidence(written)
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
