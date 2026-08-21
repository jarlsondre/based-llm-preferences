# Language

How to write. These rules apply everywhere: responses, files, column
headers, code comments.

---

## 1. Write plain

Writing exists to transfer meaning. Plain writing transfers it faster,
with no loss of precision. Overly complicated vocabulary and convoluted
sentences are what mid writing looks like; good writers say the thing
directly. Use precise terms where they belong and simple words
everywhere else.

Plain:

> We tested whether plants grow faster under blue or red light. After
> four weeks, the blue-light plants had grown 12 cm on average and the
> red-light plants 8 cm.

Not plain:

> The purpose of this experimental investigation was to ascertain
> whether the utilization of blue versus red light wavelengths would
> facilitate differential rates of botanical growth. Over a four-week
> temporal period, the specimens subjected to blue light conditions
> exhibited an average vertical elongation of 12 cm.

The second version adds words and removes clarity. These are the
mechanisms that produce it, and each one is banned:

| mechanism | don't write | write |
|---|---|---|
| fancy synonym | utilize, ascertain, facilitate | use, find out, help |
| nominalization | exhibited vertical elongation | grew |
| passive evasion | it was observed that | we saw |
| throat-clearing | it should be noted that | (nothing) |

---

## 2. Banned patterns

**Em-dashes.** Never. Use a comma, a colon, parentheses, or two
sentences. The character reads as AI text before the sentence is even
read, and every use has a cheap replacement.

**"Not A, but B" as a flourish.** Contrast is allowed only against
something the reader might actually believe. "The date the numbers
were computed, not the edit date" corrects a real assumption and is
fine. "It's not just a tool, it's a paradigm" argues with nobody. The
test: if dropping the "not A" clause loses no information, drop it.

**Emojis.** Never.

**Filler.** No sycophantic openers ("Great question!"). No summary
paragraphs that restate what was just said. No transitions that carry
no content ("Furthermore,"). End when done.

**Hype adjectives.** No "robust", "seamless", "blazingly fast",
"powerful". Say what the thing does; the reader decides whether it is
impressive.

**Rule-of-three padding.** "Fast, reliable, and scalable" is a triplet
where one word was the point. Say the one word.

**Bullet-point inflation.** Do not chop prose into bullets with bolded
lead-ins to look organized. Bullets are for lists.

**Unearned hedging.** No "should probably work", no "arguably". Either
check it or state the uncertainty precisely: "untested", "holds for
n < 100".

---

## 3. Banned words

Most of these are metaphors standing in for a concrete thing. Name the
thing. A banned word may be used only when it is literally the subject
at hand (a real clinical treatment, an actual organism).

| don't write | write |
|---|---|
| organism | the model itself, named: "the bad-medical model" |
| treatment (arm) | what was picked, named: "top 6,000 by score" |
| control (arm) | the comparison rows |
| lever | the actual mechanism or intervention, named |
| delve | look into, examine |
| leverage (as a verb) | use |
| utilize | use |
| crucial, pivotal | important, or say why it matters |
| robust, seamless | say what it handles |
| comprehensive | say what it covers |
| landscape, journey | name the thing |
| deep dive | name the analysis |

The first four came from the emergent-misalignment project, where
borrowed biology and clinical-trial words obscured what was actually
done. The ban is general.
