import requests
import csv
from datetime import datetime

url = "https://hacker-news.firebaseio.com/v0/topstories.json"

response = requests.get(url, timeout=10)

data = response.json() 

with open ("posts.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "score", "comments", "published", "hn_url"])

    for post in data[:100]:
        story_url = f"https://hacker-news.firebaseio.com/v0/item/{post}.json"

        try:
            story_response = requests.get(story_url, timeout=10)
        except Exception as exc:
            print(f"Не удалось получить данные ({exc})")
            continue

        if story_response.status_code != 200:
            print(f"Сервер ответил {story_response.status_code}")
            continue

        story = story_response.json()
        title = story.get("title", 'без заголовка')
        score = story.get("score", 0)
        descendants = story.get("descendants", 0)
        time_raw = story.get("time", 0)
        published = datetime.fromtimestamp(time_raw)
        hn_url = f"https://news.ycombinator.com/item?id={post}"
        writer.writerow([title, score, descendants, published, hn_url])
        print(f"{title} - {score} голосов, {descendants} комментариев")
