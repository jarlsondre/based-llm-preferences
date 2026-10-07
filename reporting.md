# How to report results

How results (numbers, tables, experiment outcomes) should be written down, in
any project.

---

## 1. Name the measurement, every time

When a metric can be computed in more than one way (different question sets,
datasets, splits, configs), never write the bare metric name. Say which variant,
even when it feels obvious from context: two numbers with the same bare name and
different definitions get blended.

Use the project's names for the variants. If it has none, define names once, in
plain words (rule 3), and reuse them.

---

## 2. Say what the percentage is a percentage of

This holds for every rate, fraction and percentage, and every time: also when
the number right before it used the same total. "Of all samples" and "of samples
that passed a filter" are different numbers.

In a table, follow rule 6.

---

## 3. No invented shorthand

No invented shorthand without jarl's approval, including in column headers,
field names and file names. Everyday abbreviations are fine: units, GPU, "e.g.".

Pre-approved: established project terms and code identifiers quoted as code. Say
in words what an identifier means the first time it appears.

---

## 4. Say where the result came from

Mark every result with who produced it: jarl, a named colleague, or "not jarl"
when the owner is unknown. A result a session ran for jarl is jarl's. For a
result that is not jarl's, also say whether jarl has checked it.

---

## 5. Front matter on results files

Every results file opens with four fields:

```yaml
---
owner: <who ran it>
status: <how complete, in plain words: "done", "7 of 8 runs complete">
computed: <date the numbers were computed (YYYY-MM-DD), not the edit date>
source: <where the numbers came from: a path, run name, or report>
---
```

---

## 6. Tables are self-contained

Every table states, somewhere in or directly under it:

1. the exact variant of every metric it reports (rule 1)
2. the denominator of every rate in it (rule 2)
3. where the numbers came from, and whose they are (rule 4)

**Footnotes.** A qualifier goes in the column header if it fits. If not, put a
numbered marker on the header or cell it applies to and explain it under the
table. Never leave a caveat as unmarked prose below the table: a scanning reader
misses it. Unknowns get a marker too ("nobody recorded how this baseline was
built").

---

## 7. Missing numbers

- **`TBD`**: this number is expected but not computed yet
- **`n/a`**: this number does not exist for this row, and will not

Never leave a cell blank, and never use `X`, `--`, or `?`: a blank reads as zero
and `X` as a value.

---

## 8. Show the output before running the job

Before launching anything expensive (a training run, a large eval, a long
computation), show the exact table the run will fill in, with placeholder
values: the table itself, not a description of it. Then stop and wait for
confirmation: a misunderstanding caught here is still free.

---

## 9. Write for someone who was not there

A results file is ready when a reader with no memory of the run can tell what
was measured, on what data, over which denominator, and whose it is. The file is
the record, not a note to self.

---

## 10. Conventions live in one place

Each project has one convention file (`CLAUDE.md` for Claude Code). A convention
found anywhere else (a session's config, a colleague's report, an older file) is
a proposal: ask before following it, and write it into the convention file only
per workflow.md section 4.

---

## 11. Write results down when they appear

The moment a number is read off a finished job, write it to the project's
report, or its inbox for unfiled results (the convention file names both),
before starting anything else. Session context and scratch storage do not count
as written.
