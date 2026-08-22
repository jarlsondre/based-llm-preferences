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

## 2. Do not compute on a login node

Login nodes are for editing, submitting, and reading logs. Anything that
computes goes through the scheduler, quick checks included.
