# Plans

Ideas worth adding, not prioritized yet. Nothing here is a rule.

- LaTeX guidelines. Wait until the paper has produced a few corrections, then
  build a latex skill in one go: the rules, a compile-log check (undefined
  references, missing citations, overfull boxes), a formatter (latexindent or
  tex-fmt), and guard 7 moved in.

## Open threads (2026-10-13)

Paused mid-discussion; resume in this order unless jarl says otherwise.

- Mistakes logs in `other-mistakes/`: 16 rule candidates were proposed (four for
  main.md, two for workflow.md, three for reporting.md, four for the cluster
  skill, three for code-style.md and hooks.md). Open: gitignore the folder (the
  repo is public and the logs name colleagues), which candidates to write, and
  the entry-form changes (three-sentence cap on "what happened", a one-word
  cause tag, prevention written as a rule candidate).
- ASD-STE100: language.md section 2 names the standard and lists the adopted
  rules (written 2026-10-20); the Vale STE style enforces five of them on rule
  files; the other rule files were cleaned up against it the same day. Open:
  whether to test that naming the standard changes model output. For audits
  with a real parser: sourdough-bread/asd-ste100-checker, run with the
  dictionary findings ignored (scanned and run 2026-10-20).
- Approval page: fixed 2026-10-13, tested live; awaiting commit.
- Fetch skill and guard 12: written and installed 2026-10-20; awaiting commit.
  Possible later addition: click through cookie banners.
- Bring slurminator (~/programming/misc/slurminator, builds and submits Slurm
  scripts from a config) into the cluster skill, once jarl's current projects
  are done.
