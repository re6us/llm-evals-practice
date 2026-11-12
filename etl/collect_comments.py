import csv
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
import os
from config import POSTS, COMMENTS

today = date.today().isoformat()

today_rows = []

with open(POSTS, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["collected_at"] == today:
            today_rows.append(row)

def comment_count(row):
    return int(row["comments"])

today_rows.sort(key=comment_count, reverse=True)
top_stories = today_rows[:10]

file_exists = os.path.exists(COMMENTS)

already_collected = False

if file_exists:
    with open(COMMENTS, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["collected_at"] == today:
                already_collected = True
                break

if not top_stories:
    print(f"No posts collected for {today} — run git pull or hn.py first")
    exit()

if already_collected:
    print(f"Comments already collected for {today}")
    exit()

with open(COMMENTS, "a", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)
    if not file_exists:
        writer.writerow(["collected_at", "story_id", "comment_id", "author", "published", "text"])

    for story in top_stories:
        story_id = story["story_id"]
        url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"

        response = requests.get(url, timeout=10)
        data = response.json()

        kids = data.get("kids", [])
        top_kids = kids[:30]

        print(f"{len(top_kids):>3} out of {data.get('descendants', 0):>4} {story['title']}")

        for kid in top_kids:
            kid_url = f"https://hacker-news.firebaseio.com/v0/item/{kid}.json"
            kid_response = requests.get(kid_url, timeout=10)
            comment = kid_response.json()

            if comment.get("deleted") or comment.get("dead"):
                continue

            raw_text = comment.get("text", "")
            soup = BeautifulSoup(raw_text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)

            published = datetime.fromtimestamp(comment.get("time", 0))
            writer.writerow([today, story_id, kid, comment.get("by", "unknown"), published, text])