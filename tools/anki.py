# /// script
# requires-python = ">=3.11"
# dependencies = ["genanki"]
# ///
"""Validate cards and build Anki decks; conventions in anki.md.

Usage: uv run tools/anki.py anki/cards.json          # push via AnkiConnect (Anki open)
       uv run tools/anki.py anki/cards.json --check  # validate only
       uv run tools/anki.py anki/cards.json --apkg   # write <deck>.apkg instead

cards.json holds {"deck": name, "cards": [...]}; a card is
{"id": stable-slug, "front": question, "back": answer, "extra": optional} or
{"id": stable-slug, "type": "cloze", "text": ..., "extra": optional}.
pushed.json next to it records pushed ids: an id pushed before but now missing
from Anki was deleted by jarl in review and is never re-added.
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

ANKI_URL = "http://localhost:8765"
BASIC_ID = 1758912001
CLOZE_ID = 1758912002
CSS = """.card { font-family: -apple-system, "Helvetica Neue", sans-serif; font-size: 20px;
  text-align: left; color: black; background-color: white; }
.extra { margin-top: 1.2em; padding-top: 0.6em; border-top: 1px dashed #bbb;
  font-size: 15px; color: #777; }
"""
BASIC_BACK = '{{FrontSide}}<hr id="answer">{{Back}}{{#Extra}}<div class="extra">{{Extra}}</div>{{/Extra}}'
CLOZE_BACK = '{{cloze:Text}}{{#Extra}}<div class="extra">{{Extra}}</div>{{/Extra}}'
YES_NO = re.compile(
    r"^(is|are|was|were|do|does|did|can|could|will|would|should|has|have)\b",
    re.IGNORECASE,
)
BARE_DOLLAR = re.compile(r"(?<!\\)\$")


def validate(cards: list[dict[str, str]]) -> list[str]:
    errors = []
    seen: set[str] = set()
    for i, card in enumerate(cards):
        cid = card.get("id", f"<card {i}>")
        if cid in seen:
            errors.append(f"{cid}: duplicate id")
        seen.add(cid)
        is_cloze = card.get("type") == "cloze"
        required = {"id", "text"} if is_cloze else {"id", "front", "back"}
        for field in sorted(required - card.keys()):
            errors.append(f"{cid}: missing field {field}")
        if is_cloze and "{{c" not in card.get("text", ""):
            errors.append(f"{cid}: cloze card without a {{{{c1::...}}}} deletion")
        if not is_cloze and YES_NO.match(card.get("front", "")):
            errors.append(f"{cid}: yes/no question; rephrase open-ended (anki.md)")
        for value in card.values():
            if BARE_DOLLAR.search(value):
                errors.append(
                    rf"{cid}: bare $ delimiter; math is MathJax \(...\) (anki.md)"
                )
                break
    return errors


def fields_for(card: dict[str, str]) -> dict[str, str]:
    if card.get("type") == "cloze":
        return {"Id": card["id"], "Text": card["text"], "Extra": card.get("extra", "")}
    return {
        "Id": card["id"],
        "Front": card["front"],
        "Back": card["back"],
        "Extra": card.get("extra", ""),
    }


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


def ensure_note_types() -> None:
    existing = invoke("modelNames")
    if "jarl-basic" not in existing:
        invoke(
            "createModel",
            modelName="jarl-basic",
            inOrderFields=["Id", "Front", "Back", "Extra"],
            css=CSS,
            cardTemplates=[
                {"Name": "Card 1", "Front": "{{Front}}", "Back": BASIC_BACK}
            ],
        )
    if "jarl-cloze" not in existing:
        invoke(
            "createModel",
            modelName="jarl-cloze",
            inOrderFields=["Id", "Text", "Extra"],
            css=CSS,
            isCloze=True,
            cardTemplates=[
                {"Name": "Cloze", "Front": "{{cloze:Text}}", "Back": CLOZE_BACK}
            ],
        )


def push(deck: str, cards: list[dict[str, str]], pushed_path: Path) -> None:
    pushed = set(json.loads(pushed_path.read_text())) if pushed_path.exists() else set()
    invoke("createDeck", deck=deck)
    ensure_note_types()
    added, updated, skipped = [], [], []
    for card in cards:
        cid = card["id"]
        note_ids = invoke("findNotes", query=f'"Id:{cid}"')
        if note_ids:
            invoke(
                "updateNoteFields", note={"id": note_ids[0], "fields": fields_for(card)}
            )
            updated.append(cid)
        elif cid in pushed:
            skipped.append(cid)
        else:
            model = "jarl-cloze" if card.get("type") == "cloze" else "jarl-basic"
            invoke(
                "addNote",
                note={"deckName": deck, "modelName": model, "fields": fields_for(card)},
            )
            added.append(cid)
    pushed |= set(added) | set(updated)
    pushed_path.write_text(json.dumps(sorted(pushed)) + "\n")
    print(f"{deck}: added {len(added)}, updated {len(updated)}")
    if skipped:
        print(
            "deleted in review, not re-added; remove from cards.json: "
            + ", ".join(skipped)
        )


def write_apkg(deck: str, cards: list[dict[str, str]], out: Path) -> None:
    import genanki  # type: ignore  # uv script dep

    field_names = {
        "jarl-basic": ["Id", "Front", "Back", "Extra"],
        "jarl-cloze": ["Id", "Text", "Extra"],
    }
    basic = genanki.Model(
        BASIC_ID,
        "jarl-basic",
        fields=[{"name": n} for n in field_names["jarl-basic"]],
        templates=[{"name": "Card 1", "qfmt": "{{Front}}", "afmt": BASIC_BACK}],
        css=CSS,
    )
    cloze = genanki.Model(
        CLOZE_ID,
        "jarl-cloze",
        fields=[{"name": n} for n in field_names["jarl-cloze"]],
        templates=[{"name": "Cloze", "qfmt": "{{cloze:Text}}", "afmt": CLOZE_BACK}],
        css=CSS,
        model_type=genanki.Model.CLOZE,
    )
    deck_id = int(hashlib.sha256(deck.encode()).hexdigest()[:8], 16)
    package = genanki.Deck(deck_id, deck)
    for card in cards:
        model = cloze if card.get("type") == "cloze" else basic
        fields = fields_for(card)
        note = genanki.Note(
            model=model,
            fields=[fields[n] for n in field_names[model.name]],
            guid=genanki.guid_for(card["id"]),
        )
        package.add_note(note)
    genanki.Package(package).write_to_file(str(out))
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cards_file", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apkg", action="store_true")
    args = ap.parse_args()
    data = json.loads(args.cards_file.read_text())
    deck, cards = data["deck"], data["cards"]
    errors = validate(cards)
    if errors:
        sys.exit("anki.py: invalid cards:\n" + "\n".join(errors))
    if args.check:
        print(f"{deck}: {len(cards)} cards valid")
    elif args.apkg:
        write_apkg(
            deck, cards, args.cards_file.with_name(deck.replace("::", "-") + ".apkg")
        )
    else:
        push(deck, cards, args.cards_file.with_name("pushed.json"))


if __name__ == "__main__":
    main()
