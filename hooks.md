# Hooks

Mechanical guards for rules that must not depend on the model remembering prose.
This file is Claude Code specific.

The guards and settings below live in the user settings,
`~/.claude/settings.json`, so they apply in every project on the machine.
`uv run tools/machine.py` installs them; setup.md section 1 has the commands.

The tool merges every JSON block that follows the exact line "Merge into
`~/.claude/settings.json`:". That line is the tool's marker, never an
instruction to merge by hand. Every guard command starts with the same `jq`
check, `command -v jq >/dev/null || { echo 'hook: jq missing`; the tool removes
any installed hook that starts with it and is no longer in this file. A setting
that should hold on every machine is added here as such a block, never set by
hand on one machine.

Never retype a guard from memory. Never put these guards in a project's
`.claude/settings.json`: a project copy that differs from the user copy runs
next to it. A project's settings hold only guard 4 and the attribution setting
in section 8.

After pulling this repo, run `uv run tools/machine.py` and tell jarl what it
changed. When a project's `.claude/settings.json` still carries guards from this
file, remove them and tell jarl.

Every guard needs `jq`; without it the guard fails the tool call with an install
message. Guards match text: a reworded command can evade them, and an unrelated
command can trigger them, which costs one prompt or one denied call. Hooks run
in every permission mode; in a mode that never prompts (`dontAsk`), an ask
becomes a block.

---

## 1. Approval guard: Slurm and gh

Enforces cluster.md rule 1 (no job submission without a yes) and the gh rule in
workflow.md. Any Bash command containing `sbatch`, `srun`, `salloc`, or `gh` as
a word triggers a permission prompt for jarl.

Merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; cmd=$(jq -r '.tool_input.command // empty'); if printf '%s' \"$cmd\" | grep -qwE 'sbatch|srun|salloc'; then printf '%s' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"cluster.md rule 1: job submission needs jarl approval\"}}'; fi"
          },
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; cmd=$(jq -r '.tool_input.command // empty'); if printf '%s' \"$cmd\" | grep -qwE 'gh'; then printf '%s' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"workflow.md: gh needs jarl approval\"}}'; fi"
          }
        ]
      }
    ]
  }
}
```

Notes:

- The guard matches the words anywhere in the command, so
  `cd work && sbatch job.sh` is caught. A permission rule like `Bash(sbatch *)`
  checks only the leading command; do not replace the hook with one.

---

## 2. Lint guard: ruff and ty on every Python edit

Enforces the linter rule in code-style.md section 1. After every edit to a `.py`
file, ruff and ty run on that file, and findings come back to the model as a
blocking error. No auto-formatting: the hook only reports.

Merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; f=$(jq -r '.tool_input.file_path // empty'); case \"$f\" in *.py) r=$(uvx ruff check --no-cache --output-format concise \"$f\" 2>&1); rok=$?; t=$(uvx ty check --project \"$(dirname \"$f\")\" --output-format concise \"$f\" 2>&1); tok=$?; if [ \"$rok\" -ne 0 ] || [ \"$tok\" -ne 0 ]; then [ \"$rok\" -ne 0 ] && printf '%s\\n' \"$r\" >&2; [ \"$tok\" -ne 0 ] && printf '%s\\n' \"$t\" >&2; exit 2; fi ;; esac"
          }
        ]
      }
    ]
  }
}
```

Notes:

- Missing `uv` fails loudly through the tool calls themselves.
- Both tools always run, and only failing output is reported.
- ruff resolves the nearest config, so the project's own `ruff.toml` applies;
  without one, ruff defaults apply.
- Keep ty's `--project` flag: it finds the file's project venv from any cwd,
  where `uv run` would hide it behind an overlay env.

---

## 3. Language guard: Vale on every markdown edit

Enforces language.md. After every edit to a `.md` file, Vale runs on it using
the nearest `.vale.ini` found upward from the file, and findings come back as a
blocking error. With no `.vale.ini` above the file, the file passes unchecked.

Merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; f=$(jq -r '.tool_input.file_path // empty'); case \"$f\" in *.md) d=$(cd \"$(dirname \"$f\")\" && pwd); cfg=\"\"; while :; do { [ -e \"$d/.vale.ini\" ] || [ -L \"$d/.vale.ini\" ]; } && { cfg=\"$d/.vale.ini\"; break; }; [ \"$d\" = \"/\" ] && break; d=$(dirname \"$d\"); done; [ -n \"$cfg\" ] || exit 0; command -v vale >/dev/null || { echo 'hook: vale missing; install per language.md section 4' >&2; exit 2; }; out=$(vale --config \"$cfg\" --output line \"$f\" 2>&1) || { printf '%s\\n' \"$out\" >&2; exit 2; } ;; esac"
          }
        ]
      }
    ]
  }
}
```

Notes:

- The Vale style reaches a project through setup.md section 2.
- Missing `vale` fails after the edit with an install message. A dangling
  `.vale.ini` symlink fails with Vale's own error: re-run the `ln` line in
  setup.md section 2.

---

## 4. Reporting guard: no stopping with unwritten results

Enforces reporting.md rule 11. The first attempt to end a turn is blocked with a
reminder to write unwritten results to the report or its inbox; the second goes
through (`stop_hook_active`). This guard is per project: install it only in
projects that produce results.

Merge into the project's `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; a=$(jq -r '.stop_hook_active // false'); [ \"$a\" = \"true\" ] && exit 0; printf '%s' '{\"decision\":\"block\",\"reason\":\"rule 11 (reporting.md): write any unwritten results now. If none, say: nothing to report.\"}'"
          }
        ]
      }
    ]
  }
}
```

Notes:

- The bounce fires whether or not results were produced; the agent judges.

---

## 5. Secrets guard: no reading or printing secrets

Enforces the secrets rule in workflow.md section 2. Any Bash command, Read, or
Grep whose input names a secret-holding file (`.env` and `.envrc` files,
`.secrets*`, ssh private keys, cloud credentials) or a secret-shaped variable,
or dumps the environment with a bare `env`, `printenv` or `set`, is denied, with
no approval case. One command passes: `has_secret` with variable names and
nothing else on the line.

Merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Read|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; in=$(cat); cmd=$(printf '%s' \"$in\" | jq -r '.tool_input.command // empty'); if printf '%s' \"$cmd\" | grep -qE '^has_secret( [A-Za-z_][A-Za-z0-9_]*)+$'; then exit 0; fi; t=$(printf '%s' \"$in\" | jq -r '.tool_input | tostring'); if printf '%s' \"$t\" | grep -qE '\\.env(rc)?([^A-Za-z0-9]|$)|\\.secrets|id_rsa|id_ed25519|id_ecdsa|\\.aws/credentials'; then echo 'secrets guard (workflow.md section 2): never open or search a secrets file. To check that a secret is set: has_secret NAME' >&2; exit 2; fi; if printf '%s' \"$t\" | grep -qE '(API_KEY|_TOKEN|_SECRET|PASSWORD)([^A-Z0-9]|$)'; then echo 'secrets guard (workflow.md section 2): the input names a secret-shaped variable. To check that it is set: has_secret NAME' >&2; exit 2; fi; if printf '%s' \"$cmd\" | grep -qE '(^|[;&|(][[:space:]]*)(env|printenv|set)([[:space:]]*$|[[:space:]]*[|;&>])'; then echo 'secrets guard (workflow.md section 2): a bare env, printenv or set prints every variable, secrets included. To check that one is set: has_secret NAME' >&2; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

Notes:

- A guardrail against the accidental case, not a sandbox: a reworded command or
  an unusual file name can evade word matching. The companion fix is keeping
  secrets out of agent shells entirely: the shell rc sources `~/.secrets.env`
  only when `CLAUDECODE` is unset.
- Secret-shaped means `API_KEY`, `_TOKEN`, `_SECRET` or `PASSWORD` in uppercase
  at the end of a name, so `MAX_TOKENS` and `--max-tokens` pass.
- `has_secret` is `tools/has_secret.py`, linked into `~/.local/bin` by
  `tools/machine.py`. The exception is the whole command: a pipe, `;`, `&&`, a
  redirect or `$(...)` after it is denied.
- The pattern matches the whole tool input, so a Grep into a secret file is
  caught by its path.

---

## 6. Approval guard: destructive commands

Any Bash command matching a destructive pattern triggers a permission prompt for
jarl: recursive force delete (`rm -rf` and its flag variants),
`git reset --hard`, force push, piping a download into a shell
(`curl ... | sh`), and `chmod 777`.

Merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; cmd=$(jq -r '.tool_input.command // empty'); if printf '%s' \"$cmd\" | grep -qE 'rm -[a-zA-Z]*[rR][a-zA-Z]*f|rm -[a-zA-Z]*f[a-zA-Z]*[rR]|rm -[rR] -f|rm -f -[rR]|git reset --hard|git push [^|&;]*--force|git push [^|&;]*-f( |$)|(curl|wget) [^|]*\\| *(ba|z)?sh( |$)|chmod [^|&;]*777'; then printf '%s' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"destructive command: needs jarl approval\"}}'; fi"
          }
        ]
      }
    ]
  }
}
```

---

## 7. Lint guard: Vale and chktex on every LaTeX edit

Guard 3 for LaTeX. After every edit to a `.tex` file, Vale runs with the nearest
`.vale.ini` (whose `[*.tex]` section applies the language rules), then chktex
checks the LaTeX itself; findings from either come back as a blocking error.

Merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; f=$(jq -r '.tool_input.file_path // empty'); case \"$f\" in *.tex) d=$(cd \"$(dirname \"$f\")\" && pwd); cfg=\"\"; while :; do { [ -e \"$d/.vale.ini\" ] || [ -L \"$d/.vale.ini\" ]; } && { cfg=\"$d/.vale.ini\"; break; }; [ \"$d\" = \"/\" ] && break; d=$(dirname \"$d\"); done; [ -n \"$cfg\" ] || exit 0; command -v vale >/dev/null || { echo 'hook: vale missing; install per language.md section 4' >&2; exit 2; }; command -v chktex >/dev/null || { echo 'hook: chktex missing; install TeX Live' >&2; exit 2; }; out=$(vale --config \"$cfg\" --output line \"$f\" 2>&1) || { printf '%s\\n' \"$out\" >&2; exit 2; }; cout=$(chktex -q \"$f\" 2>&1) || { printf '%s\\n' \"$cout\" >&2; exit 2; } ;; esac"
          }
        ]
      }
    ]
  }
}
```

Notes:

- chktex runs with its defaults; project settings go in a `.chktexrc`.
- Failures behave as in guard 3; missing `chktex` also fails after the edit with
  an install message.

---

## 8. Settings: no commit or PR attribution

Enforces the no-AI-attribution rule in workflow.md section 1. Claude Code by
default appends attribution to commits and PRs, and carries built-in commit and
PR instructions; these settings turn both off.

Merge into `~/.claude/settings.json`:

```json
{
  "attribution": {
    "commit": "",
    "pr": "",
    "sessionUrl": false
  },
  "includeGitInstructions": false
}
```

The `attribution` object also goes, committed, into every project's
`.claude/settings.json`, for machines whose user settings lack it.

Notes:

- If commits get worse without Claude Code's built-in instructions, delete the
  `includeGitInstructions` line.
- `commit` is the co-author trailer and `pr` the "generated with" footer in PR
  bodies; both are strings, and the empty string hides them. `sessionUrl` is a
  boolean and `false` omits the session link trailer. Booleans for `commit` or
  `pr` fail settings validation.
- `includeCoAuthoredBy` is the deprecated older key; replace it with this object
  where found.

---

## 9. Approval guard: git commit and push

Enforces the git rule in workflow.md section 1. Any Bash command containing the
word `git` together with the word `commit` or `push` triggers a permission
prompt for jarl. Other git commands pass.

Merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; cmd=$(jq -r '.tool_input.command // empty'); if printf '%s' \"$cmd\" | grep -qw git && printf '%s' \"$cmd\" | grep -qwE 'commit|push'; then printf '%s' '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"workflow.md: committing or pushing needs jarl approval\"}}'; fi"
          }
        ]
      }
    ]
  }
}
```

Notes:

- The two-word match catches `cd x && git commit` and `git -C dir push`; a
  command like `git log --grep commit` also triggers it.
- The prompt appears even when jarl asked for the commit in the same turn.

---

## 10. Attribution guard: no AI trailer in commits

Enforces the no-AI-attribution rule in workflow.md section 1 where the settings
in section 8 are missing or ignored. A `git commit` command whose text carries a
Claude co-author trailer, a "generated with" line, or a session link is denied.

Merge into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; cmd=$(jq -r '.tool_input.command // empty'); if printf '%s' \"$cmd\" | grep -qw git && printf '%s' \"$cmd\" | grep -qw commit && printf '%s' \"$cmd\" | grep -qiE 'co-authored-by: *claude|noreply@anthropic\\.com|generated with \\[claude|claude-session:'; then echo 'attribution guard (workflow.md): no AI attribution in commits; remove the trailer and commit again' >&2; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

Notes:

- It reads the command text only. A message passed through a file
  (`git commit -F`) is not seen.
