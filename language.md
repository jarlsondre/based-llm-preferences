# Language

These rules apply to all writing: responses, files, column headers, code
comments.

---

## 1. Write plain

Plain writing transfers meaning faster with no loss of precision. Say the thing
directly: precise terms where they belong, simple words everywhere else.

Plain:

> We tested whether plants grow faster under blue or red light. After four
> weeks, the blue-light plants had grown 12 cm on average and the red-light
> plants 8 cm.

Not plain:

> The purpose of this experimental investigation was to ascertain whether the
> utilization of blue versus red light wavelengths would facilitate differential
> rates of botanical growth. Over a four-week temporal period, the specimens
> subjected to blue light conditions exhibited an average vertical elongation of
> 12 cm.

Banned mechanisms:

| mechanism       | don't write                    | write               |
| --------------- | ------------------------------ | ------------------- |
| fancy synonym   | utilize, ascertain, facilitate | use, find out, help |
| nominalization  | exhibited vertical elongation  | grew                |
| passive evasion | it was observed that           | we saw              |
| throat-clearing | it should be noted that        | (nothing)           |

---

## 2. Banned patterns

**Em-dashes.** Never: the character reads as AI text. Use a comma, a colon,
parentheses, or two sentences. Also banned as substitutes: an en-dash, `--`, or
`---` standing in for an em-dash. An en-dash in a range (6–7, pages 20–31) is
fine.

**"Not A, but B" as a flourish.** Contrast is allowed only against something the
reader might believe. "The date the numbers were computed, not the edit date"
corrects a real assumption and is fine. "It's not just a tool, it's a paradigm"
argues with nobody. The test: if dropping the "not A" clause loses no
information, drop it.

**Emojis.** Never.

**Filler.** No sycophantic openers ("Great question!"). No summary paragraphs
that restate what was just said. No transitions that carry no content
("Furthermore,").

**Teasers.** No withheld payoff: "and one of them is unexpected", "the third
will surprise you". Say the information on the spot or cut the sentence. A
signpost that states structure ("three findings:") is fine.

**Performed feelings.** No "I'm excited to", "I love this", "happy to help". No
"I prefer X": recommend with the reason, "I recommend X, because...".

**Hype adjectives.** No "robust", "seamless", "blazingly fast", "powerful". Say
what the thing does; the reader judges.

**Rule-of-three padding.** "Fast, reliable, and scalable" is a triplet where one
word was the point: say the one word. Three real items are a list and fine.

**Bullet-point inflation.** Do not chop prose into bullets with bolded lead-ins
to look organized. Bullets are for lists.

**Unearned hedging.** No "should probably work", no "arguably". Either check it
or state the uncertainty precisely: "untested", "holds for n < 100".

---

## 3. Banned words

Name the concrete thing, never a metaphor or a term borrowed from another field.
These words are banned outright, except where one is the literal subject (an
actual organism, a real trial arm). In a file, wrap that passage in
`<!-- vale jarl.BannedWords = NO -->` and
`<!-- vale jarl.BannedWords = YES -->`.

| don't write        | write                                            |
| ------------------ | ------------------------------------------------ |
| organism           | the model itself, named: "the bad-medical model" |
| treatment arm      | what was picked, named: "top 6,000 by score"     |
| control arm        | the comparison rows                              |
| arm, arms          | name the group: which runs, which selection      |
| lever              | the actual mechanism or intervention, named      |
| delve              | look into, examine                               |
| leverage           | use                                              |
| utilize            | use                                              |
| crucial, pivotal   | important, or say why it matters                 |
| robust, seamless   | say what it handles                              |
| comprehensive      | say what it covers                               |
| landscape, journey | name the thing                                   |
| deep dive          | name the analysis                                |
| tranche            | batch, part, or the number                       |
| ascertain          | find out                                         |
| facilitate         | say what it does: help, enable, make possible    |
| powerful           | say what it does                                 |
| blazingly fast     | say how fast                                     |

---

## 4. Enforcement

Vale (`.vale.ini`, `styles/`) checks the bans a pattern can match; prettier
(`.prettierrc`) wraps prose at 80 columns. Both must pass, and passing does not
prove compliance: apply the remaining rules yourself, in files and in every
response. When a ban changes here, change the Vale style too.

In any project:

1. `vale` missing: on macOS, `brew install vale`. Elsewhere, download the
   release tarball for the machine's architecture from Vale's GitHub releases
   and put the `vale` binary on PATH (`~/.local/bin`). Never sudo.
2. Before the first vale call, check the project's `.vale.ini`: if it is missing
   or a dangling symlink, run the `ln` line in [setup.md](setup.md) section 2.
3. After writing markdown or LaTeX: run `vale <file>`; for markdown also
   `npx --yes prettier --write <file>`. Fix every finding before presenting.

In Claude Code, guards 3 and 7 in [hooks.md](hooks.md) run Vale on every
markdown and LaTeX edit; prettier stays manual.
