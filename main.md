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
- `plans.md` and `sources.md` are jarl's bookkeeping, and `README.md` is for
  human readers: do not read them.

## Rules that always apply

- Give the minimal sufficient answer: a lookup gets a line, an explanation gets
  paragraphs. Nothing after the answer is done. Files follow the same rule.
- Do not commit, push, or run `gh` without asking first; details in
  [workflow.md](workflow.md).
- Prefer LSP operations for code navigation (definitions, references, symbols);
  grep is for text and pattern searches.
- If an LSP call fails because no language server is configured, say so in the
  For jarl section; the fix is in setup.md.

## The For jarl section

Every response ends with this section, and nothing follows it:

```
**For jarl:**

f1) first item
f2) second item
```

Every item is a request: an approval to give, a command to run, a question to
answer. The test: jarl reads the item and now has something to do. A sentence
that only informs the reader is not an item; report it in the body of the
response, never here. With no requests, the whole section is exactly one line:
`**For jarl:** none`.

When a response follows another response with no reply from jarl in between (for
example after a hook bounce), repeat every still-unanswered item verbatim, same
labels, same order, and append any new items after them.

Ordinary numbered lists are fine elsewhere in the response; the f labels appear
only here.

## Topics

| file                                       | covers                                            |
| ------------------------------------------ | ------------------------------------------------- |
| [reporting.md](reporting.md)               | how to write down results, numbers, tables        |
| [language.md](language.md)                 | writing style, banned patterns and words          |
| [cluster.md](cluster.md)                   | Slurm clusters: submitting jobs, login nodes      |
| [workflow.md](workflow.md)                 | git etiquette, secrets, the mistakes log          |
| [code-style.md](code-style.md)             | linting, Python, Rust, testing                    |
| [hooks.md](hooks.md)                       | Claude Code hooks that enforce rules mechanically |
| [python/](python/)                         | starter configs for Python projects               |
| [gitignore](gitignore)                     | starter .gitignore for new projects               |
| [.vale.ini](.vale.ini), [styles/](styles/) | mechanical enforcement of language.md             |
| [.prettierrc](.prettierrc)                 | markdown prose wrapped at 80 columns              |
| [setup.md](setup.md)                       | copying these configs into a project              |
| [tools/](tools/)                           | scripts to run, e.g. fetch.py for blocked pages   |
