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
EMBEDDINGS_BGE_BASE = DATA / "embeddings_bge_base.npy"
EMBEDDINGS_ARCTIC_M = DATA / "embeddings_arctic_m.npy"
CONTEXTS_HAIKU = DATA / "contexts_haiku.csv"
EMBEDDINGS_ARCTIC_HAIKU = DATA / "embeddings_arctic_haiku.npy"
QUERIES_HYDE = DATA / "queries_hyde.csv"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
BGE_SMALL = "BAAI/bge-small-en-v1.5"
ARCTIC_M = "Snowflake/snowflake-arctic-embed-m-v1.5"
VARIANTS = {
    "baseline": {"collection": "comments_baseline", "embeddings": EMBEDDINGS, "model": BGE_SMALL},
    "ctx": {"collection": "comments_ctx", "embeddings": EMBEDDINGS_CTX, "model": BGE_SMALL},
    "noquote": {"collection": "comments_noquote", "embeddings": EMBEDDINGS_NOQUOTE, "model": BGE_SMALL},
    "parent": {"collection": "comments_parent", "embeddings": EMBEDDINGS_PARENT, "model": BGE_SMALL},
    "bge_base": {"collection": "comments_bge_base", "embeddings": EMBEDDINGS_BGE_BASE,
                 "model": "BAAI/bge-base-en-v1.5"},
    "arctic_m": {"collection": "comments_arctic_m", "embeddings": EMBEDDINGS_ARCTIC_M, "model": ARCTIC_M},
    "arctic_bm25": {"collection": "comments_arctic_bm25", "embeddings": EMBEDDINGS_ARCTIC_M,
                    "model": ARCTIC_M, "sparse": "Qdrant/bm25", "bm25_avg_len": 34.7},
    "arctic_haiku": {"collection": "comments_arctic_haiku", "embeddings": EMBEDDINGS_ARCTIC_HAIKU,
                     "model": ARCTIC_M, "contexts": CONTEXTS_HAIKU},
    "arctic_haiku_hyde": {"collection": "comments_arctic_haiku", "embeddings": EMBEDDINGS_ARCTIC_HAIKU,
                     "model": ARCTIC_M, "contexts": CONTEXTS_HAIKU, "queries": QUERIES_HYDE},
    "arctic_haiku_bge": {"collection": "comments_arctic_haiku", "embeddings": EMBEDDINGS_ARCTIC_HAIKU,
                     "model": ARCTIC_M, "contexts": CONTEXTS_HAIKU, "reranker": "BAAI/bge-reranker-v2-m3"},
}
COMMENTS_RAW = DATA / "comments_raw.csv"
QRELS_EXTEND = DATA / "qrels-extend.csv"