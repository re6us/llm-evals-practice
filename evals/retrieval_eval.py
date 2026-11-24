import argparse
import csv
import math

from qdrant_client import QdrantClient
from qdrant_client.models import Prefetch, Rrf, RrfQuery, SparseVector
from sentence_transformers import SentenceTransformer

from config import QDRANT_PATH, QRELS, QUERIES, QUERY_PREFIX, RUNS, VARIANTS

TOP_N = 50
KS = (5, 10)
RELEVANT_LABEL = "2"
PREFETCH_N = 100
RRF_K = 60


def load_queries():
    with open(QUERIES, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_relevant():
    relevant = {}
    with open(QRELS, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["label"] == RELEVANT_LABEL:
                relevant.setdefault(row["query_id"], set()).add(row["comment_id"])
    return relevant


def dense_hits(client, collection, vec):
    return client.query_points(
        collection_name=collection, query=vec.tolist(), limit=TOP_N
    ).points


def hybrid_hits(client, collection, vec, sparse_vec):
    return client.query_points(
        collection_name=collection,
        prefetch=[
            Prefetch(query=vec.tolist(), using="dense", limit=PREFETCH_N),
            Prefetch(query=SparseVector(indices=sparse_vec.indices.tolist(),
                                        values=sparse_vec.values.tolist()),
                     using="bm25", limit=PREFETCH_N),
        ],
        query=RrfQuery(rrf=Rrf(k=RRF_K)),
        limit=TOP_N,
    ).points


def query_texts(queries, variant):
    if "queries" not in variant:
        return [QUERY_PREFIX + q["query"] for q in queries]
    with open(variant["queries"], "r", encoding="utf-8") as f:
        rewritten = {r["query_id"]: r["hyde"] for r in csv.DictReader(f)}
    return [rewritten.get(q["query_id"]) or QUERY_PREFIX + q["query"] for q in queries]


def retrieve(queries, variant):
    collection = variant["collection"]
    model = SentenceTransformer(variant["model"])
    texts = query_texts(queries, variant)
    vectors = model.encode(texts, normalize_embeddings=True)

    sparse_vectors = None
    if "sparse" in variant:
        from fastembed import SparseTextEmbedding
        sparse_model = SparseTextEmbedding(variant["sparse"])
        sparse_vectors = list(sparse_model.query_embed([q["query"] for q in queries]))

    client = QdrantClient(path=str(QDRANT_PATH))
    results = {}
    for i, (q, vec) in enumerate(zip(queries, vectors)):
        if sparse_vectors is None:
            hits = dense_hits(client, collection, vec)
        else:
            hits = hybrid_hits(client, collection, vec, sparse_vectors[i])
        results[q["query_id"]] = [(str(h.id), h.score) for h in hits]
    client.close()
    return results


def save_run(results, run_name):
    RUNS.mkdir(exist_ok=True)
    path = RUNS / f"{run_name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "rank", "comment_id", "score"])
        for query_id, hits in results.items():
            for rank, (comment_id, score) in enumerate(hits, start=1):
                writer.writerow([query_id, rank, comment_id, f"{score:.4f}"])
    return path


def score_query(ranked_ids, relevant_ids):
    scores = {}
    for k in KS:
        hits = len(set(ranked_ids[:k]) & relevant_ids)
        precision = hits / k
        recall = hits / len(relevant_ids)
        f1 = 2 * precision * recall / (precision + recall) if hits else 0.0
        scores[f"recall@{k}"] = recall
        scores[f"precision@{k}"] = precision
        scores[f"f1@{k}"] = f1

    scores["mrr"] = 0.0
    for rank, comment_id in enumerate(ranked_ids, start=1):
        if comment_id in relevant_ids:
            scores["mrr"] = 1 / rank
            break
    return scores


def mean_with_ci(values):
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, 1.96 * math.sqrt(variance / n)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=sorted(VARIANTS))
    args = parser.parse_args()
    run_name = args.variant
    collection = VARIANTS[run_name]["collection"]

    queries = load_queries()
    relevant = load_relevant()

    results = retrieve(queries, VARIANTS[run_name])
    run_path = save_run(results, run_name)
    print(f"variant: {run_name} -> collection: {collection}, model: {VARIANTS[run_name]['model']}, "
          f"sparse: {VARIANTS[run_name].get('sparse', 'none')}")
    print(f"run saved: {run_path} ({len(results)} queries)")

    per_query = []
    skipped = []
    for q in queries:
        if q["type"] != "pointed":
            continue
        qid = q["query_id"]
        if qid not in relevant:
            skipped.append(qid)
            continue
        ranked_ids = [comment_id for comment_id, _ in results[qid]]
        row = {"query_id": qid, "n_relevant": len(relevant[qid]), "query": q["query"]}
        row.update(score_query(ranked_ids, relevant[qid]))
        per_query.append(row)

    per_query_path = RUNS / f"{run_name}_per_query.csv"
    with open(per_query_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(per_query[0].keys()))
        writer.writeheader()
        for row in per_query:
            writer.writerow({k: f"{v:.4f}" if isinstance(v, float) else v for k, v in row.items()})
    print(f"per-query scores saved: {per_query_path}")

    print(f"\nevaluated: {len(per_query)} pointed queries, skipped (no relevant): {skipped or 'none'}")
    avg_relevant = sum(r["n_relevant"] for r in per_query) / len(per_query)
    print(f"avg relevant per query: {avg_relevant:.1f}\n")
    metric_names = [m for m in per_query[0] if m not in ("query_id", "n_relevant", "query")]
    for name in metric_names:
        mean, half = mean_with_ci([r[name] for r in per_query])
        print(f"{name:<14} {mean:.3f} ± {half:.3f}")


if __name__ == "__main__":
    main()