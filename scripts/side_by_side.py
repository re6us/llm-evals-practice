import argparse
import csv

from config import CHUNKS, QRELS, QUERIES, RUNS

SHOW_TOP = 5
SNIPPET = 180
REASON = 150


def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_ranked(run_name):
    ranked = {}
    for row in load_csv(RUNS / f"{run_name}.csv"):
        ranked.setdefault(row["query_id"], []).append(row["comment_id"])
    return ranked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("other")
    parser.add_argument("query_ids", nargs="+")
    args = parser.parse_args()

    queries = {r["query_id"]: r["query"] for r in load_csv(QUERIES)}
    chunks = {r["chunk_id"]: r for r in load_csv(CHUNKS)}
    qrels = {(r["query_id"], r["comment_id"]): r for r in load_csv(QRELS)}
    runs = {name: load_ranked(name) for name in (args.base, args.other)}

    for qid in args.query_ids:
        print("=" * 80)
        print(f"{qid}  Q: {queries[qid]}")
        for name in (args.base, args.other):
            print(f"\n  --- {name} ---")
            for rank, cid in enumerate(runs[name][qid][:SHOW_TOP], start=1):
                chunk = chunks[cid]
                qrel = qrels.get((qid, cid))
                label = qrel["label"] if qrel else "?"
                text = " ".join(chunk["text"].split())[:SNIPPET]
                print(f"  #{rank} [{label}] [{chunk['title'][:55]}]")
                print(f"       {text}")
                if label == "2":
                    print(f"       judge: {qrel['reason'][:REASON]}")
        print()


if __name__ == "__main__":
    main()