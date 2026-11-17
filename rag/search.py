import csv

import numpy as np
from sentence_transformers import SentenceTransformer

from config import CHUNKS, EMBEDDINGS, EMBEDDING_IDS, EMBEDDINGS_CTX

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
vectors = np.load(EMBEDDINGS)

ids = []
with open(EMBEDDING_IDS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ids.append(row["chunk_id"])

texts = {}
with open(CHUNKS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        texts[row["chunk_id"]] = row["text_with_context"]

vectors_plain = np.load(EMBEDDINGS)
vectors_ctx = np.load(EMBEDDINGS_CTX)

def search(query, k=10, use_context=False):
    source = vectors_ctx if use_context else vectors_plain
    q = model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
    scores = source @ q
    top = np.argsort(-scores)[:k]
    return [(ids[i], float(scores[i])) for i in top]


if __name__ == "__main__":
    print("--- without context ---")
    for chunk_id, score in search("is dnssec worth deploying in practice"):
        print(f"{score:.3f}  {texts[chunk_id][:300]}")

    print("\n--- with context ---")
    for chunk_id, score in search("is dnssec worth deploying in practice", use_context=True):
        print(f"{score:.3f}  {texts[chunk_id][:300]}")