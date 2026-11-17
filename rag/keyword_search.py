import csv
import re

import numpy as np
from rank_bm25 import BM25Okapi

from config import CHUNKS

def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


ids = []
corpus = []
with open(CHUNKS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ids.append(row["chunk_id"])
        corpus.append(tokenize(row["text_with_context"]))

bm25 = BM25Okapi(corpus)


def keyword_search(query, k=10):
    scores = bm25.get_scores(tokenize(query))
    top = np.argsort(-scores)[:k]
    return [(ids[i], float(scores[i])) for i in top]


if __name__ == "__main__":
    texts = {}
    with open(CHUNKS, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            texts[row["chunk_id"]] = row["text_with_context"]

    for chunk_id, score in keyword_search("lisp production companies"):
        print(f"{score:.2f}  {texts[chunk_id][:300]}")