import csv
import re

import numpy as np
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from config import (CHUNK_VARIANTS, CHUNKS, COMMENTS_RAW, EMBEDDING_IDS, EMBEDDINGS,
                    EMBEDDINGS_NOQUOTE, EMBEDDINGS_PARENT)

PARENT_WORDS = 60
BATCH_SIZE = 64
CHECK_N = 50


def paragraphs(html):
    parts = re.split(r"<p>", html or "", flags=re.I)
    texts = [BeautifulSoup(p, "html.parser").get_text(" ", strip=True) for p in parts]
    return [" ".join(t.split()) for t in texts if t]


def is_quote(paragraph):
    return paragraph.startswith(">")


def build_noquote(base_text, raw):
    if raw is None:
        return base_text, "no_raw"
    paras = paragraphs(raw["html"])
    if not any(is_quote(p) for p in paras):
        return base_text, "no_quote"
    own = [p for p in paras if not is_quote(p)]
    if not own:
        return base_text, "only_quote"
    return " ".join(own), "stripped"


def build_parent(base_text, raw):
    if raw is None:
        return base_text, "no_raw"
    if raw["parent_is_story"] == "True":
        return base_text, "top_level"
    parent = " ".join(p for p in paragraphs(raw["parent_html"]) if not is_quote(p))
    words = parent.split()[:PARENT_WORDS]
    if not words:
        return base_text, "empty_parent"
    return f"{base_text}\n\nIn reply to: {' '.join(words)}", "added"


def count(statuses):
    result = {}
    for s in statuses:
        result[s] = result.get(s, 0) + 1
    return result


def main():
    with open(EMBEDDING_IDS, "r", encoding="utf-8") as f:
        ids = [row["chunk_id"] for row in csv.DictReader(f)]
    with open(CHUNKS, "r", encoding="utf-8") as f:
        base = {row["chunk_id"]: row["text"] for row in csv.DictReader(f)}
    with open(COMMENTS_RAW, "r", encoding="utf-8") as f:
        raw = {row["comment_id"]: row for row in csv.DictReader(f)}

    noquote, noquote_status, parent, parent_status = [], [], [], []
    for cid in ids:
        text, status = build_noquote(base[cid], raw.get(cid))
        noquote.append(text)
        noquote_status.append(status)
        text, status = build_parent(base[cid], raw.get(cid))
        parent.append(text)
        parent_status.append(status)

    print(f"noquote: {count(noquote_status)}")
    print(f"parent:  {count(parent_status)}")

    with open(CHUNK_VARIANTS, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["chunk_id", "text_noquote", "text_parent"])
        writer.writerows(zip(ids, noquote, parent))
    print(f"texts saved: {CHUNK_VARIANTS}")

    i = noquote_status.index("stripped")
    print(f"\nexample noquote {ids[i]}:\n  before: {base[ids[i]][:200]}\n  after:  {noquote[i][:200]}")
    j = parent_status.index("added")
    print(f"\nexample parent {ids[j]}:\n  {parent[j][:400]}")

    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    stored = np.load(EMBEDDINGS)[:CHECK_N]
    fresh = model.encode([base[c] for c in ids[:CHECK_N]], normalize_embeddings=True)
    sims = (stored * fresh).sum(axis=1)
    print(f"\nsetup check on {CHECK_N} baseline texts: min similarity {sims.min():.4f}")
    assert sims.min() > 0.99, "embedding setup differs from embeddings.npy"

    for name, texts, path in (("noquote", noquote, EMBEDDINGS_NOQUOTE),
                              ("parent", parent, EMBEDDINGS_PARENT)):
        print(f"\nembedding {name}...")
        vectors = model.encode(texts, normalize_embeddings=True,
                               batch_size=BATCH_SIZE, show_progress_bar=True)
        np.save(path, vectors)
        print(f"saved {path} {vectors.shape}")


if __name__ == "__main__":
    main()