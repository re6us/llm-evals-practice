import csv
import sys

import numpy as np
from sklearn.cluster import KMeans

from config import CHUNKS, EMBEDDINGS, EMBEDDING_IDS, EMBEDDINGS_CTX

USE_CONTEXT = "--context" in sys.argv
SOURCE = EMBEDDINGS_CTX if USE_CONTEXT else EMBEDDINGS
COLUMN = "text_with_context" if USE_CONTEXT else "text"
SHOW_CHARS = 600

ONLY = None
if "--cluster" in sys.argv:
    ONLY = int(sys.argv[sys.argv.index("--cluster") + 1])

SHOW = 20

print(f"clustering on: {COLUMN}, showing: {ONLY if ONLY is not None else 'all'}")

K = 20

vectors = np.load(SOURCE)

ids = []
with open(EMBEDDING_IDS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ids.append(row["chunk_id"])

texts = {}
with open(CHUNKS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        texts[row["chunk_id"]] = row[COLUMN]

kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
labels = kmeans.fit_predict(vectors)

for cluster in range(K):
    if ONLY is not None and cluster != ONLY:
        continue
    members = np.where(labels == cluster)[0]
    centre = kmeans.cluster_centers_[cluster]
    distances = np.linalg.norm(vectors[members] - centre, axis=1)
    closest = members[np.argsort(distances)[:SHOW]]

    print(f"\n--- cluster {cluster} · {len(members)} chunks ---")
    for i in closest:
        snippet = texts[ids[i]][:SHOW_CHARS].replace("\n", " ")
        print(f"  {snippet}")