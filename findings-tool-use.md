# Findings: tool use and the agent loop

Error analysis for `classify_v3.py` — a Hacker News headline classifier built on the Claude API with two tools.

---

## Part 1 · Tool use, 50 headlines

**Date:** 28 October 2026
**Under test:** a closed tool-use cycle — the model requests `fetch_page`, the code returns a `tool_result`, and a second request produces the classification.

### What worked

| Metric | Value |
|---|---|
| Headlines processed | 50 |
| Went to the page (`fetch_page`) | 15 (30%) |
| `KeyError: 'topic'` failures | 0 |

The tool demonstrably brings in information the headline does not carry. Checked against the model's own justifications:

| Headline | What the model learned from the page |
|---|---|
| `A story of WiFi secrets, UART lockdowns...` | the subject is a Eufy doorbell — absent from the headline |
| `What on Earth Is Dekton?` | a building material used for countertops |
| `How to Formalize All of Mathematics` | the Xena Project |
| `Muse Spark Open` | an open model by Meta |
| `Tesla Roadster` | the new car with rocket thrusters |

Without the second request all 15 rows would have stayed `ERROR`.

### Finding 1 · Confidence is not calibrated

50 rows, not a single `low`. Only `medium` and `high`. The field does not separate confident answers from shaky ones, which makes it useless as a filter.

**Fix hypothesis:** state in the field's `description` when to use `low` — for example, "low if the topic was chosen without support from the text, high only when the headline or page states it directly".

### Finding 2 · Rule 1 is applied inconsistently — the main finding

The prompt says: if the subject is artificial intelligence or language models, answer AI, regardless of the field AI is applied to.

| Headline | Decision | Model's justification |
|---|---|---|
| `Postgres 19 delayed after AI reviewers find bugs` | AI | "rule 1 makes this AI" |
| `Show HN: Wonderhop` (a game) | Other | "AI is only an implementation detail, not the main topic" |
| `Anthropic assigned highest junk credit rating` | Business | "news about a credit rating, not about AI technology" |
| `Anthropic Console overcharged my card 100x` | Business | "a billing error, not AI itself" |

In all four cases AI is circumstance rather than subject. The decisions differ.

**This is a gap in the specification, not a failure of the model.** The rule does not distinguish "news about AI" from "news about something else in which AI is mentioned". The ceiling on accuracy is set by the ambiguity of the task, not by the wording of the prompt — the same conclusion the earlier prompt iterations reached.

**Fix hypothesis:** separate the two cases explicitly. Either "AI as an instrument → classify by subject matter", or "any mention of AI → AI". The second is easier to measure; the first is closer to how a person reads the feed.

### Finding 3 · The language of `reason` was unspecified

`Woman who rescued injured crow...` produced an English justification while the other 49 were in Russian, because the field's `description` said nothing about language.

**Status:** resolved by moving the whole prompt to English.

### Finding 4 · The model misreported a tool result

`Piramidal (YC W24) Is Hiring` → `reason`: "Piramidal builds a foundation model for brain EEG; **the page is empty**".

The page was not empty — its text was printed to the terminal. The model cited missing data and then answered from its own knowledge.

This pattern is dangerous because the logs read as "the tool failed" when the tool worked. Worth a separate check in production.

### Finding 5 · Page text quality

`fetch_page` returns `soup.get_text()[:3000]`. The first ~150 characters of every page are Hacker News navigation:

```
Hacker News new | past | comments | ask | show | jobs | submit login
```

The useful content starts after that. Comments, where the substance of the discussion lives, are partly cut off by the 3000-character limit.

**For the retrieval block:** extract the relevant region of the page instead of the whole text, split on semantic boundaries rather than character counts, and stop paying tokens for site chrome.

---

## Part 2 · From two requests to an agent loop

**Date:** 30 October 2026

The first version made exactly two requests: ask → return the page → ask again. The number of steps was baked into the structure of the code, and there was nowhere to put a third step.

Rewritten as a loop. The code now describes a rule rather than a sequence: while the model asks for tools, serve it and ask again.

### What replaced what

| Before | After | Why |
|---|---|---|
| a second `requests.post` block | a second pass of the loop | on the second pass the first request does the same thing |
| `save_classification` parsed outside the loop | a branch inside the block handler | what matters is the latest response, not which pass produced it |
| the `page_fetched` flag | the `done` flag | the old flag answered "did we fetch a page" (a question about the step), the new one answers "is the work finished" (a question about the result) |
| an unconditional `break` | three conditional exits | the decision to stop moved out of the shape of the code and into a check on state |

### Three exits from the loop

| Condition | What happened |
|---|---|
| `step > 5` | emergency: the model is stuck asking for tools in circles |
| `stop_reason != "tool_use"` | the model answered in plain text and wants no tools |
| `done` | the classification arrived, the work is finished |

### Result

On 10 headlines: one pass for most, two for the ambiguous ones (`What on Earth Is Dekton?`, `Piramidal (YC W24) Is Hiring`). No failures.

The defining property of the new version: the code does not know what the next step will be. It only knows how to serve any step. Giving the model a new capability means one entry in `TOOLS`, one function and one branch in the block handler — the loop itself is untouched.

---

## Implementation notes

- `stop_reason == "tool_use"` arrives for both `fetch_page` and `save_classification`. Tell them apart by `block["name"]` only.
- Collect results into a list and send them as one message. The model may request two tools in a single turn, and two separate `user` messages break the required alternation of roles.
- `break` exits the nearest enclosing loop. `if done: break` placed inside `for block` ends the block scan, not the agent loop — it belongs at the level of the `for`.
- `KeyError: 'content'` means the API returned an error instead of a message. The usual cause is a `tool_use` in the history with no matching `tool_result`.
- If the editor dims the code after `while True`, the exit is missing and the loop is infinite.
- `tool_choice` is not supported for `claude-sonnet-5-5`. Omit it.
- The model has no memory of its own. Every request sends the whole `messages` history from scratch.

---

## What was not measured

Accuracy. `golden.csv` was labelled against an older set of headlines: after an `hn_url` column was added to `hn.py`, `posts.csv` was regenerated from a fresh Hacker News front page and the labels no longer matched the rows.

This is an ordinary production problem rather than an oversight: the corpus moved and the golden set lagged behind. The fix is to key the golden set by row identifiers instead of by position.

**Next step on quality:** label the current 50 headlines, apply fixes 1 and 2, and measure the difference. The measurement applies to the English prompt, which replaced the Russian one on 30 October.
