from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

POSTS = DATA / "posts.csv"
COMMENTS = DATA / "comments.csv"
CHUNKS = DATA / "chunks.csv"
CLASSIFIED = DATA / "posts_classified2.csv"
DB = DATA / "posts.db"
GOLDEN = DATA / "golden.csv"
ERRORS = DATA / "errors.csv"
EMBEDDINGS = DATA / "embeddings.npy"
EMBEDDING_IDS = DATA / "embedding_ids.csv"
EMBEDDINGS_CTX = DATA / "embeddings_ctx.npy"
QUERIES = DATA / "queries.csv"
POOL = DATA / "pool.csv"
QRELS = DATA / "qrels.csv"
JUDGE_PROMPT = ROOT / "evals" / "judge_prompt.md"
REVIEW = DATA / "review.csv"
QDRANT_PATH = DATA / "qdrant"
RUNS = DATA / "runs"
CHUNK_VARIANTS = DATA / "chunks_variants.csv"
EMBEDDINGS_NOQUOTE = DATA / "embeddings_noquote.npy"
EMBEDDINGS_PARENT = DATA / "embeddings_parent.npy"
VARIANTS = {
    "baseline": {"collection": "comments_baseline", "embeddings": EMBEDDINGS},
    "ctx": {"collection": "comments_ctx", "embeddings": EMBEDDINGS_CTX},
    "noquote": {"collection": "comments_noquote", "embeddings": EMBEDDINGS_NOQUOTE},
    "parent": {"collection": "comments_parent", "embeddings": EMBEDDINGS_PARENT},
}
COMMENTS_RAW = DATA / "comments_raw.csv"