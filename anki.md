# Anki cards

Flashcards for jarl's courses. Distilled from Nielsen and Matuschak (links at
the bottom); fetch a source only when this file cannot answer.

Course material jarl provides is the notation source and the arbiter when
unsure; match it. If no material is found, ask jarl whether any exists.

## 1. Which cards exist

- Decided with jarl, never for jarl: the agent knows the domain, so it proposes
  what earns cards, and jarl trims what is too granular or too much; morning
  review time is the budget.
- Many small cards over few big ones, but at least two or three per topic. Skip
  trivial inferences, material jarl does not care about, and anything
  speculative or wrong.
- Math priority: definitions, then results, then proofs; intuition and
  terminology cards are welcome in every tier.

## 2. Writing a card

- One idea per card; almost always answerable, never trivially inferable.
- Self-contained: understandable in two months with no memory of this chat.
  Everything the question uses is defined on the card; nothing else is. Example:
  for \(\partial x^T A x / \partial x\), define "x in R^n, A in R^{n by n}
  symmetric"; also defining \(f(x) = x^T A x\) is unused and gets cut.
- Same answer every time: enough context to exclude alternative answers, no
  more. Short questions, no yes/no questions.
- Proof cloze is incremental: earlier steps visible, all later steps hidden
  (they give the blank away). Cloze elsewhere is rare and short.
- An optional details footer for the curious is allowed: never needed to answer,
  never filler. If unsure, omit it.
- A failing card is split into atomic pieces (keep an integrative version); a
  card jarl stopped caring about is deleted.

## 3. Building the deck

- `anki/cards.json` in the course repo is the source of truth and where any
  agent looks up existing cards; every card has a stable id.
- Push after stating what changes and getting jarl's yes:
  `uv run tools/anki.py anki/cards.json` from this repo's clone (AnkiConnect,
  Anki open), or `--apkg` for a file to import manually.
- The tool owns the mechanics; never work around it: it validates cards
  (duplicate ids, yes/no questions, missing fields, math not in MathJax
  `\(...\)`), applies the one shared note type (per-card formatting is banned),
  updates by id without duplicating, and never re-adds cards jarl deleted in
  review.

## Sources

- Nielsen, Augmenting Long-term Memory: https://augmentingcognition.com/ltm.html
- Matuschak, How to write good prompts: https://andymatuschak.org/prompts
