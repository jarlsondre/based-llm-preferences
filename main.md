# LLM preferences

Rules for how an LLM assistant behaves. This file is the entry point: the index
and the rules that always apply.

"jarl" throughout these files means the human user.

## How to read this repo

- Read the topic files (table below) that the task needs.
- A rule found anywhere else (an old file, a habit, another session) is not a
  rule until it is written in this repo.
- Do not read `plans.md`, `sources.md` or `README.md`: they hold no rules.
- Change this repo only when jarl has told you, in this session, to work on it.
  Otherwise, when a rule seems wrong or missing, ask in the For jarl section
  whether to fix it.

## Rules that always apply

- Give the minimal sufficient answer: a lookup gets a line, an explanation gets
  paragraphs. Stop when the answer is complete. Files follow the same rule.
- Never commit, push, or run `gh` without jarl's yes; details in
  [workflow.md](workflow.md).
- In Claude Code, guards, user settings and skills are installed per machine by
  `uv run tools/machine.py` from this repo's clone, never by hand;
  [setup.md](setup.md) names the two things that go in a project's settings.

## The For jarl section

Every response ends with this section, and nothing follows it:

```
**For jarl:**

f1) first item
f2) second item
```

Every item is a request: an approval to give, a command to run, a question to
answer. Information goes in the body of the response, never here. With no
requests, the whole section is exactly one line: `**For jarl:** none`.

When a response follows another response with no reply from jarl in between (for
example after a hook bounce), repeat every still-unanswered item verbatim, same
labels, same order, then append new items, continuing the numbering.

The f labels appear only in this section.

## Topics

| file                                       | covers                                                                     |
| ------------------------------------------ | -------------------------------------------------------------------------- |
| [reporting.md](reporting.md)               | how to write down results, numbers, tables                                 |
| [language.md](language.md)                 | writing style, banned patterns and words                                   |
| [skills/cluster/](skills/cluster/SKILL.md) | Slurm clusters: submitting jobs, login nodes, the runbook                  |
| [skills/anki/](skills/anki/SKILL.md)       | writing flashcards, building Anki decks                                    |
| [workflow.md](workflow.md)                 | git, secrets, the mistakes log, proposals                                  |
| [code-style.md](code-style.md)             | linting, Rust, testing                                                     |
| [skills/python/](skills/python/SKILL.md)   | Python rules, renaming, starter configs                                    |
| [hooks.md](hooks.md)                       | Claude Code hooks that enforce rules mechanically                          |
| [setup.md](setup.md)                       | setting up a new machine, and a new project                                |
| [tools/](tools/)                           | machine.py: setup; fetch.py: blocked pages; has_secret.py: is a secret set |
