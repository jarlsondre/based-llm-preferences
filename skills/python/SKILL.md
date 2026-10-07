---
name: python
description:
  "Rules and tools for Python code in jarl's projects: uv, ruff, ty and pytest,
  finding code with the language server, renaming symbols, and starter configs.
  Use when reading, writing or changing Python code, or when setting up a Python
  project."
compatibility: Needs uv.
---

# Python

`${CLAUDE_SKILL_DIR}` is the folder this file is in; where it shows as literal
text, put the path in its place.

## 1. Tools

- **uv** (`uv`, `uvx`) for environments, installs and running tools. Take a
  sizeable detour to keep it; drop it only with jarl's yes.
- **ruff** lints and formats.
- **ty** checks types. New code carries type annotations. ty config lives in
  `ty.toml`, not `pyproject.toml`. `ty.toml` and `pyrightconfig.json` (the LSP)
  mirror each other: change both, or pyright reports imports that resolve fine.
- **pytest** runs tests; warnings are errors.
- A new project copies the starters (`ruff.toml`, `ty.toml`,
  `pyrightconfig.json`, `pytest.ini`) with `cp ${CLAUDE_SKILL_DIR}/assets/* .`,
  then edits and commits them. Never recreate them from memory.

## 2. Finding code

- Prefer LSP operations for code navigation (definitions, references, symbols);
  grep is for text and pattern searches.
- If an LSP call fails because no language server is configured, ask jarl in the
  For jarl section to install the LSP plugin (setup.md section 1 of the
  preferences repo).

## 3. Renaming

- Rename a symbol with the tool, never by editing each reference:
  `uv run ${CLAUDE_SKILL_DIR}/scripts/rename.py FILE:LINE:COL NEW_NAME`;
  `--help` has the flags and checks.
- Use `--force` only after finding out why the tool refused.
- Afterwards fix the quoted names it lists by hand, and run ruff and ty on the
  files it prints: no edit hook fires on them.
