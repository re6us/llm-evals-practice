import csv
import random
import sys
from collections import Counter

from config import CHUNKS, DATA, QRELS, QUERIES, REVIEW

# --fresh: blind re-check against the judge-v2 definition.
# Separate output file, excludes pairs from the first review,
# no per-pair feedback until the summary at the end.
FRESH = "--fresh" in sys.argv
OUT = DATA / "review-v2.csv" if FRESH else REVIEW

SEED = 42
MAX_PER_ZERO2 = 8
N_LABEL2, N_LABEL1, N_LABEL0 = (15, 15, 10) if FRESH else (50, 30, 20)

texts = {}
with open(CHUNKS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        texts[row["chunk_id"]] = row["text_with_context"]

query_text = {}
with open(QUERIES, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        query_text[row["query_id"]] = row["query"]

rows = []
with open(QRELS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        rows.append(row)
print(f"labels: {len(rows)}")

reason_by_pair = {(r["query_id"], r["comment_id"]): r["reason"] for r in rows}

done = set()
new_file = not OUT.exists()
if not new_file:
    with open(OUT, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            done.add((row["query_id"], row["comment_id"]))
print(f"output: {OUT.name}, already reviewed: {len(done)}")

rng = random.Random(SEED)
taken = set()

if FRESH:
    with open(REVIEW, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            taken.add((row["query_id"], row["comment_id"]))
    print(f"excluded from old review: {len(taken)}")

# phase 1 - queries the judge found no answer for, grouped, in order
has_two = {r["query_id"] for r in rows if r["label"] == "2"}
zero2 = [] if FRESH else sorted({r["query_id"] for r in rows} - has_two)
print(f"queries with no label-2: {len(zero2)}")

phase1 = []
for query_id in zero2:
    ones = [r for r in rows if r["query_id"] == query_id and r["label"] == "1"]
    rng.shuffle(ones)
    for r in ones[:MAX_PER_ZERO2]:
        phase1.append(("zero2", r))
        taken.add((r["query_id"], r["comment_id"]))

# phase 2 - sampled by label, shuffled together
phase2 = []


def sample(name, label, n):
    pool = [r for r in rows
            if r["label"] == label
            and (r["query_id"], r["comment_id"]) not in taken]
    for r in rng.sample(pool, min(n, len(pool))):
        phase2.append((name, r))
        taken.add((r["query_id"], r["comment_id"]))


sample("label2", "2", N_LABEL2)
sample("label1", "1", N_LABEL1)
sample("label0", "0", N_LABEL0)
rng.shuffle(phase2)

queue = [(n, r) for n, r in phase1 + phase2
         if (r["query_id"], r["comment_id"]) not in done]
print(f"to review: {len(queue)}\n")

if FRESH:
    print("blind mode: judge labels are shown only in the summary at the end")
    print("read the label definitions in evals/judge_prompt.md before starting\n")

with open(OUT, "a", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)
    if new_file:
        writer.writerow(["query_id", "comment_id", "bucket", "judge_label",
                         "judge_borderline", "human_label"])

    for i, (name, r) in enumerate(queue, start=1):
        print("=" * 72)
        print(f"[{i}/{len(queue)}]  {r['query_id']}")
        print(f"\nQUESTION:  {query_text[r['query_id']]}")
        comment = " ".join(texts[r["comment_id"]].split())
        print(f"\nCOMMENT:\n{comment}\n")

        print("-" * 72)
        print("2 = answers   1 = on topic   0 = unrelated   s = skip   q = quit")
        answer = input("> ").strip()
        if answer == "q":
            print("stopped, progress saved")
            break
        if answer not in {"0", "1", "2"}:
            print("skipped\n")
            continue

        judge = r["label"]
        writer.writerow([r["query_id"], r["comment_id"], name, judge,
                         r["borderline"], answer])
        f_out.flush()

        if not FRESH:
            if answer == judge:
                print(f"judge: {judge} - match\n")
            else:
                print(f"judge: {judge} - DISAGREEMENT")
                print(f"judge's reason: {r['reason']}\n")

# summary over every row in the output file, across all sessions
with open(OUT, "r", encoding="utf-8") as f:
    reviewed = list(csv.DictReader(f))

print("=" * 72)
if not reviewed:
    print("nothing reviewed yet")
    sys.exit()

n = len(reviewed)
print(f"reviewed: {n}")

print("\nexact agreement by bucket:")
for name in sorted({r["bucket"] for r in reviewed}):
    group = [r for r in reviewed if r["bucket"] == name]
    hits = sum(r["judge_label"] == r["human_label"] for r in group)
    print(f"  {name:8} {hits}/{len(group)} = {hits/len(group):.0%}")

exact = sum(r["judge_label"] == r["human_label"] for r in reviewed)
binary = sum((r["judge_label"] == "2") == (r["human_label"] == "2")
             for r in reviewed)
print(f"\nexact agreement:  {exact}/{n} = {exact/n:.0%}")
print(f"binary agreement (label 2 or not): {binary}/{n} = {binary/n:.0%}")

print("\njudge -> human:")
cells = Counter((r["judge_label"], r["human_label"]) for r in reviewed)
for j in ("0", "1", "2"):
    for h in ("0", "1", "2"):
        if cells[(j, h)]:
            print(f"  {j} -> {h}   {cells[(j, h)]}")

print("\nexact agreement by judge confidence:")
for conf, label in (("False", "confident"), ("True", "borderline")):
    group = [r for r in reviewed if r["judge_borderline"] == conf]
    if group:
        hits = sum(r["judge_label"] == r["human_label"] for r in group)
        print(f"  {label:11} {hits}/{len(group)} = {hits/len(group):.0%}")

if FRESH:
    print("\ndisagreements:")
    for r in reviewed:
        if r["judge_label"] != r["human_label"]:
            pair = (r["query_id"], r["comment_id"])
            print("-" * 72)
            print(f"{r['query_id']} / {r['comment_id']}: "
                  f"judge {r['judge_label']}, you {r['human_label']}")
            print(f"judge's reason: {reason_by_pair.get(pair, '')}")
