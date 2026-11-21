import argparse
import csv

from config import POOL, QRELS, QUERIES, RUNS

TOP_N = 20


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="+")
    args = parser.parse_args()

    with open(QUERIES, "r", encoding="utf-8") as f:
        pointed = {r["query_id"] for r in csv.DictReader(f) if r["type"] == "pointed"}
    with open(QRELS, "r", encoding="utf-8") as f:
        labeled = {(r["query_id"], r["comment_id"]) for r in csv.DictReader(f)}
    with open(POOL, "r", encoding="utf-8") as f:
        pool_rows = list(csv.DictReader(f))
    in_pool = {(r["query_id"], r["comment_id"]): r for r in pool_rows}
    size_before = len(pool_rows)

    new = {}
    for run in args.runs:
        added = 0
        with open(RUNS / f"{run}.csv", "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["query_id"] not in pointed or int(row["rank"]) > TOP_N:
                    continue
                key = (row["query_id"], row["comment_id"])
                if key in in_pool:
                    names = set(in_pool[key]["found_by"].split("+")) | {run}
                    in_pool[key]["found_by"] = "+".join(sorted(names))
                else:
                    if key not in new:
                        added += 1
                    new.setdefault(key, set()).add(run)
        print(f"{run}: {added} new pairs")

    for (query_id, comment_id), names in sorted(new.items()):
        pool_rows.append({"query_id": query_id, "comment_id": comment_id,
                          "found_by": "+".join(sorted(names))})

    with open(POOL, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query_id", "comment_id", "found_by"])
        writer.writeheader()
        writer.writerows(pool_rows)

    unlabeled = sum((r["query_id"], r["comment_id"]) not in labeled for r in pool_rows)
    print(f"\npool: {size_before} -> {len(pool_rows)} pairs")
    print(f"pairs to label: {unlabeled}")


if __name__ == "__main__":
    main()