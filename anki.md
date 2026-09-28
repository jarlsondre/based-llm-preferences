# Anki cards

Flashcards for anything jarl studies. Distilled from Nielsen and Matuschak
(links at the bottom); fetch a source only when this file cannot answer.

Material jarl provides is the notation source and the arbiter when unsure; match
it. If no material is found, ask jarl whether any exists.

## 1. Which cards exist

- Decided with jarl, never for jarl: the agent knows the domain, so it proposes
  what earns cards, and jarl trims what is too granular or too much; morning
  review time is the budget.
- Many small cards over few big ones, but at least two or three per topic. Skip
  trivial inferences, material jarl does not care about, and anything
  speculative or wrong.
- Priority, in this order:
  1. What a thing is: terms and definitions. In math: definitions and notation.
  2. What is true of it and how it works. In math: theorems and lemmas.
  3. Step-by-step sequences, which cost one card per step. In math: proofs.

  Intuition, terminology, and distinctions between similar concepts are welcome
  in every tier. A distinction needs both sides carded first.

## 2. Proposing cards

Cards are chosen before any card text is written.

- Read first: past exams or tests if there are any, then the material.
- Propose one row per card: a stable id, one line saying what the card would
  ask, and how many Anki cards it costs. No question or answer text yet.
- Each row names its evidence: where the fact appears in the material, and the
  exam question behind it if there is one. A row absent from the material says
  so.
- With past exams, group the rows: asked in an exam, close to an exam question,
  in no exam. The first group gets cards first, ahead of the priority order.
- Write the rows to `anki/proposals/<name>.json` in the project's repo, then run
  `uv run tools/anki_proposal.py` on that file from this repo's clone. It writes
  a markdown file and a page beside it. The script's header gives the file
  format.
- In Claude Code, publish the page and read jarl's choices back from it.
  Elsewhere, jarl marks rows in the markdown file.
- Write card text only for the rows jarl kept.

## 3. Writing a card

- One idea per card; almost always answerable, never trivially inferable.
- Self-contained: understandable in two months with no memory of this chat.
  Everything the question uses is defined on the card; nothing else is. Example:
  for \(\partial x^T A x / \partial x\), define "x in R^n, A in R^{n by n}
  symmetric"; also defining \(f(x) = x^T A x\) is unused and gets cut.
- Same answer every time: enough context to exclude alternative answers, no
  more. Short questions, no yes/no questions.
- Ordered material is one card per step: written once as a `"type": "steps"`
  entry, which the tool expands. Card k shows the full numbered list: earlier
  steps in full, step k blanked, later steps as "hidden" placeholders (their
  content gives the blank away, their count does not). Proofs are written this
  way. So are algorithms and protocols, where the order is the knowledge. Other
  cloze cards are rare and short.
- Code goes in backticks, inline or as a fenced block. The tool shows it
  literally, in monospace.
- An optional details footer for the curious is allowed: never needed to answer,
  never filler. If unsure, omit it.
- A failing card is split into atomic pieces (keep an integrative version); a
  card jarl stopped caring about is deleted.

## 4. Building the deck

- `anki/` in the project's repo is the source of truth and where any agent looks
  up existing cards: one JSON file per subdeck, each naming its deck. Every card
  has a stable id, unique across the files.
- Push after stating what changes and getting jarl's yes:
  `uv run tools/anki.py anki/` from this repo's clone (AnkiConnect, Anki open),
  or `--apkg` for a file to import manually.
- The tool owns the mechanics; never work around it: it validates cards
  (duplicate ids, yes/no questions, missing fields, math not in MathJax
  `\(...\)`), applies the one shared note type (per-card formatting is banned),
  updates by id without duplicating, moves a card when its entry changes file,
  and never re-adds cards jarl deleted in review.

## Sources

- Nielsen, Augmenting Long-term Memory: https://augmentingcognition.com/ltm.html
- Matuschak, How to write good prompts: https://andymatuschak.org/prompts
