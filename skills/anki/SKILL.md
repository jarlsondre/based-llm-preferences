---
name: anki
description:
  Write Anki flashcards for anything jarl studies, get jarl's approval on a
  page, and push them into Anki. Use when jarl asks for flashcards, Anki cards
  or a deck, or wants existing cards checked or converted.
compatibility: Needs uv. Pushing needs Anki open with the AnkiConnect add-on.
---

# Anki cards

`${CLAUDE_SKILL_DIR}` is the folder this file is in; where it shows as literal
text, put the path in its place. The tool is
`${CLAUDE_SKILL_DIR}/scripts/anki.py`. Run it with `--help` before writing card
files: that prints the card file format.

Match the notation of jarl's material and settle doubts from it. Notation jarl
states overrides the material; record it in the project's convention file (e.g.
`CLAUDE.md`). No material found: ask jarl whether any exists.

## 1. Which cards exist

- Propose cards by writing them; jarl trims them on the approval page (section
  2): morning review time is the budget. Never push a card jarl has not
  approved.
- Many small cards rather than a few large ones: a card holding several ideas is
  scheduled as one unit, so the algorithm cannot tell which part is known, and
  it is tiring to review.
- Priority, in this order:
  1. What a thing is: terms and definitions. In math: definitions and notation.
  2. What is true of it and how it works. In math: theorems and lemmas.
  3. Step-by-step sequences, which cost one card per step. In math: proofs.

  Intuition and distinctions between similar concepts fit every tier. Card both
  sides before the distinction.

## 2. Approving new cards

1. Ask which parts of the material jarl has covered, and write cards only for
   those. Read past exams or tests first if there are any, then the material.
2. List the cards already in the target deck with
   `uv run ${CLAUDE_SKILL_DIR}/scripts/anki.py --existing <deck>`, and write no
   card that one of them covers.
3. Cards that listing marks `NOT IN FILES` were made outside the card files. Ask
   jarl whether to convert them to the shared note type, which costs one one-way
   sync in Anki; never convert unasked. After a yes, add the card to the files
   with `"adopt": <note id>`, the listing's first column.
4. Write the cards (section 3). Give each its evidence: `where` (the place in
   the material) and, when past exams exist, `asked` (`"directly"`, or
   `"indirectly"` for close to an exam question) with `exam` (the question).
   Directly asked cards outrank the section 1 priority order.
5. Build the page with
   `uv run ${CLAUDE_SKILL_DIR}/scripts/anki.py anki/ --approval`. In Claude
   Code, follow the line the tool prints to publish it and read jarl's choices.
   Elsewhere, jarl opens the file in a browser and pastes its text box back.
6. Remove the cards jarl dropped from the card files. A note on one card applies
   to every card with the same flaw: check all cards against each note, and
   report what changed.
7. If cards changed and jarl wants another look, repeat step 5. Otherwise push
   (section 4).

## 3. Writing a card

- One idea per card, and one ask: "what is X, and why?" is two. Easy enough that
  jarl nearly always recalls it, never trivially inferable.
- Self-contained: understandable in two months with no memory of this chat.
  `setting` defines everything the question uses and nothing else. Example: for
  \(\partial x^T A x / \partial x\), define "x in R^n, A in R^{n by n}
  symmetric"; defining \(f(x) = x^T A x\) too is unused, cut it. No term or
  symbol jarl has not met yet.
- Every card names its `kind`: the sort of answer it wants, in one or two words
  (`--help` lists examples).
- Card the general fact, never a specific exercise, which gets answered by rote.
  An example can go in `extra`.
- Same answer every time: enough context to exclude alternative answers, no
  more. Short questions, no yes/no questions.
- Ordered material (proofs, algorithms, protocols) is one `"type": "steps"`
  entry; the tool makes one card per step. Other cloze cards are rare and short.
- Code goes in backticks, inline or as a fenced block.
- Math is MathJax `\(...\)`; the tool rejects a bare `$` outside code.
- `extra` is an optional footer: never needed to answer. If unsure, omit it.
- A card jarl keeps failing is split into one-idea cards; keep the original too.
  A card jarl no longer wants: remove its entry and ask jarl to delete the note
  in Anki.

## 4. Building the deck

- Cards live in `anki/` in the project's repo; `--help` has the format. The
  files hold the cards the tool manages; `--existing` also shows cards made
  outside them. Never change an id after a push: the tool would add a second
  note.
- Push after stating what changes and getting jarl's yes:
  `uv run ${CLAUDE_SKILL_DIR}/scripts/anki.py anki/`. `--apkg` writes a file to
  import by hand instead; it ignores `pushed.json` and `adopt`, so the import
  brings back cards jarl deleted and duplicates an adopted card. Use it only
  when Anki cannot be reached.
- Never work around the tool; per-card formatting is banned.

## Sources

Fetch a source only when this file cannot answer.

- Nielsen, Augmenting Long-term Memory: https://augmentingcognition.com/ltm.html
- Matuschak, How to write good prompts: https://andymatuschak.org/prompts
