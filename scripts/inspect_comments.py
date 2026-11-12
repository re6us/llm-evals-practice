import csv

lengths = []
with open("comments.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        lengths.append(len(row["text"].split()))

lengths.sort()

print(f"total_comments: {len(lengths)}")
print(f"min: {lengths[0]}")
print(f"max: {lengths[-1]}")
print(f"mean: {sum(lengths)/len(lengths):.1f}")
print(f"median_commnt: {lengths[len(lengths) // 2]}")

len_less_10 = 0
len_more_300 = 0

for i in lengths:
    if i < 10:
        len_less_10 += 1
    if i > 300:
        len_more_300 += 1

print(f"length less than 10 words: {len_less_10}")
print(f"length more than 300 words: {len_more_300}")

with open("comments.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        length2 = len(row["text"].split())
        if length2 > 300:
            print(f"{row["story_id"]} | {row["author"]} | {length2} words | {row["text"][-200:]}")