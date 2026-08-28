# Setup

How to bring this repo's config files into a project. The language configs are
symlinked, so the machine has exactly one copy of the rules: a broken link fails
loudly and gets re-created, while a copy would go stale silently.

```sh
PREFS=<this repo's clone: the directory this file is in>
ln -s "$PREFS/.vale.ini" "$PREFS/.prettierrc" "$PREFS/styles" .
cp "$PREFS/gitignore" .gitignore   # new projects only
cp "$PREFS/python/"* .             # Python projects only
```

- The symlinks are per-machine and gitignored (the `gitignore` starter covers
  them). On a machine where they are missing or dangling, re-run the `ln` line.
- The copied files are starters: the project owns them, extends them, and
  commits them.
- Never recreate any of these files from memory.

The Claude Code guards install differently (they merge into
`.claude/settings.json`); see [hooks.md](hooks.md).
