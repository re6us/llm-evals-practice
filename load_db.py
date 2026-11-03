import csv
import sqlite3

conn = sqlite3.connect("posts.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS posts")

cur.execute("""
    CREATE TABLE posts(
        title TEXT,
        score INTEGER,
        comments INTEGER,
        published TEXT,
        topic TEXT,
        confidence TEXT,
        reason TEXT,
        needs_review TEXT,
        steps INTEGER,
        tokens_in INTEGER,
        tokens_out INTEGER,
        cost REAL
    )
""")

with open("posts_classified2.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute(
            "INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (row["title"],
             row["score"],
             row["comments"],
             row["published"],
             row["topic"],
             row["confidence"],
             row["reason"],
             row["needs_review"],
             row["steps"],
             row["tokens_in"],
             row["tokens_out"],
             row["cost"])
        )

conn.commit()
conn.close()

cur2 = sqlite3.connect("posts.db").cursor()
cur2.execute("SELECT COUNT(*) FROM posts")
print(cur2.fetchone())