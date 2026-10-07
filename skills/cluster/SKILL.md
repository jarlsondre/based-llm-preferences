---
name: cluster
description:
  "Rules and tools for Slurm clusters (Euler, Clariden): asking before every job
  submission, requesting a tight time limit, keeping compute off login nodes,
  and logging every job in the runbook. Use when working on a cluster or when a
  command mentions sbatch, srun, salloc or Slurm."
compatibility:
  "Requires uv. The runbook tool reads sacct and scontrol on the cluster."
---

# Clusters

Applies on every Slurm cluster (e.g. Euler, Clariden). `${CLAUDE_SKILL_DIR}` is
the folder this file is in; where it shows as literal text, put the path in its
place.

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

Every project that submits jobs keeps `runbook.jsonl` in the project root, one
line per job, written only through the tool, never by hand. Login-node work is
never logged.

Right after a submission (`sbatch`, `srun`, `salloc`, or a command the project's
convention file adds), with the job id from its output:

```sh
uv run ${CLAUDE_SKILL_DIR}/scripts/runbook.py add JOB_ID --command "the submit line, verbatim" --what "..." --why "..."
```

`what` and `why` are the two lines from the ask (section 1), at most 100 and 500
characters. The tool fills the cluster, the timestamp, the commit, the owner
(`jarl`; `--owner` for someone else, reporting.md rule 4) and the time
requested, which it reads from `--time` in the command or takes from
`--time-requested`.

The first session that reads the job's results closes the entry:

```sh
uv run ${CLAUDE_SKILL_DIR}/scripts/runbook.py close JOB_ID --outcome "one line on what came out"
```

That fills `time_used` and the job's final state from `sacct`.

A wrong entry is fixed by running `add` again with the same job id: the fields
given replace the old ones. Read the runbook only to update an entry or when
jarl asks; `--help` on the tool has the fields.
