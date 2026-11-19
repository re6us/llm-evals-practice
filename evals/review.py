import csv
import random

from config import CHUNKS, QRELS, QUERIES, REVIEW

SEED = 42
MAX_PER_ZERO2 = 8
N_LABEL2 = 50
N_LABEL1 = 30
N_LABEL0 = 20

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

done = set()
new_file = not REVIEW.exists()
if not new_file:
    with open(REVIEW, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            done.add((row["query_id"], row["comment_id"]))
print(f"already reviewed: {len(done)}")

rng = random.Random(SEED)
taken = set()

# phase 1 - queries the judge found no answer for, grouped, in order
has_two = {r["query_id"] for r in rows if r["label"] == "2"}
zero2 = sorted({r["query_id"] for r in rows} - has_two)
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

agree = {}
total = {}
agree_conf = {"True": 0, "False": 0}
total_conf = {"True": 0, "False": 0}

with open(REVIEW, "a", newline="", encoding="utf-8") as f_out:
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
        conf = r["borderline"]
        total[name] = total.get(name, 0) + 1
        total_conf[conf] = total_conf.get(conf, 0) + 1

        if answer == judge:
            agree[name] = agree.get(name, 0) + 1
            agree_conf[conf] = agree_conf.get(conf, 0) + 1
            print(f"judge: {judge} - match\n")
        else:
            agree[name] = agree.get(name, 0)
            print(f"judge: {judge} - DISAGREEMENT")
            print(f"judge's reason: {r['reason']}\n")

        writer.writerow([r["query_id"], r["comment_id"], name, judge,
                         conf, answer])
        f_out.flush()

print("=" * 72)
print("agreement by label:")
for name in sorted(total):
    print(f"  {name:8} {agree[name]}/{total[name]} = {agree[name]/total[name]:.0%}")

print("\nagreement by judge confidence:")
for conf, label in (("False", "confident"), ("True", "borderline")):
    if total_conf.get(conf):
        print(f"  {label:11} {agree_conf[conf]}/{total_conf[conf]} "
              f"= {agree_conf[conf]/total_conf[conf]:.0%}")