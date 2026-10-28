# Code style

---

## 1. Any language

- After understanding the problem and before writing code, check in order: (1)
  does this need to exist at all, (2) does the codebase already have it, (3)
  does the stdlib have it, (4) does the platform have it, (5) does an installed
  dependency have it. Only then write it, minimally.
- After editing code, run the project's formatter, linter, and type checker.
  Work is not done while any of them complains.
- No new dependencies without asking jarl first.
- Prefer pure functions where the cost is small: they are easier to test.
- Keep functions small, but do not extract a one-liner unless the separation
  makes semantic sense on its own, or the same line appears more than three
  times.
- A comment states what the code cannot: a constraint, a why, a warning. Never
  narrate what the next line does. One line is the norm; a longer explanation
  goes in a doc.
- Edit files with the harness's editing tools, never with string-replacement
  commands or scripts (`sed -i`, `.replace()` one-liners). Those skip the hooks,
  and a failed match is a silent no-op where the editing tool fails loudly. Two
  exceptions. The rename tool in the python skill. A mechanical transform across
  many files, never one or two: tell jarl before the script runs. The script
  sets the encoding explicitly, counts the replacements, and fails on zero
  matches. Guard 11 in hooks.md denies such a command unless its first line is
  `# not using Edit because: <reason>`. The reason names what the editing tool
  cannot do, such as a command whose output is the file.

---

## 2. Python

See the python skill: [skills/python/SKILL.md](skills/python/SKILL.md).

---

## 3. Rust

- Format with `cargo fmt`, default style.
- Lint with `cargo clippy -- -D warnings`.

---

## 4. Testing

A test pins behavior so the implementation can change freely: a function's body
must be rewritable (a faster algorithm, a different data structure) with every
test still passing. When a test breaks and only the implementation changed,
rewrite or delete the test.

- A test knows only the contract: the signature and the documented behavior.
  Feed inputs, assert on outputs and observable effects.
- Never assert on how: no "f called g", no "the database call happened" (assert
  on the stored row instead).
- Mock only what cannot run inside a test (external services, the network).
- Cover every behavior the contract describes, including the failures.
- Every bug that got past the tests gets a regression test as part of the fix.
