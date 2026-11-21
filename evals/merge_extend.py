import csv

from config import QRELS, QRELS_EXTEND


def main():
    with open(QRELS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    existing = {(r["query_id"], r["comment_id"]) for r in rows}
    size_before = len(rows)

    with open(QRELS_EXTEND, "r", encoding="utf-8") as f:
        new = list(csv.DictReader(f))

    added = 0
    for r in new:
        key = (r["query_id"], r["comment_id"])
        if key in existing:
            continue
        row = {**r, "source": "judge", "judge_label": r["label"]}
        rows.append({k: row.get(k, "") for k in fields})
        existing.add(key)
        added += 1

    with open(QRELS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for r in rows:
        counts[r["label"]] = counts.get(r["label"], 0) + 1
    print(f"qrels: {size_before} -> {len(rows)} (+{added})")
    print(f"labels: {dict(sorted(counts.items()))}")


if __name__ == "__main__":
    main()