import csv
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from config import POSTS, COMMENTS

stories = set()
with open(POSTS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        stories.add(row["story_id"])
print(f"stories to process: {len(stories)}")

seen = set()
with open(COMMENTS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        seen.add(row["comment_id"])
print(f"comments already collected: {len(seen)}")

added = 0
skipped_dup = 0
failed = 0
skipped_empty = 0
today = date.today().isoformat()

with open(COMMENTS, "a", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)

    for i, story_id in enumerate(sorted(stories), start=1):
        url = (
            "http://hn.algolia.com/api/v1/search"
            f"?tags=comment,story_{story_id}&hitsPerPage=20"
        )

        try:
            response = requests.get(url, timeout=10)
            data = response.json()
        except Exception as exc:
            print(f"failed {story_id}: {exc}")
            failed += 1
            continue

        for hit in data.get("hits", []):
            comment_id = hit["objectID"]

            if comment_id in seen:
                skipped_dup += 1
                continue
            seen.add(comment_id)

            raw = hit.get("comment_text") or ""
            soup = BeautifulSoup(raw, "html.parser")
            text = soup.get_text(separator=" ", strip=True)

            if not text:
                skipped_empty += 1
                continue

            published = hit["created_at"][:19].replace("T", " ")

            writer.writerow([today, hit["story_id"], comment_id,
                             hit.get("author", "unknown"), published, text])
            added += 1

        if i % 50 == 0:
            print(f"{i}/{len(stories)} — added {added}, dup {skipped_dup}, failed {failed}")

        time.sleep(0.2)

print(f"\nadded: {added}")
print(f"skipped dup: {skipped_dup}")
print(f"skipped empty: {skipped_empty}")
print(f"failed: {failed}")