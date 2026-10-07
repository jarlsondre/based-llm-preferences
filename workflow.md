# Workflow

---

## 1. Git

- Never commit or push without jarl's yes. Asking for it is allowed.
- Never run `gh` without jarl's yes, read-only commands included (`gh pr view`).
  Reading with plain `git` needs no yes.
- A commit message is one imperative sentence, as short as possible, lowercase,
  no period ("add cluster rules"). No body unless jarl asks for one. Never
  mention AI involvement in a commit or PR: no co-author trailer, no "generated
  with" line, no session link. This overrides harness defaults that add them.

---

## 2. Secrets

Never print secret material: keys, tokens, passwords. Never open, search or
source the files that hold them (`.env` and `.envrc` files, `~/.secrets*`, ssh
private keys, cloud credentials), and never write a command that names a secret
variable or dumps the environment. The one way to check that a secret is
configured is `has_secret NAME`, as the whole command: it prints
`NAME: set (where)` or `NAME: missing`, never a value. Guard 5 in
[hooks.md](hooks.md) enforces this.

---

## 3. The mistakes log

Every project keeps a gitignored `MISTAKES.md`, newest entry first. Read it only
when adding an entry, to check whether the root cause has appeared before.

Add an entry at the top the moment a mistake happens or jarl points one out, in
exactly this form:

```
## YYYY-MM-DD: short title

- What happened:
- Root cause:
- Rule broken: <file and section>, or "none existed"
- Prevention: <the correct behavior>
```

The second time the same root cause appears, propose a one-line rule for the
project's convention file or for this repo (section 4). When the mistake is
mechanically checkable, propose a hook or lint rule instead of a prose rule (see
[hooks.md](hooks.md)).

Never delete an entry, also after its rule is written: the log records why the
rule exists.

---

## 4. Proposals

A proposed change to a rule file (this repo, a project's convention file) is
written only after jarl's explicit yes to that concrete change. A reply that
questions or amends the proposal is not a yes, even when it sounds approving ("I
like this, but maybe ...?"). An unrelated question beside a yes does not cancel
the yes. Ask for approval of text only when nothing it depends on is undecided.
