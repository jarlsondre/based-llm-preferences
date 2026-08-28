# Sources

Where the rules came from. Bookkeeping for jarl; not for models to read.

- Mistakes log (workflow.md): reddit r/ClaudeCode, "I make Claude Code keep a
  MISTAKES.md file" by thabxi, 2026-08. Evidence-store framing, promotion on
  repetition, deposit-then-audit split (commenter tribat).
- Testing section (code-style.md): TestDriven.io "Test behavior, not
  implementation"; "An Empirical Evaluation of Property-Based Testing in Python"
  (OOPSLA 2025,
  https://cseweb.ucsd.edu/~mcoblenz/assets/pdf/OOPSLA_2025_PBT.pdf); coverage vs
  mutation overview
  (https://www.aravindhu.com/software%20development/2020/12/06/coverage-vs-mutation-vs-property-base-testing.html).
- Check-before-ladder bullet (code-style.md): ponytail
  (https://github.com/DietrichGebert/ponytail), distilled, plugin not adopted.
- Anti-slop ruff families (ruff.toml): GitClear 211M-line analysis via
  https://arter.dev/blog/the-antidote-to-code-slop/; antislop
  (https://github.com/skew202/antislop) for the deferral/placeholder categories;
  scicode-lint (https://arxiv.org/pdf/2603.17893) watched, not adopted.
- Minimal-sufficient-answer rule (main.md): "Brevity is the soul of
  sustainability" (https://arxiv.org/pdf/2506.08686), directive "Only provide
  the minimal answer" measured best (~60% shorter); YapBench
  (https://arxiv.org/html/2601.00624) for the "minimal sufficient" framing;
  accuracy cost of aggressive brevity (https://arxiv.org/pdf/2401.05618).
