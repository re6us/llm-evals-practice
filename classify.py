import csv
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

PROMPT_TEMPLATE = """Определи тему заголовка.
Ответь одним словом из списка: AI, Security, Hardware, Programming, Business, Science, Other, Design, Society.

Правила приоритета:
1. Если речь об искусственном интеллекте или языковых моделях — AI,
   независимо от того, к какой области ИИ применяется.
2. Иначе классифицируй по тому, кому материал интересен,
   а не по предмету: железо и математика в контексте разработки — Programming.
3. Если тем несколько, выбирай главную — о чём новость,
   а не что в ней упоминается.

Примеры:
"Sharing AI progress in mathematics" → AI
"South Korea says AI agents used to hack banks" → AI
"ESP32-C3 Adblock" → Programming
"Integer multiplication below n log n" → Programming
"Nobel Prize in Chemistry 2026" → Science

Без объяснений, только одно слово.

Заголовок: {title}"""


with open("posts.csv", "r", encoding="utf-8") as f_in, \
    open("posts_classified.csv", "w", newline="", encoding="utf-8") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(["title", "score", "comments", "published", "topic"])

    for i, row in enumerate(reader):
        print(row["title"])

        prompt = PROMPT_TEMPLATE.format(title=row["title"])
        topic = "ERROR"
        try:
            response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-5-5",
                "max_tokens": 1000,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30,
            )

        
            data = response.json()
            for block in data["content"]:
                if block["type"] == "text":
                    topic = block["text"]
        except Exception as exc:
            print(f"ошибка: {exc}")


        writer.writerow([row["title"], row["score"], row["comments"], row["published"], topic])