"""Load plain-text comment embeddings into a local Qdrant collection.

Baseline config: bge-small-en-v1.5, one comment = one point, `text` column only.
Re-running the script rebuilds the collection from scratch.
"""
import csv

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from config import CHUNKS, EMBEDDINGS, EMBEDDING_IDS, QDRANT_PATH

COLLECTION = "comments_baseline"
BATCH_SIZE = 500
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
CHECK_QUERY = "is dnssec worth deploying in practice"


def load_ids():
    with open(EMBEDDING_IDS, "r", encoding="utf-8") as f:
        return [row["chunk_id"] for row in csv.DictReader(f)]


def load_payloads():
    payloads = {}
    with open(CHUNKS, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            payloads[row["chunk_id"]] = {
                "story_id": row["story_id"],
                "title": row["title"],
                "published": row["published"],
                "text": row["text"],
            }
    return payloads


def build_collection(client, vectors, ids, payloads):
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=vectors.shape[1], distance=Distance.COSINE),
    )

    for start in range(0, len(ids), BATCH_SIZE):
        batch = [
            PointStruct(
                id=int(ids[i]),
                vector=vectors[i].tolist(),
                payload=payloads[ids[i]],
            )
            for i in range(start, min(start + BATCH_SIZE, len(ids)))
        ]
        client.upsert(collection_name=COLLECTION, points=batch)
        print(f"loaded {start + len(batch)} / {len(ids)}")


def check_against_numpy(client, vectors, ids):
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    q = model.encode([QUERY_PREFIX + CHECK_QUERY], normalize_embeddings=True)[0]

    numpy_top = [ids[i] for i in np.argsort(-(vectors @ q))[:5]]
    hits = client.query_points(collection_name=COLLECTION, query=q.tolist(), limit=5).points
    qdrant_top = [str(h.id) for h in hits]

    print(f"\ncheck query: {CHECK_QUERY}")
    print(f"numpy  top-5: {numpy_top}")
    print(f"qdrant top-5: {qdrant_top}")
    print("MATCH" if numpy_top == qdrant_top else "MISMATCH")


def main():
    vectors = np.load(EMBEDDINGS)
    ids = load_ids()
    payloads = load_payloads()

    assert len(ids) == len(vectors), f"{len(ids)} ids vs {len(vectors)} vectors"
    missing = [i for i in ids if i not in payloads]
    assert not missing, f"{len(missing)} ids missing from chunks.csv"

    client = QdrantClient(path=str(QDRANT_PATH))
    build_collection(client, vectors, ids, payloads)
    print(f"\npoints in collection: {client.count(COLLECTION).count}")

    check_against_numpy(client, vectors, ids)
    client.close()


if __name__ == "__main__":
    main()