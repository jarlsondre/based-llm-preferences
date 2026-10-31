# Plans

Ideas worth adding, not prioritized yet. Nothing here is a rule.

- LaTeX guidelines. Wait until the paper has produced a few corrections, then
  build a latex skill in one go: the rules, a compile-log check (undefined
  references, missing citations, overfull boxes), a formatter (latexindent or
  tex-fmt), and guard 7 moved in.
- Fetch skill: click through cookie banners, which today fill the page text.

## Open threads (updated 2026-10-31)

Paused mid-discussion; resume in this order unless jarl says otherwise.

- Mistakes logs in `other-mistakes/` (gitignored 2026-10-28): 16 rule candidates
  were proposed (four for main.md, two for workflow.md, three for reporting.md,
  four for the cluster skill, three for code-style.md and hooks.md). Open: which
  candidates to write, and the entry-form changes (three-sentence cap on "what
  happened", a one-word cause tag, prevention written as a rule candidate).
- Coursework spoilers (2026-10-28): agents in course directories answer the
  question asked and then also give the solution, their own or the course's.
  Settled: each course is one directory with its own `.claude/settings.json`;
  the agent finds the solution files per course. Design so far, nothing written:
  a rule with a checkable definition of a spoiler and an unlock phrase; a
  reminder from a UserPromptSubmit hook in the course settings, only on messages
  that mention an assignment or exercise; a deny guard on solution files. Open:
  the unlock phrase, and whether "check my answer" passes by default.
- ASD-STE100: language.md section 2 names the standard and lists the adopted
  rules (written 2026-10-20); the Vale STE style enforces five of them on rule
  files; the other rule files were cleaned up against it the same day. Open:
  whether to test that naming the standard changes model output. For audits with
  a real parser: sourdough-bread/asd-ste100-checker, run with the dictionary
  findings ignored (scanned and run 2026-10-20).
- Bring slurminator (~/programming/misc/slurminator, builds and submits Slurm
  scripts from a config) into the cluster skill, once jarl's current projects
  are done.
