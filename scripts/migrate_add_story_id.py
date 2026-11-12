import csv

rows = []

with open("posts.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["story_id"] = row["hn_url"].split("id=")[1]
        rows.append(row)

with open("posts.csv", "w", newline ="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["collected_at", "story_id", "title", "score", "comments", "published", "hn_url"])
    for row in rows:
        writer.writerow([row["collected_at"], row["story_id"], row["title"], row["score"], row["comments"], row["published"], row["hn_url"]])

print(f"migrated {len(rows)} rows")