import requests
import csv
import os
from datetime import datetime, date

url = "https://hacker-news.firebaseio.com/v0/topstories.json"

response = requests.get(url, timeout=10)

today = date.today().isoformat()
file_exists = os.path.exists("posts.csv")

already_collected = False
if file_exists:
    with open("posts.csv", "r", encoding = "utf-8") as f:
        for row in csv.DictReader(f):
            if row["collected_at"] == today:
                already_collected = True
                break
            
if already_collected:
    print(f"Already collected for {today}, nothing to do")
    exit()

data = response.json() 

with open("posts.csv", "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["collected_at", "title", "score", "comments", "published", "hn_url"])

    for post in data[:100]:
        story_url = f"https://hacker-news.firebaseio.com/v0/item/{post}.json"

        try:
            story_response = requests.get(story_url, timeout=10)
        except Exception as exc:
            print(f"Failed to fetch story ({exc})")
            continue

        if story_response.status_code != 200:
            print(f"Server returned {story_response.status_code}")
            continue

        story = story_response.json()
        title = story.get("title", "no_title")
        score = story.get("score", 0)
        descendants = story.get("descendants", 0)
        time_raw = story.get("time", 0)
        published = datetime.fromtimestamp(time_raw)
        hn_url = f"https://news.ycombinator.com/item?id={post}"
        writer.writerow([today, title, score, descendants, published, hn_url])
        print(f"{title} - {score} points, {descendants} comments")
