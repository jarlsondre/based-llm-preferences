# Code style

---

## 1. Any language

- Before writing code, check in order: (1) does this need to exist at all, (2)
  does the codebase already have it, (3) does the stdlib have it, (4) does the
  platform have it, (5) does an installed dependency have it. Only then write
  it, minimally. Check after understanding the problem, not instead of it.
  (Distilled from ponytail.)
- After editing code, run the project's formatter, linter, and type checker.
  Work is not done while any of them complains.
- No new dependencies without asking jarl first.
- Prefer pure functions wherever it is not a big hassle. They are easier to test
  and to reason about.
- Keep functions small, but do not extract a one-liner unless the separation
  makes semantic sense on its own, or the same line appears more than about
  three times.
- A comment states what the code cannot: a constraint, a why, a warning. Never
  narrate what the next line does. One line is the norm; if it needs more,
  consider whether the explanation belongs in a doc instead.
- Edit files with the harness's editing tools, never with string-replacement
  commands or scripts (`sed -i`, `.replace()` one-liners). Those skip the hooks,
  and a failed match is a silent no-op where the editing tool fails loudly. The
  one exception is a bulk mechanical transform across many files; there, set the
  encoding explicitly, count the replacements, and fail on zero matches.

---

## 2. Python

- **uv, always.** Environments, installs, running tools: `uv` and `uvx` for
  everything. A sizeable detour to keep uv is the correct trade; dropping it
  needs a really good reason.
- **ruff** lints and formats. New projects start from this repo's
  [python/ruff.toml](python/ruff.toml).
- **ty** checks types. New code carries type annotations; the ANN rules in ruff
  enforce this. ty config lives in `ty.toml`, not `pyproject.toml`. `ty.toml`
  and `pyrightconfig.json` (the LSP) are a mirrored pair, starting from this
  repo's [python/](python/) copies: change both, or pyright reports imports that
  resolve fine.
- **pytest** runs tests, starting from this repo's
  [python/pytest.ini](python/pytest.ini): warnings are errors.

---

## 3. Rust

- **rustfmt** with default style formats everything.
- **clippy** is the linter, with warnings as errors:
  `cargo clippy -- -D warnings`.

---

## 4. Testing

The point of a test is to pin down behavior so the implementation can change
freely. A function's body should be fully rewritable (a faster algorithm, a
different data structure) with every test still passing. A test that breaks when
the implementation changes, while the behavior did not, is holding the code
back; rewrite or delete it.

- A test knows only the contract: the signature and the documented behavior.
  Feed inputs, assert on outputs and observable effects.
- Never assert on how: no "check that the database call happened", no "check
  that f called g". If a test needs to look inside the function, the test is
  wrong.
- Mock only what cannot run inside a test (external services, the network).
  Never mock in order to observe internals. Prefer real objects when they are
  cheap to construct.
- A function usually allows several logic paths depending on its input. Cover
  each path, including the failure paths.
- Every bug that got past the tests gets a regression test as part of the fix.
