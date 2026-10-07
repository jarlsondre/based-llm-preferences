# Setup

## 1. A new machine

Clone this repo, then from the clone:

```sh
uv run tools/machine.py           # bring this machine up to date
uv run tools/machine.py --check   # only report; exit code 1 when out of date
```

It puts the guards and settings from [hooks.md](hooks.md) into
`~/.claude/settings.json`, links every folder in [skills/](skills/) into
`~/.claude/skills/`, links `has_secret` into `~/.local/bin`, and names any
missing command-line tool; install what it names. After pulling this repo, run
it again and tell jarl what it changed. A setting or skill meant for every
machine goes into hooks.md or skills/, never into one machine by hand.

LSP plugins are installed by hand. Get the binaries first:
`brew install pyright` on macOS or `npm install -g pyright` elsewhere, and
`rustup component add rust-analyzer`. Then:

```sh
claude plugin install pyright-lsp@claude-plugins-official
claude plugin install rust-analyzer-lsp@claude-plugins-official
```

Pick user scope when prompted. If `claude plugin list` shows a plugin disabled,
run `claude plugin enable <name>` and restart the session.

## 2. A new project

Symlink the Vale and prettier configs, never copy them: a copy goes stale
silently.

```sh
PREFS=<this repo's clone: the directory this file is in>
ln -sf "$PREFS/.vale.ini" "$PREFS/.prettierrc" "$PREFS/styles" .
cp "$PREFS/gitignore" .gitignore   # new projects only
cp "$PREFS/skills/python/assets/"* .   # Python projects only
```

- The symlinks are per machine and gitignored. The `gitignore` starter covers
  them; in an existing project, add `.vale.ini`, `.prettierrc` and `styles` to
  its `.gitignore`. On a machine where they are missing or dangling, re-run the
  `ln` line.
- The project owns the copied files: extend and commit them.
- Never recreate any of these files from memory.
- The project's committed `.claude/settings.json` holds two things: the
  `attribution` object from hooks.md section 8 and, in a project that produces
  results, guard 4 (hooks.md section 4). No other guard goes in it.
