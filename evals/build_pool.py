import csv
from rag.search import search
from rag.keyword_search import keyword_search
from config import QUERIES, POOL

TOP_N = 20

queries = []
with open(QUERIES, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["type"] == "pointed":
            queries.append((row["query_id"], row["query"]))

print(f"pointed queries: {len(queries)}")

total_rows = 0

with open(POOL, "w", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["query_id", "comment_id", "found_by"])

    for i, (query_id, query) in enumerate(queries, start=1):
        runs = [
            ("vector", search(query, k=TOP_N)),
            ("vector_ctx", search(query, k=TOP_N, use_context=True)),
            ("bm25", keyword_search(query, k=TOP_N)),
        ]

        found = {}
        for name, hits in runs:
            for comment_id, score in hits:
                found.setdefault(comment_id, set()).add(name)


        for comment_id, names in found.items():
            writer.writerow([query_id, comment_id, "+".join(sorted(names))])
            total_rows += 1

        if i % 10 == 0:
            print(f"{i}/{len(queries)}")

print(f"rows: {total_rows}")
print(f"avg candidates per query: {total_rows / len(queries):.1f}")