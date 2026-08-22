# Setup

How to bring this repo's config files into a project. The language configs are
symlinked, so the machine has exactly one copy of the rules: a broken link fails
loudly and gets re-created, while a copy would go stale silently.

```sh
PREFS=<this repo's clone: the directory this file is in>
ln -s "$PREFS/.vale.ini" "$PREFS/.prettierrc" "$PREFS/styles" .
cp "$PREFS/ruff.toml" .   # Python projects only
```

- The symlinks are per-machine: add `.vale.ini`, `.prettierrc`, and `styles` to
  the project's `.gitignore`. On a machine where they are missing or dangling,
  re-run the `ln` line.
- `ruff.toml` is copied, not linked: it is a starting config the project owns,
  may change, and gets committed so collaborators and CI have it.
- Never recreate any of these files from memory.

The Claude Code guards install differently (they merge into
`.claude/settings.json`); see [hooks.md](hooks.md).
