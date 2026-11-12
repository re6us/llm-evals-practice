import csv

FILE_A = "run_v2_3.csv"
FILE_B = "run_v2_4.csv"

def load(path):
    result = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result[row["title"]] = row["topic"]
    return result

a = load(FILE_A)
b = load(FILE_B)

same = 0

for title in a:
    if a[title] == b[title]:
        same += 1
    else:
        print(title)
        print(f" {a[title]} → {b[title]}")

print(f"\nagreement: {same}/{len(a)} = {same / len(a) * 100:.0f}%")