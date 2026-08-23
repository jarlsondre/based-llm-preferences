# Hooks

Mechanical guards for rules that must not depend on the model remembering prose.
This file is Claude Code specific.

**Instruction:** when working in a project that follows these preferences and a
guard below is missing from the project's `.claude/settings.json`, add it and
tell jarl.

---

## 1. Approval guard: Slurm and gh

Enforces cluster.md rule 1 (no job submission without a yes) and the gh rule in
workflow.md. Any Bash command containing `sbatch`, `srun`, `salloc`, or `gh` as
a word triggers a permission prompt for jarl.

Merge into `.claude/settings.json`:

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

- Missing `jq` blocks the command with an install message instead of silently
  disabling the guard.
- The guard matches the words anywhere in the command, so
  `cd work && sbatch job.sh` is caught. Permission prefix rules like
  `Bash(sbatch *)` check only the leading command and miss that form, which is
  why this is a hook.
- Hooks run in every permission mode. In a mode that never prompts (`dontAsk`),
  the ask becomes a block instead of a prompt.
- A false positive (the word appearing in an unrelated command) costs one extra
  prompt, never a silent allow.

---

## 2. Lint guard: ruff and ty on every Python edit

Enforces code-style.md rule 1 mechanically. After every edit to a `.py` file,
ruff and ty run on that file; findings are fed back to the model as a blocking
error, so it fixes them immediately instead of remembering to lint. No
auto-formatting: the hook only reports.

Merge into `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; f=$(jq -r '.tool_input.file_path // empty'); case \"$f\" in *.py) r=$(uvx ruff check --no-cache \"$f\" 2>&1); rok=$?; t=$(uvx ty check \"$f\" 2>&1); tok=$?; if [ \"$rok\" -ne 0 ] || [ \"$tok\" -ne 0 ]; then [ \"$rok\" -ne 0 ] && printf '%s\\n' \"$r\" >&2; [ \"$tok\" -ne 0 ] && printf '%s\\n' \"$t\" >&2; exit 2; fi ;; esac"
          }
        ]
      }
    ]
  }
}
```

Notes:

- Missing `jq` blocks the edit with an install message; missing `uv` fails
  loudly through the tool calls themselves.
- Both tools always run, and only failing output is reported.
- ruff resolves the nearest config, so the project's own `ruff.toml` applies;
  without one, ruff defaults apply.
- Non-Python files pass through untouched. Rust has no per-edit equivalent
  (clippy compiles the whole crate); run `cargo clippy -- -D warnings` per
  code-style.md instead.

---

## 3. Language guard: Vale on every markdown edit

Enforces language.md mechanically. After every edit to a `.md` file, Vale runs
on it using the nearest `.vale.ini` found upward from the file, and findings
come back as a blocking error.

Merge into `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; f=$(jq -r '.tool_input.file_path // empty'); case \"$f\" in *.md) d=$(cd \"$(dirname \"$f\")\" && pwd); cfg=\"\"; while :; do { [ -e \"$d/.vale.ini\" ] || [ -L \"$d/.vale.ini\" ]; } && { cfg=\"$d/.vale.ini\"; break; }; [ \"$d\" = \"/\" ] && break; d=$(dirname \"$d\"); done; [ -n \"$cfg\" ] || { echo 'hook: no Vale config found; run setup.md from the preferences repo' >&2; exit 2; }; command -v vale >/dev/null || { echo 'hook: vale missing; install per language.md section 4' >&2; exit 2; }; out=$(vale --config \"$cfg\" --output line \"$f\" 2>&1) || { printf '%s\\n' \"$out\" >&2; exit 2; } ;; esac"
          }
        ]
      }
    ]
  }
}
```

Notes:

- The Vale style lives in this repo; language.md section 4 says how to get it
  into a project.
- Every failure is loud and names its fix: missing `jq`, no Vale config, missing
  `vale`, and a dangling `.vale.ini` symlink all block the edit. Installing this
  hook is the opt-in; wherever it is installed, every markdown edit is either
  checked or fails with the fix named.

---

## 4. Reporting guard: no stopping with unwritten results

Enforces reporting.md rule 11. When the agent tries to end its turn, the hook
blocks it once with a reminder to write any results produced this session to the
report or its inbox. The second stop goes through (`stop_hook_active` guards the
loop), so the cost is one bounce per turn-end. Install in projects that produce
results.

Merge into `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "command -v jq >/dev/null || { echo 'hook: jq missing; install a static jq binary into ~/.local/bin (no sudo needed)' >&2; exit 2; }; a=$(jq -r '.stop_hook_active // false'); [ \"$a\" = \"true\" ] && exit 0; printf '%s' '{\"decision\":\"block\",\"reason\":\"reporting.md rule 11: if this session produced results not yet written to the report or its inbox, write them now, then stop.\"}'"
          }
        ]
      }
    ]
  }
}
```

Notes:

- The bounce fires whether or not results were produced; the agent judges. If
  the noise proves annoying, the refinement is grepping the transcript (the hook
  receives its path) for result-producing markers before bouncing.
