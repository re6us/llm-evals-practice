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