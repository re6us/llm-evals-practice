import requests
import csv
from datetime import datetime

url = "https://hacker-news.firebaseio.com/v0/topstories.json"

response = requests.get(url, timeout=10)

data = response.json() 

with open ("posts.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "score", "comments", "published"])

    for post in data[:100]:
        top10_url = f"https://hacker-news.firebaseio.com/v0/item/{post}.json"

        try:
            story_response = requests.get(top10_url, timeout=10)
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
        writer.writerow([title, score, descendants, published])
        print(f"{title} - {score} голосов, {descendants} комментариев")

#try:
       # response = requests.get(url, params=params, timeout=10)
    #except Exception as exc:
      #  print(f"{name}: не удалось получить данные ({exc})")
       # continue