import csv
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

PROMPT_TEMPLATE = """Определи тему заголовка.
Доступные темы: AI, Security, Hardware, Programming, Business, Science, Other, Design, Society.

Правила приоритета:
1. Если речь об искусственном интеллекте или языковых моделях — AI,
   независимо от того, к какой области ИИ применяется.
2. Иначе классифицируй по тому, кому материал интересен,
   а не по предмету: железо и математика в контексте разработки — Programming.
3. Если тем несколько, выбирай главную — о чём новость,
   а не что в ней упоминается.

Примеры классификации:
"Sharing AI progress in mathematics" → AI
"South Korea says AI agents used to hack banks" → AI
"ESP32-C3 Adblock" → Programming
"Integer multiplication below n log n" → Programming
"Nobel Prize in Chemistry 2026" → Science


Заголовок: {title}"""

TOOLS = [
    {
        "name": "save_classification",
        "description": "Сохранить классификацию заголовка",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": ["AI", "Security", "Hardware", "Programming",
                             "Business", "Science", "Other", "Design", "Society"]
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                },
                "reason": {
                    "type": "string",
                    "description": "Обоснование, не более 10 слов"
                }
            },
            "required": ["topic", "confidence", "reason"]
        }
    }
]

with open("posts.csv", "r", encoding="utf-8") as f_in, \
    open("posts_classified2.csv", "w", newline="", encoding="utf-8") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(["title", "score", "comments", "published", "topic", "confidence", "reason"])

    for i, row in enumerate(reader):
        print(row["title"])

        prompt = PROMPT_TEMPLATE.format(title=row["title"])
        topic = "ERROR"
        confidence = ""
        reason = ""
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
                "tools": TOOLS,
                "messages": [
                    {"role": "user", "content": prompt},
                ]
            },
            timeout=30,
            )

        
            data = response.json()
            for block in data["content"]:
                if block["type"] == "tool_use":
                    parsed = block["input"]
                    topic = parsed["topic"]
                    confidence = parsed["confidence"]
                    reason = parsed["reason"]
        except Exception as exc:
            print(f"ошибка: {exc}")
            print(f"ответ: {response.json()}")


        writer.writerow([row["title"], row["score"], row["comments"], row["published"], topic, confidence, reason])