"""Overlay adjudicated human labels on the judge labels in qrels.csv.

Human labels come from the blind re-review (data/review-v2.csv, 40 pairs),
with nine disputed pairs settled by adjudication. The older review.csv
(152 pairs) is not used: it was labelled before the definition was written
down, and the re-review showed that its bar was looser.

Adds two columns: source (judge / human) and judge_label (the label before
the overlay), so every label's origin stays visible.
"""
import csv
from collections import Counter

from config import DATA, QRELS

REVIEW_FRESH = DATA / "review-v2.csv"

# adjudicated binary verdicts: True = must be 2, False = must not be 2,
# None = still disputed, the judge label stays
VERDICT = {
    ("q004", "50361818"): False,  # judge took a fact from the title
    ("q059", "50476183"): False,  # restates the question's premise
    ("q021", "50493052"): False,  # facts on a neighbouring topic
    ("q045", "50395903"): False,  # general claim, question is specific
    ("q019", "50388659"): False,  # the step to the question is the reader's
    ("q066", "50401849"): True,   # position with reasons on half the question
    ("q054", "50429383"): True,   # names the mechanisms directly
    ("q033", "50426983"): True,   # first-hand, answers the quality half
    ("q004", "50392357"): None,   # the question reads two ways
}

EXTRA = {
    ("q021", "50446770"): "1",  # quotes an article, never ties it to the S-1
    ("q005", "50341207"): "2",  # direct claim on half the question
}

with open(QRELS, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    header = reader.fieldnames
    rows = list(reader)

if "source" in header:
    raise SystemExit("qrels.csv already has a source column - overlay was done before")

human = {}
with open(REVIEW_FRESH, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        key = (row["query_id"], row["comment_id"])
        verdict = VERDICT.get(key, "none")
        if verdict is None:
            continue
        if verdict is True:
            human[key] = "2"
        elif verdict is False:
            human[key] = row["human_label"] if row["human_label"] != "2" else "1"
        else:
            human[key] = row["human_label"]

human.update(EXTRA)
before = Counter(r["label"] for r in rows)
changed = 0
found = 0
for r in rows:
    key = (r["query_id"], r["comment_id"])
    r["judge_label"] = r["label"]
    if key in human:
        found += 1
        if human[key] != r["label"]:
            changed += 1
        r["label"] = human[key]
        r["source"] = "human"
    else:
        r["source"] = "judge"

if found != len(human):
    raise SystemExit(f"only {found} of {len(human)} human pairs found in qrels.csv - nothing written")

with open(QRELS, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header + ["source", "judge_label"])
    writer.writeheader()
    writer.writerows(rows)

after = Counter(r["label"] for r in rows)
print(f"rows: {len(rows)}")
print(f"human labels applied: {found}, changed: {changed}")
print(f"labels before: {dict(sorted(before.items()))}")
print(f"labels after:  {dict(sorted(after.items()))}")
print(f"source: {dict(Counter(r['source'] for r in rows))}")
