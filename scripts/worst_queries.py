import csv
import sys

from config import CHUNKS, QRELS, RUNS

DEFAULT_RUN = "baseline"
N_WORST = 10
SHOW_TOP = 5
SNIPPET = 220


def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    run_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RUN

    per_query = load_csv(RUNS / f"{run_name}_per_query.csv")
    worst = sorted(per_query, key=lambda r: (float(r["recall@10"]), float(r["mrr"])))[:N_WORST]

    ranked = {}
    for row in load_csv(RUNS / f"{run_name}.csv"):
        ranked.setdefault(row["query_id"], []).append(row["comment_id"])

    labels = {(r["query_id"], r["comment_id"]): r["label"] for r in load_csv(QRELS)}
    chunks = {r["chunk_id"]: r for r in load_csv(CHUNKS)}

    def describe(comment_id):
        chunk = chunks.get(comment_id)
        if chunk is None:
            return "<missing from chunks.csv>", ""
        text = " ".join(chunk["text"].split())[:SNIPPET]
        return chunk["title"][:70], text

    for r in worst:
        qid = r["query_id"]
        top = ranked[qid]
        print("=" * 80)
        print(f"{qid}  recall@10={float(r['recall@10']):.2f}  "
              f"mrr={float(r['mrr']):.2f}  relevant={r['n_relevant']}")
        print(f"Q: {r['query']}")

        print(f"\n  returned top-{SHOW_TOP}:")
        for rank, cid in enumerate(top[:SHOW_TOP], start=1):
            title, text = describe(cid)
            print(f"  #{rank} [{labels.get((qid, cid), '?')}] {title}")
            print(f"       {text}")

        relevant = [cid for (q, cid), label in labels.items() if q == qid and label == "2"]
        missed = [cid for cid in relevant if cid not in top[:SHOW_TOP]]
        print(f"\n  relevant missed from top-{SHOW_TOP}:")
        for cid in missed:
            where = f"rank {top.index(cid) + 1}" if cid in top else "not in top-50"
            title, text = describe(cid)
            print(f"  ({where}) {title}")
            print(f"       {text}")
        print()


if __name__ == "__main__":
    main()