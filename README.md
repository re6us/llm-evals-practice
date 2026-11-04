# LLM Classification with Evals

A small project built to learn how to measure the quality of LLM
classification, rather than just eyeballing the output.

It grew in two stages. The first measured accuracy against a hand-labelled
reference set and ran into a ceiling. The error analysis argued the ceiling
was a specification problem rather than a prompt-wording problem. The second
stage tested that claim and measured the result.

## What it does

Collects the top 100 Hacker News stories and classifies the first 50 by
topic using Claude. The classifier is an agent: it has two tools and decides
for itself whether the headline is enough to answer or whether it needs to
open the page first.

Quality is measured two ways — against hand labels, and by running the same
prompt twice over the same data to see where the answers move.

## Structure

| Script | Purpose |
|---|---|
| `hn.py` | Fetches top 100 HN stories into `posts.csv` (title, score, comments, published, url) |
| `make_golden.py` | Exports headlines into `golden.csv` for manual labelling |
| `classify.py` | Sends each headline to Claude, writes labels to `posts_classified.csv` |
| `evaluate.py` | Compares model labels against the reference set, reports accuracy and writes mismatches to `errors.csv` |
| `classify_v3.py` | Agent version: tool use, page fetching, agent loop with three exit conditions and a step limit |
| `fetch_page.py` | Extracts page text with BeautifulSoup |
| `compare.py` | Compares two result files and reports agreement between them |
| `findings.md` | Full error analysis for the agent version |

## Stage 1 · Accuracy against hand labels

Five prompt iterations: **70% → 75% → 73% → 74% → 75%**

Accuracy plateaued around 75%. Prompt changes shifted *which* headlines
were misclassified, but not how many.

### Error analysis

Reviewing the 25 mismatches surfaced four distinct problems:

**1. Missing categories (15 headlines).** While labelling by hand I kept
writing notes like `society`, `design`, `gaming` next to headlines I had
forced into `Other`. The category scheme didn't fit the data. Adding
`Society` and `Design` helped, but introduced new boundary disputes.

**2. Subject vs audience.** `ESP32-C3 Adblock` — Hardware or Programming?
The model classified by subject matter, I classified by who reads it.
Neither is wrong; the instruction simply didn't say which to use.

**3. AI vs application domain.** `Sharing AI progress in mathematics` —
AI or Science? Notably, the model and I swapped positions across similar
headlines, meaning neither of us had a consistent rule.

**4. Genuinely ambiguous headlines.** `Mallet Head Angle`, `Berthd` — not
enough information in the title to classify at all. These will always
fail.

One iteration dropped accuracy to 73% because the prompt contained a
direct contradiction: a rule said "AI applied to maths → AI" while an
example said the opposite. Worth noting that prompts accumulate conflicts
as they grow.

### The claim this produced

> The remaining errors aren't a prompt problem — they're a specification
> problem. Further improvement requires defining what each category
> actually means and where the boundaries sit, not rewording instructions.

Stage 2 tests it.

## Stage 2 · Agent version, and testing the claim

### Tool use

`classify_v3.py` gives the model two tools: one to save a classification
against a JSON schema, one to fetch the text of a page. Schema-constrained
output removed a class of failure outright — the earlier version parsed JSON
out of free text and lost 7 of 50 rows to malformed output, most often a
trailing comma. With tool use, 0 of 50.

Fetching changes answers rather than decorating them. `A story of WiFi
secrets, UART lockdowns and a damaged flash memory chip` is a write-up about
a Eufy doorbell, which the headline does not say and the page does.

### Agent loop

Written by hand, without a framework, so the mechanics are visible:

```
ask the model
  ↓
model answers
  ↓
model asked for a tool?  →  run it, return the result  →  back to the top
  ↓
classification arrived   →  done
```

Three exit conditions: the classification arrived, the model answered in
plain text and wants no tools, or the step limit was hit. The step limit is
the first of the guardrails and exists because a loop without a brake bills
until someone notices.

The loop earns its keep on headlines that need two sources.
`How to Formalize All of Mathematics` was classified on the third pass: the
model read the discussion thread, found a link to the original site, read
that, and only then answered.

### Measuring self-consistency

Accuracy needs labels, and labels go stale — `golden.csv` stopped matching
the corpus as soon as `posts.csv` was regenerated from a fresh front page.

Self-consistency needs none. Run the same prompt twice over the same data:
every headline where the two runs disagree is a headline where the task left
the model a choice. The disagreement list is not a list of bugs. It is a
pointer at what the specification failed to say.

The first thing it showed was about the measurement, not the model:

| Prompt | Pair 1 | Pair 2 | Mean |
|---|---|---|---|
| Categories named, not defined | 96% | 90% | **93%** |
| Categories defined | 98% | 98% | **98%** |

Two pairs of runs of the *same* prompt disagreed by 6 points. A single
measurement could not have separated an improvement from luck, so every
figure here is the mean of two independent pairs.

### What the fix was

The earlier prompt listed nine category names and defined none of them. The
model inferred that the taxonomy was for technical subjects and routed
everything else to `Other`, writing justifications like "not tech, fits no
specific topic" while `Society` sat unused in the list.

The new prompt gives each category a one-line definition, states that
`Other` is a last resort, and says explicitly that being non-technical is
not a reason to choose it.

Six headlines that flipped between runs are now stable:

```
Stolen Renoir paintings found behind a wall
Woman who rescued injured crow
The Economic Complexity of the Western Roman Empire
What on Earth Is Dekton?
Tesla Roadster
Bark: The Toll-Free BBS for 90s Teens
```

The last two had been unstable under both baseline pairs and were written
off as questions with no determinate answer. They were questions the prompt
had not answered.

### What remains, and why it is a different defect

One disagreement survived in each pair:

```
pair 1   How to Formalize All of Mathematics
         read the HN thread only     →  Programming
         read the original site too  →  AI

pair 2   RFC8950: Announce IPv4 with an IPv6 next-hop
         classified from the headline  →  Programming
         read the linked page         →  Hardware
```

Neither is a wording problem. The two runs read different amounts of
material and answered honestly from what they had. The model decides for
itself whether the headline is enough, so the trajectory varies and the
answer follows it.

Specification ambiguity is closed. What is left is retrieval
non-determinism, and it has a different fix: fetch always, fetch never, or
cache and reuse.

### Cost of the change

| | Page fetches per 50 headlines |
|---|---|
| Before | 12 |
| After | 18 |

Definitions made the model more cautious: it looks for evidence more often
instead of deciding from the headline. Roughly 50% more page requests, more
tokens, longer runs. Five points of consistency for that spend is a trade,
not a win; whether it is worth taking depends on what an error costs.

### Cost, measured

A full run over 50 headlines: 118,072 input tokens, 10,843 output,
$0.34 at Sonnet 5.5 pricing. 18 headlines needed a page fetch; those cost
2.2× the ones answered from the title alone.

84% of all input tokens are the prompt itself, re-sent on each of the 68
requests. Caching the fixed part of the prompt should roughly halve the
run, which is the next thing worth doing.

Four rows were flagged `needs_review` — low confidence or a failed
classification — so a human looks at four lines instead of fifty.

## Limits of these numbers

**Self-consistency is necessary, not sufficient.** A prompt can be perfectly
stable and stably wrong. The claim here is that the answers stopped moving,
not that they became correct. Accuracy for the new prompt is unmeasured,
because the reference set needs relabelling against the current corpus.

**Latency is uninstrumented.** Tokens and money are counted per headline;
wall-clock time is not, so there is no figure for how long a run takes or
where it waits.

**No retries.** A rate-limit or overload response ends that headline rather
than waiting and trying again, so a run during a busy period would show
failures that are not really failures.

## Method notes

**Verify the input before explaining the output.** The first measurement of
the new prompt came out *worse* than baseline — 90% against 96% — and
produced a plausible theory about why. The file had not been saved. The
prompt under test was still the old one. Every run now prints a
`PROMPT_VERSION` line.

**Few-shot examples must not come from the evaluation set.** Using the
disputed headlines themselves as examples would have guaranteed correct
answers on exactly the rows being measured.

**Key comparisons by content, not position.** `golden.csv` was keyed by row
order and broke silently when the corpus was regenerated. `compare.py` keys
by headline.

**A guardrail that has never fired is untested.** The escalation flag read
zero on a five-row run, which proves nothing. It was only confirmed working
once a full run produced four flagged rows.

## Takeaway

The hand-labelling was the most useful part of stage 1: it exposed questions
about the task that weren't visible until I had to answer them 100 times.

Stage 2's equivalent was the disagreement list. Both work the same way —
they turn "the output looks a bit off" into a specific sentence the
specification is missing.