# Workflow

Git etiquette and the mistakes log.

---

## 1. Git

- Do not commit or push on jarl's behalf, unless explicitly asked to do so.
- Never run `gh` without asking first. This covers reading (`gh repo list`,
  `gh pr view`, `gh auth status`) as well as writing. Plain `git` may be used
  freely for reading.

---

## 2. Secrets

Never print secret material: keys, tokens, passwords. Never open the files that
hold them (`.env` files, `~/.secrets*`, ssh private keys, cloud credentials). To
check a secret is configured, test presence without the value:
`grep -q NAME file`, or `printenv NAME >/dev/null && echo set`. Guard 5 in
[hooks.md](hooks.md) enforces the file ban.

---

## 3. The mistakes log

Every project keeps a gitignored `MISTAKES.md`, newest entry first. It is
evidence, not context: do not load it routinely, and do not go looking for rules
in it. Rules live in the project's convention file and in this repo; the log is
where the evidence for them accumulates.

Append an entry the moment a mistake happens or jarl points one out. Each entry
states:

- date
- what happened
- root cause
- which written rule was broken, or "none existed"
- prevention, phrased as the correct behavior

Sessions log; they do not decide. When the same root cause has appeared two or
three times, propose a one-line rule for the project's convention file or for
this repo, then wait for jarl. When the mistake is mechanically checkable,
propose a hook or lint rule instead of a prose rule (see [hooks.md](hooks.md)).

Entries stay in the log after a rule is promoted. They are the audit trail: the
record of why the rule exists, kept so the rule does not get argued away later.
