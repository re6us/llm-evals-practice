import csv
import sys
from statistics import median

from config import CHUNKS, QUERIES, RUNS

DEFAULT_RUN = "baseline"
TOP_K = 10
SNIPPET = 160
TYPES = ("pointed", "aggregating", "unanswerable")


def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in TYPES:
        sys.exit(f"usage: python -m scripts.inspect_run <{'|'.join(TYPES)}> [run_name]")
    query_type = sys.argv[1]
    run_name = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_RUN

    queries = load_csv(QUERIES)
    chunks = {r["chunk_id"]: r for r in load_csv(CHUNKS)}

    hits = {}
    for row in load_csv(RUNS / f"{run_name}.csv"):
        hits.setdefault(row["query_id"], []).append((row["comment_id"], float(row["score"])))

    for q in queries:
        if q["type"] != query_type:
            continue
        qid = q["query_id"]
        print("=" * 80)
        print(f"{qid}  Q: {q['query']}")
        for rank, (cid, score) in enumerate(hits[qid][:TOP_K], start=1):
            chunk = chunks[cid]
            text = " ".join(chunk["text"].split())[:SNIPPET]
            print(f"  #{rank:<2} {score:.3f}  [{chunk['title'][:50]}]")
            print(f"        {text}")
        print()

    print("=" * 80)
    print("top-1 score by query type (min / median / max):")
    for t in TYPES:
        top1 = [hits[q["query_id"]][0][1] for q in queries if q["type"] == t]
        print(f"  {t:<13} n={len(top1):<3} {min(top1):.3f} / {median(top1):.3f} / {max(top1):.3f}")


if __name__ == "__main__":
    main()