# LLM Classification with Evals

A small project built to learn how to measure the quality of LLM
classification, rather than just eyeballing the output.

## What it does

Collects the top 100 Hacker News stories, classifies each headline by
topic using Claude, and measures how often the model agrees with a
hand-labelled reference set.

## Structure

| Script | Purpose |
|---|---|
| `hn.py` | Fetches top 100 HN stories into `posts.csv` (title, score, comments, published) |
| `make_golden.py` | Exports headlines into `golden.csv` for manual labelling |
| `classify.py` | Sends each headline to Claude, writes labels to `posts_classified.csv` |
| `evaluate.py` | Compares model labels against the reference set, reports accuracy and writes mismatches to `errors.csv` |

## Results

Five prompt iterations: **70% → 75% → 73% → 74% → 75%**

Accuracy plateaued around 75%. Prompt changes shifted *which* headlines
were misclassified, but not how many.

## Error analysis

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

## Takeaway

The remaining errors aren't a prompt problem — they're a specification
problem. Further improvement requires defining what each category
actually means and where the boundaries sit, not rewording instructions.

The hand-labelling itself was the most useful part: it exposed questions
about the task that weren't visible until I had to answer them 100 times.