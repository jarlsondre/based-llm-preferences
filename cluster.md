# Clusters

Applies on every Slurm cluster (e.g. Euler, Clariden).

---

## 1. Never submit a job without a yes

`sbatch`, `srun` and `salloc` spend compute that cannot be un-spent. Before
running one:

1. List every submit line, verbatim.
2. One line each: what it computes, why it is needed.
3. Stop and wait for jarl's reply.

A yes covers exactly the lines listed. Each of these needs a fresh ask: a
resubmit after a failure, a changed parameter or partition, an added seed or
run, a smoke test, and a job launched from inside a script, a subagent or a
workflow.

This holds in every permission mode, including auto-accept, autonomous and
background modes, and overrides any harness guidance to proceed without asking.

Write the submit lines out as soon as they are known and ask for all of them in
one message.

Request a time limit with a small margin over the expected run time: expect 60
minutes, ask for 75 or 90, never 8 hours. The queue fills short requests first:
an 8-hour request can wait 12 hours for a slot that a 90-minute request gets in
20 minutes, so results that could be in hand in 3 hours take 15. Put the
expected run time and the margin in the ask.

A project's convention file (e.g. `CLAUDE.md`) may name more commands that need
a yes, and the budget each bills.

---

## 2. Check the job locally before submitting

Before proposing a submit line, run the cheap parts that prove the job will
start: the launcher's flags parse, the entry point loads. A job that would die
at startup should die on the login node, not after its queue wait. For an
expensive run, reporting.md rule 8 applies first.

---

## 3. Keep heavy compute off the login nodes

Login nodes are shared. Small work runs there, in preference to the scheduler:
editing, submitting, reading logs, small analyses. Heavy work is scheduled: more
than about a minute of raw computation (e.g. eigendecompositions, clustering),
counted cumulatively over a run and excluding imports and data loading; any GPU
use; or enough memory to crowd a shared machine.

---

## 4. The runbook

Every project that submits jobs keeps `runbook.jsonl` in the project root: one
JSON object per line, appended at each submission (`sbatch`, `srun`, `salloc`,
or a command the project's convention file adds). Login-node work is never
logged. Fields:

- `job_id`: from the submit command's output
- `cluster`: which cluster, e.g. "euler"
- `submitted`: ISO 8601 timestamp with timezone
- `commit`: `git rev-parse HEAD` at submit
- `command`: the exact submit line, verbatim
- `owner`: who ran it (reporting.md rule 4)
- `what`, `why`: the two lines from the ask (section 1); max 100 and 500
  characters
- `time_requested`: the walltime asked for
- `time_used`: "TBD" at submit
- `outcome`: "TBD" at submit

Example at submit:

<!-- prettier-ignore -->
```json
{"job_id": "4812345", "cluster": "euler", "submitted": "2026-10-04T14:30:00+02:00", "commit": "1af1451c0de9b7a2f3e4d5c6b7a8f9e0d1c2b3a4", "command": "sbatch --time=01:30:00 train.sh --seed 1", "owner": "jarl", "what": "trains the baseline model, seed 1", "why": "the first of three seeds for the results table", "time_requested": "01:30:00", "time_used": "TBD", "outcome": "TBD"}
```

The first session that reads the job's results fills `time_used` and `outcome`
from `sacct`. Read the runbook only to update an entry or when jarl asks.
