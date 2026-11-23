import argparse
import csv

import numpy as np
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, Modifier, PointStruct, SparseVector,
                                  SparseVectorParams, VectorParams)
from sentence_transformers import SentenceTransformer

from config import CHUNKS, QDRANT_PATH, QUERY_PREFIX, VARIANTS
from etl.load_qdrant import load_ids, load_payloads

BATCH_SIZE = 500
CHECK_QUERY = "is dnssec worth deploying in practice"
CHECK_WORD = "dnssec"


def load_texts(ids):
    with open(CHUNKS, "r", encoding="utf-8") as f:
        texts = {row["chunk_id"]: row["text"] for row in csv.DictReader(f)}
    return [texts[i] for i in ids]


def build_collection(client, collection, dense, sparse, ids, payloads):
    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        vectors_config={"dense": VectorParams(size=dense.shape[1], distance=Distance.COSINE)},
        sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)},
    )
    for start in range(0, len(ids), BATCH_SIZE):
        batch = [
            PointStruct(
                id=int(ids[i]),
                vector={
                    "dense": dense[i].tolist(),
                    "bm25": SparseVector(indices=sparse[i].indices.tolist(),
                                         values=sparse[i].values.tolist()),
                },
                payload=payloads[ids[i]],
            )
            for i in range(start, min(start + BATCH_SIZE, len(ids)))
        ]
        client.upsert(collection_name=collection, points=batch)
        print(f"loaded {start + len(batch)} / {len(ids)}")


def check_dense(client, collection, dense, ids, model_name):
    model = SentenceTransformer(model_name)
    q = model.encode([QUERY_PREFIX + CHECK_QUERY], normalize_embeddings=True)[0]
    numpy_top = [ids[i] for i in np.argsort(-(dense @ q))[:5]]
    hits = client.query_points(collection_name=collection, query=q.tolist(),
                               using="dense", limit=5).points
    qdrant_top = [str(h.id) for h in hits]
    print(f"\ndense check: {CHECK_QUERY}")
    print(f"numpy  top-5: {numpy_top}")
    print(f"qdrant top-5: {qdrant_top}")
    print("MATCH" if numpy_top == qdrant_top else "MISMATCH")


def check_sparse(client, collection, sparse_model, payloads):
    q = next(iter(sparse_model.query_embed(CHECK_QUERY)))
    hits = client.query_points(
        collection_name=collection,
        query=SparseVector(indices=q.indices.tolist(), values=q.values.tolist()),
        using="bm25", limit=5,
    ).points
    with_word = sum(CHECK_WORD in payloads[str(h.id)]["text"].lower() for h in hits)
    print(f"\nsparse check: {CHECK_QUERY}")
    print(f"bm25 top-5: {[str(h.id) for h in hits]}")
    print(f"contain '{CHECK_WORD}': {with_word} / {len(hits)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=sorted(v for v in VARIANTS if "sparse" in VARIANTS[v]))
    args = parser.parse_args()
    variant = VARIANTS[args.variant]
    collection = variant["collection"]

    ids = load_ids()
    payloads = load_payloads()
    dense = np.load(variant["embeddings"])
    assert len(ids) == len(dense), f"{len(ids)} ids vs {len(dense)} vectors"

    print(f"variant: {args.variant} -> collection: {collection}")
    print(f"dense: {variant['model']}, sparse: {variant['sparse']}")
    sparse_model = SparseTextEmbedding(variant["sparse"], avg_len=variant["bm25_avg_len"])
    print(f"bm25 avg_len: {sparse_model.model.avg_len}")
    sparse = list(sparse_model.embed(load_texts(ids), batch_size=256))
    print(f"sparse vectors: {len(sparse)}, avg terms: {sum(len(s.indices) for s in sparse) / len(sparse):.1f}")

    client = QdrantClient(path=str(QDRANT_PATH))
    build_collection(client, collection, dense, sparse, ids, payloads)
    print(f"\npoints in collection: {client.count(collection).count}")
    check_dense(client, collection, dense, ids, variant["model"])
    check_sparse(client, collection, sparse_model, payloads)
    client.close()


if __name__ == "__main__":
    main()