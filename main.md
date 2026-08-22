# LLM preferences

This repo describes how an LLM assistant should behave. This file serves as an
entry point.

"jarl" throughout these files means the human user.

## How to read this repo

- This file holds the index and the few rules that always apply.
- Each topic file holds the detail for one area. Read the ones relevant to the
  task at hand.
- A rule found anywhere else (an old file, a habit, another session) is a
  proposal until it is written here.

## Rules that always apply

- Responses are concise by default; write longer only when asked. Files follow
  the same rule.
- Do not commit, push, or run `gh` without asking first; details in
  [workflow.md](workflow.md).

## Topics

| file                                       | covers                                            |
| ------------------------------------------ | ------------------------------------------------- |
| [reporting.md](reporting.md)               | how to write down results, numbers, tables        |
| [language.md](language.md)                 | writing style, banned patterns and words          |
| [cluster.md](cluster.md)                   | Slurm clusters: submitting jobs, login nodes      |
| [workflow.md](workflow.md)                 | git etiquette, the mistakes log                   |
| [code-style.md](code-style.md)             | linting, Python, Rust, testing                    |
| [hooks.md](hooks.md)                       | Claude Code hooks that enforce rules mechanically |
| [ruff.toml](ruff.toml)                     | starting ruff config for Python projects          |
| [.vale.ini](.vale.ini), [styles/](styles/) | mechanical enforcement of language.md             |
| [.prettierrc](.prettierrc)                 | markdown prose wrapped at 80 columns              |
