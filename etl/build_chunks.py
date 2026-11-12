import csv
from config import POSTS, COMMENTS, CHUNKS

titles = {}
with open(POSTS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        titles[row["story_id"]] = row["title"]

print(len(titles))

written = 0
skipped_short = 0
skipped_dup = 0
missing_title = 0
seen = set()

with open(COMMENTS, "r", encoding="utf-8") as f_in, \
    open(CHUNKS, "w", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["chunk_id", "story_id", "title", "author", "published", "text", "text_with_context"])

    for row in csv.DictReader(f_in):
        length = len(row["text"].split())
        if length < 10:
            skipped_short += 1
            continue
        chunk_id = row["comment_id"]
        if chunk_id in seen:
            skipped_dup += 1
            continue
        seen.add(chunk_id)
        title = titles.get(row["story_id"], "")
        if title == "no_title":
            title = ""
        if title == "":
            missing_title += 1
        date = row["published"][:10]
        if title:
            text_with_context = f"{title} ({date}) - {row['text']}"
        else:
            text_with_context = row["text"]
        writer.writerow([row["comment_id"], row["story_id"], title, row["author"], row["published"], row["text"], text_with_context])
        written += 1

print(f"written: {written}")
print(f"skipped short: {skipped_short}")
print(f"skipped dup: {skipped_dup}")
print(f"missing title: {missing_title}")