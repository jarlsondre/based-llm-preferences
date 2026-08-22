# How to report results

How results (numbers, tables, experiment outcomes) should be written
down, in any project.

---

## 1. Name the measurement, every time

When a metric can be computed in more than one way (different question
sets, datasets, splits, configs), never write the bare metric name. Say
which variant, even when it feels obvious from context. Two numbers with the same bare name and different definitions
are the classic way results get blended.

If the project has short canonical names for the variants, use those.
If it does not, invent them once, define them once, and use them
consistently.

---

## 2. Say what the percentage is a percentage of

A percentage is meaningless without its denominator. This holds for any
rate, fraction, or percentage. Two denominators that sound similar can
differ wildly (e.g. "of all samples" vs. "of samples that passed a
filter"), and the difference can be larger than the effect being
reported.

Put the denominator in the column header when it fits. When it needs a
longer explanation, put a numbered marker in the header and explain it
under the table. What matters is that every rate points at its
denominator somewhere. A bare rate with nothing pointing anywhere is
not acceptable.

If a number is quoted from an older source that only survives on one
denominator, say so.

---

## 3. Write plain words

No abbreviation is used without jarl's approval: not in column
headers, not in field names, not in file names. Shorthand only costs
the reader.

Pre-approved: names that are already the real name of the thing,
meaning established project terms and code identifiers quoted as code. When
quoting a code identifier, say in words what it means the first time it
appears.

**No borrowed jargon.** Do not describe work with words borrowed from
another field (e.g. "treatment arm" / "control arm" from clinical
trials) when plainer words say what was actually done. Better still,
name the selection itself: "top 6,000 by score" says what was done;
"treatment" makes the reader look it up. Banned words are listed in
[language.md](language.md).

---

## 4. Say where the result came from

Every result is marked with who produced it: jarl, a named colleague,
or "not jarl" when the owner is unknown. An unknown owner is never a
reason to leave a result unmarked.

For anything that is not jarl's, say also whether it has been checked.
The reader must never have to guess whether a number is jarl's.

---

## 5. Front matter on results files

Every results file opens with four fields:

```yaml
---
owner: <who ran it>
status: <how complete, in plain words: "done", "7 of 8 runs complete">
computed: <date the numbers were computed, not the edit date>
source: <where the numbers came from: a path, run name, or report>
---
```

---

## 6. Tables are self-contained

Every table states, somewhere in or directly under it:

1. the exact variant of every metric it reports (rule 1)
2. the denominator of every rate in it (rule 2)
3. where the numbers came from, and whose they are (rule 4)

**Footnotes.** A qualifier goes in the column header if it fits. If
not, put a numbered marker on the header or cell it applies to and
explain it under the table. Never leave a caveat as loose prose below:
a reader scanning the table will take the number at face value and miss
it. A marker is also how a table admits what it does not know ("nobody
recorded how this baseline was built").

---

## 7. Missing numbers

Two markers, with different meanings:

- **`TBD`**: this number is expected but not computed yet
- **`n/a`**: this number does not exist for this row, and will not

Never leave a cell blank. Never use `X`, `--`, or `?`. A blank reads as
zero to a tired human and to a machine, and `X` reads as a value.

---

## 8. Show the output before running the job

Before launching anything expensive (a training run, a large eval, a
long computation), show the exact table the run will fill in, with
placeholder values: the table itself, not a description of it.
Then stop and wait for confirmation. This is where misunderstandings
get caught while they are still free.

---

## 9. Write for someone who was not there

A results file is ready when a reader with no memory of the run can
tell what was measured, on what data, over which denominator, and whose
it is. If that means repeating context that felt obvious while the run
was fresh, repeat it. The file is the record, not a note to self.

---

## 10. Conventions live in one place

Each project has one file that is the source of truth for its
conventions. A rule found anywhere else (a session's config, a
colleague's report, a habit in an older file) is a proposal until it
is written there. Propose the change, wait, then edit that file. Do not
follow a convention from a file you did not write without asking first.
