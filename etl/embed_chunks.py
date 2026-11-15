import csv
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

from config import CHUNKS, EMBEDDINGS, EMBEDDING_IDS, EMBEDDINGS_CTX

USE_CONTEXT = "--context" in sys.argv
COLUMN = "text_with_context" if USE_CONTEXT else "text"
OUTPUT = EMBEDDINGS_CTX if USE_CONTEXT else EMBEDDINGS

print(f"column: {COLUMN}")

chunk_ids = []
texts = []

with open(CHUNKS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        chunk_ids.append(row["chunk_id"])
        texts.append(row[COLUMN])

print(f"chunks to embed: {len(texts)}")

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
vectors = model.encode(
    texts,
    batch_size=64,
    show_progress_bar=True,
    normalize_embeddings=True,
)

np.save(OUTPUT, vectors)

with open(EMBEDDING_IDS, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["chunk_id"])
    for chunk_id in chunk_ids:
        writer.writerow([chunk_id])

print(f"saved: {vectors.shape}")