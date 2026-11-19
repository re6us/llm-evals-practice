import csv
import sys
from collections import Counter

from config import REVIEW

path = sys.argv[1]

human = {}
with open(REVIEW, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        human[(row["query_id"], row["comment_id"])] = row["human_label"]

c = Counter()
with open(path, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        key = (row["query_id"], row["comment_id"])
        if key in human:
            c[(row["label"], human[key])] += 1

n = sum(c.values())
exact = sum(v for (j, h), v in c.items() if j == h)
binary = sum(v for (j, h), v in c.items() if (j == "2") == (h == "2"))

print(f"\n{path}")
print(f"pairs compared:    {n}")
print(f"exact agreement:   {exact}/{n} = {exact / n:.0%}")
print(f"binary (is a 2):   {binary}/{n} = {binary / n:.0%}")
print("\njudge -> human")
for j in "012":
    for h in "012":
        v = c.get((j, h), 0)
        if v:
            print(f"  {j} -> {h}: {v}{'   match' if j == h else ''}")