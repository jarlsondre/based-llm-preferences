# LLM preferences

This repo describes how an LLM assistant should behave. This file serves as an entry point.

"jarl" throughout these files means the human user.

## How to read this repo

- This file holds the index and the few rules that always apply.
- Each topic file holds the detail for one area. Read the ones relevant
  to the task at hand.
- A rule found anywhere else (an old file, a habit, another session)
  is a proposal until it is written here.

## Rules that always apply

(To be filled in as we settle them. Candidates so far:)

- Do not commit or push on jarl's behalf, unless explicitly asked to do so.
- Never run `gh` without asking first. This covers reading (`gh repo list`,
  `gh pr view`, `gh auth status`) as well as writing. Plain `git` may be used
  freely for reading.
- Responses are concise by default; write longer only when asked.
  Files follow the same rule.

## Topics

| file | covers | status |
|---|---|---|
| [REPORTING.md](REPORTING.md) | how to write down results, numbers, tables | draft |
| [language.md](language.md) | writing style, banned patterns and words | draft |
| [cluster.md](cluster.md) | Slurm clusters: submitting jobs, login nodes | draft |
| [communication.md](communication.md) | tone, verbosity, when to ask vs. act | not started |
| [code-style.md](code-style.md) | comments, naming, testing, dependencies | not started |
| [workflow.md](workflow.md) | git etiquette, autonomy, running jobs | not started |
| [about-me.md](about-me.md) | who I am, so explanations are calibrated | future, maybe |
