import argparse
import csv

import numpy as np
from sentence_transformers import SentenceTransformer

from config import CHUNKS, EMBEDDING_IDS, VARIANTS

COLUMN = "text"
BATCH_SIZE = 32


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=sorted(VARIANTS))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    variant = VARIANTS[args.variant]
    output = variant["embeddings"]

    if output.exists() and not args.force:
        raise SystemExit(f"{output} exists, use --force to overwrite")

    with open(EMBEDDING_IDS, "r", encoding="utf-8") as f:
        ids = [row["chunk_id"] for row in csv.DictReader(f)]
    with open(CHUNKS, "r", encoding="utf-8") as f:
        texts_by_id = {row["chunk_id"]: row[COLUMN] for row in csv.DictReader(f)}
    texts = [texts_by_id[i] for i in ids]
    if "contexts" in variant:
        with open(variant["contexts"], "r", encoding="utf-8") as f:
            contexts = {row["chunk_id"]: row["context"] for row in csv.DictReader(f)}
        texts = [f"{contexts[i]}\n\n{t}".strip() for i, t in zip(ids, texts)]
        print(f"contexts: {variant['contexts']}\nsample: {texts[0][:300]}")

    model = SentenceTransformer(variant["model"])
    print(f"variant: {args.variant}, model: {variant['model']}, column: {COLUMN}")
    print(f"device: {model.device}, max_seq_length: {model.max_seq_length}, chunks: {len(texts)}")

    vectors = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    np.save(output, vectors)
    print(f"saved: {output} {vectors.shape}")


if __name__ == "__main__":
    main()