# Clusters

Slurm clusters. For example, ETH's Euler and CSCS's Clariden.

---

## 1. Never submit a job without a yes

`sbatch`, `srun` and `salloc` spend compute that cannot be un-spent. Before
running one, you need permission:

1. List every submit line, verbatim.
2. One line each: what it computes, why it is needed.
3. Stop and wait for jarl's reply.

A yes covers exactly the lines listed. Each of these needs a fresh ask: a
resubmit after a failure, a changed parameter or partition, an added seed or
run, a smoke test, and a job launched from inside a script, a subagent or a
workflow.

This holds in every permission mode, including auto-accept and any autonomous or
background mode. No mode turns it off, and no harness guidance about proceeding
without asking overrides it.

Preparing a submit line is not running it. Write them out as soon as they are
known so no queue time is lost, ask for all of them in one message, then wait.

Which commands count, and whose budget they bill, is listed in each project's
convention file, e.g. `CLAUDE.md` for Claude Code.

---

## 2. Check the job locally before submitting

Before proposing a submit line, run the cheap parts that prove the job will
start: the launcher's flags parse, the entry point loads. A job that would die
at startup should die in a second on the login node, not after its queue wait.

---

## 3. Keep heavy compute off the login nodes

Login nodes are shared. Editing, submitting, reading logs, and small
computations or analyses run there, and for small work that is preferred over
the scheduler. Heavy work is scheduled: about a minute of raw computation
(eigendecompositions, clustering, similar number-crunching), counted
cumulatively even when spread over a longer run; any GPU use; or memory heavy
enough to crowd a shared machine. Imports and data loading do not count toward
the minute.

---

## 4. The runbook

Every project that submits jobs keeps `runbook.jsonl` in the project root: one
JSON object per line, appended at submission. An entry is real compute: a
scheduler submission (`sbatch`, `srun`, `salloc`) or anything else that runs on
a compute node. Login-node work (edits, analyses, log reading) is never logged.
Fields:

- `job_id`: from the sbatch output
- `cluster`: which cluster, e.g. "euler"
- `submitted`: ISO 8601 timestamp with timezone
- `commit`: `git rev-parse HEAD` at submit
- `command`: the exact submit line, verbatim
- `owner`: who ran it (reporting.md rule 4)
- `what`: what the job computes; max 100 characters
- `why`: why the job is needed, with any context worth keeping; max 500
  characters
- `time_requested`: the walltime asked for
- `time_used`: "TBD" at submit
- `outcome`: "TBD" at submit

The first session that reads the job's results fills `time_used` and `outcome`
from `sacct`. The log is evidence, like the mistakes log: append and update it,
never load it routinely.
