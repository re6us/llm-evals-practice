"""One-off: replace hardcoded data filenames with config constants.

Run once from the repo root:   python fix_paths.py
Check the result with:         git diff
Then delete this file.

Every replacement is reported. A line starting with MISS means the string was
not found in that file — look at it by hand, the code there differs from what
this script expects.
"""

from pathlib import Path

# filename in quotes  ->  what replaces it
NAMES = {
    '"posts.csv"': "POSTS",
    '"comments.csv"': "COMMENTS",
    '"chunks.csv"': "CHUNKS",
    '"posts_classified2.csv"': "CLASSIFIED",
    '"posts.db"': "DB",
    '"golden.csv"': "GOLDEN",
    '"errors.csv"': "ERRORS",
    '"run_v2_1.csv"': 'DATA / "run_v2_1.csv"',
    '"run_v2_2.csv"': 'DATA / "run_v2_2.csv"',
}

# file -> the import line it needs
FILES = {
    "etl/collect_posts.py": "from config import POSTS",
    "etl/collect_comments.py": "from config import POSTS, COMMENTS",
    "etl/classify.py": "from config import POSTS, CLASSIFIED",
    "etl/build_chunks.py": "from config import POSTS, COMMENTS, CHUNKS",
    "etl/load_db.py": "from config import CLASSIFIED, DB",
    "evals/compare.py": "from config import DATA",
    "evals/evaluate.py": "from config import GOLDEN, ERRORS, CLASSIFIED",
    "evals/make_golden.py": "from config import GOLDEN, CLASSIFIED",
    "scripts/inspect_comments.py": "from config import COMMENTS",
}

for path, import_line in FILES.items():
    p = Path(path)
    if not p.exists():
        print(f"MISS  {path} — file not found, skipped")
        continue

    src = p.read_text(encoding="utf-8")
    original = src
    hits = []

    for old, new in NAMES.items():
        count = src.count(old)
        if count:
            hits.append(f"{old} x{count}")
            src = src.replace(old, new)

    if src == original:
        print(f"MISS  {path} — nothing replaced, check this one by hand")
        continue

    if import_line not in src:
        lines = src.split("\n")
        import_rows = [
            i for i, line in enumerate(lines)
            if line.startswith("import ") or line.startswith("from ")
        ]
        insert_at = max(import_rows) + 1 if import_rows else 0
        lines.insert(insert_at, import_line)
        src = "\n".join(lines)

    p.write_text(src, encoding="utf-8")
    print(f"ok    {path} — {', '.join(hits)}")

print("\nNow run:  git diff")
