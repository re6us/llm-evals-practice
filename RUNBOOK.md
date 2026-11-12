# Runbook

What breaks, how to recognise it, and where to look. Written while building, not afterwards.

Each entry: the symptom first, because that is what you have at 23:40 when something
stops working. The explanation comes second.

Every script runs from the repository root as a module:

```
python -m etl.collect_posts
python -m etl.build_chunks
```

---

## Running and imports

### ModuleNotFoundError: No module named 'config'

**Cause** — the script was run as a path (`python etl/build_chunks.py`) instead of as a
module. Python puts the script's own directory on the import path, not the repository
root, so `config.py` is invisible.

**Fix** — run from the root with `-m` and dots instead of slashes, and no `.py`:

```
python -m etl.build_chunks
```

Every package folder needs an `__init__.py` for this to work. `etl/`, `rag/`, `evals/`
and `scripts/` each have one.

### FileNotFoundError on a data file

**Cause** — a path was hardcoded instead of imported from `config.py`.

**Fix** — never write `open("data/posts.csv")`. Import the constant:

```python
from config import POSTS
```

`config.py` builds every path from `Path(__file__).resolve().parent`, so the scripts work
regardless of the current directory.

---

## Data

### Comment has no story title

**Symptom** — `python -m etl.build_chunks` prints `missing title: N` with N above 0.

**Check** — take one orphaned `story_id` from `data/comments.csv` and search for it in
`data/posts.csv`. If it is absent, the two files have drifted apart.

**Cause** — `data/comments.csv` and `data/posts.csv` are maintained by separate scripts
and nothing enforces the link between them. CSV has no foreign key: a comment may
reference a `story_id` that no longer exists on the other side.

Most likely ways this happens:

- `data/posts.csv` was cleaned, trimmed or rebuilt while the comments kept their history
- the title lookup was built from a date-filtered slice of `data/posts.csv`
- a second comment source was added with its own id space (Algolia, Reddit)
- a git merge conflict in `data/posts.csv` was resolved by dropping rows

**Fix** — do not filter the affected comments out. Dropping them hides the breakage
and silently degrades retrieval. Keep them, keep the counter, and find out which of
the causes above applies.

A moved-to-Postgres version of this pipeline would catch it at insert time with
`REFERENCES posts(story_id)`.

### Title is the literal string "no_title"

**Symptom** — a chunk's context line reads `no_title (2026-11-04) - <comment text>`.

**Check** — `grep -c "no_title" data/posts.csv`. Note that grep exits with code 1 when
it finds nothing; that is not an error, and the terminal marks it red anyway.

**Cause** — `etl/collect_posts.py` writes `story.get("title", "no_title")`. When the
Hacker News API returns a story with no title field, that placeholder lands in the
archive.

The dangerous part is that the lookup *succeeds*: `titles.get(story_id, "")` finds the
key, returns `"no_title"`, and the missing-title counter never increments. A guard
written against a missing key does not catch a present-but-meaningless value.

**Fix** — validate the value, not the presence of the key. Treat `""` and `"no_title"`
as the same case.

### Duplicate stories in posts.csv are signal, not noise

**Symptom** — `data/posts.csv` has far more rows than unique `story_id` values
(901 rows vs 680 unique at the time of writing).

**Do not deduplicate the archive.** A story appearing on several consecutive days is
the momentum signal the whole product is built on. Collapsing it to one row per story
produces a snapshot — which is what Hacker News already shows for free.

Deduplication is correct only when building a **lookup table** (`{story_id: title}`),
and there a Python dict does it automatically: assigning to an existing key overwrites
rather than appends, so the most recent observation wins.

Two different jobs:

| file | holds | duplicates |
|---|---|---|
| `data/posts.csv` | observations: story X on date Y | required |
| `titles` dict | reference: id → title | removed for free |

### Duplicate comments in chunks.csv are harm, not signal

**Symptom** — `python -m etl.build_chunks` prints `skipped dup: N` with N above 0.

This is the **opposite** of the rule above, and the distinction matters.
`etl/collect_comments.py` takes the top-10 most discussed stories *of the day* and
their first 30 comments. A story that stays in the top for two days has its comments
collected twice, with the same `comment_id` and a different `collected_at`.

In the archive that is a second observation. In a search index it is the same opinion
occupying three of the five result slots, crowding out everything else.

`build_chunks.py` keeps the first occurrence and counts the rest. A non-zero counter is
normal once the archive is a few days old.

### Booleans leak through CSV as text

**Symptom** — `SELECT * FROM posts WHERE needs_review = True` returns zero rows and
no error.

**Check** — `SELECT needs_review, COUNT(*) FROM posts GROUP BY needs_review;` shows
the values actually stored.

**Cause** — Python wrote a boolean into a CSV, where everything is text. SQLite kept
it as text. The column contains the strings `'True'` and `'False'`.

**Fix** — quote the comparison: `WHERE needs_review = 'True'`. Or convert on load.
The general lesson: CSV erases types, and the loss surfaces two steps later as a
confidently wrong answer.

### wc -l does not count records in comments.csv

**Symptom** — `wc -l data/comments.csv` and a CSV reader disagree (352 vs ~297).

**Cause** — comment text contains newlines. A CSV record can span several physical
lines when the field is quoted.

**Fix** — count with a CSV reader:

```
python -c "import csv; print(sum(1 for _ in csv.reader(open('data/comments.csv'))))"
```

`wc -l` is safe on `data/posts.csv`, where no field contains newlines. It is not safe
on `data/comments.csv` or `data/chunks.csv`, which hold free text.

### Words appear joined together in terminal output

Not a data problem. The terminal wraps long lines and copying picks up the break.

**Check before investigating** — test the string directly:

```
print("runperhaps" in text)
```

`False` means the join exists only in the rendering.

---

## Classification pipeline

### Known gap: classify.py drops three columns

`collected_at`, `story_id` and `hn_url` are read from `data/posts.csv` but never written
to the output. Consequences:

- no date, so classifications cannot be tracked over time
- no `story_id`, so classifications cannot be joined to comments

Also, the script processes "the first LIMIT rows", which in a growing append-only
archive means **the oldest rows**, not the newest. It needs a date filter.

This blocks the whole momentum half of the product: without a date on a topic, "this
topic tripled this week" cannot be computed.

### tool_choice is not supported on claude-sonnet-5-5

**Symptom** — API error on a request that includes `tool_choice`.

**Fix** — omit the parameter. Tool selection is steered through the prompt instead.

### The ERROR branch of the escalation rule has never fired

`needs_review = confidence == "low" or topic == "ERROR"`.

The first half fired four times out of fifty. The second has never fired, because no
classification has yet failed. That branch is written but unverified.

**A guardrail that has never fired is untested.** The step limit only became
trustworthy once a real run tripped it.

**To test deliberately** — point the script at a non-existent model name, confirm the
row lands as `ERROR` and reaches the review list.

---

## Measurement

### The run measured the wrong version of the prompt

**Symptom** — results move in the wrong direction and a plausible theory starts
forming to explain it.

**Cause** — the file was edited but not saved. The run used the previous prompt.

**Fix** — `PROMPT_VERSION` is printed at the start of every run. Read it before
reading the results. If it does not match what you think you are testing, stop.

This cost the most time of anything in the project. The rule that came out of it:
**verify the input before explaining the output.**

Enabling `File → Auto Save` in VS Code removes the whole class. The same unsaved-file
problem hit `.env` and `collect.yml` as well — in the second case the workflow failed
with `No event triggers defined in 'on'` because the file was empty.

### Self-consistency never reaches 100%

Two sources of disagreement between repeated runs, and they need different fixes:

| source | looks like | fix |
|---|---|---|
| spec ambiguity | the same headline sits between two categories | sharpen the category definitions |
| retrieval non-determinism | different runs read different amounts of the page | make retrieval deterministic |

`How to Formalize All of Mathematics` and `RFC8950` were the second kind. No amount of
prompt work would have settled them.

### A single measurement is not a measurement

The same prompt scored 96% and 90% on two separate pairs of runs. The baseline itself
varies. Every reported figure is the mean of two independent pairs.

On a hundred-query retrieval set the same applies: a difference of a couple of points
between two configurations is probably noise. Report an interval, not a point.

---

## Git and CI

### Push rejected after the bot pushed

**Symptom** — `git push` rejected, remote has commits you do not.

**Cause** — the scheduled GitHub Action committed `data/posts.csv` while you were
working.

**Fix** — `git pull --rebase`, then push.

**Prevention** — `git pull` at the start of every working session, before touching any
file the bot writes. Pulling is only risky when you have already edited the same file;
new untracked files never conflict.

### The scheduled run did not happen at the scheduled time

GitHub Actions cron is best-effort. A workflow set for 07:17 has run at 15:30, 16:22,
16:39, 17:02 and 18:37.

This is not a bug to fix. Anything that depends on exact timing needs a different
trigger. `workflow_dispatch` is there for manual runs.

### The workflow runs but collects nothing

Expected, if the day's collection already happened. `etl/collect_posts.py` checks
whether `collected_at` already holds today's date and exits.

This works **across machines** because `data/posts.csv` lives in git: the runner checks
out what was collected elsewhere. A run of about 10 seconds with no commit is the
idempotency guard doing its job, not a failure.

### Node.js 20 deprecation warning

**Symptom** — a yellow annotation on an otherwise green run.

GitHub's own actions (`checkout@v4`, `setup-python@v5`) run on Node 20. Nothing in this
repository is affected. When it starts failing, raise them to `checkout@v5` and
`setup-python@v6`.

### What belongs in git and what does not

| | in git | reason |
|---|---|---|
| everything under `etl/`, `rag/`, `evals/`, `scripts/` | yes | code |
| `config.py` | yes | code |
| `data/posts.csv`, `data/comments.csv` | yes | the archive; idempotency across machines depends on it |
| `data/chunks.csv` | no | derived, rebuilt by one command |
| `data/posts.db` | no | derived from the CSVs |
| `data/posts_backup.csv` | no | one-off migration artifact |
| `.env` | never | secrets |
| `sandbox/` | no | exercises unrelated to this project |

`.gitignore` is what enforces this. Confusing a script with its output is how a
generated file ends up tracked and a code file ends up ignored.

### SQL fails with "no such column: 'True'"

**Cause** — smart quotes. The query was composed outside the editor, where `'` became
a typographic apostrophe.

**Fix** — type SQL in the terminal or the editor, not in a document.

---

## Idempotency

Three scripts re-run safely, by three different mechanisms:

| script | mechanism |
|---|---|
| `etl/collect_posts.py` | checks whether `collected_at` already has today's date; exits if so |
| `etl/collect_comments.py` | same check against `data/comments.csv` |
| `etl/load_db.py` | `DROP TABLE IF EXISTS` before create |
| `etl/build_chunks.py` | opens its output in `"w"`; a full rebuild every run |

The header check (`if not file_exists`) is a fourth instance — and the one that broke
silently once, when `os.path.exists("comment.csv")` was missing an `s` and the header
would have been rewritten on every run.
