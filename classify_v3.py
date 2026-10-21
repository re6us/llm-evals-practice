import csv
import os
import requests
from bs4 import BeautifulSoup
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

Если по заголовку тему определить трудно, сначала запроси текст страницы
через fetch_page, а потом классифицируй.

Заголовок: {title}
Ссылка на обсуждение: {url}"""

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
    },
    {
        "name": "fetch_page",
        "description": "Получить текст страницы по ссылке. Используй, если заголовка недостаточно для классификации.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Адрес страницы"}
            },
            "required": ["url"]
        }
    }
]

def fetch_page(url):
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text[:3000]

with open("posts.csv", "r", encoding="utf-8") as f_in, \
    open("posts_classified2.csv", "w", newline="", encoding="utf-8") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(["title", "score", "comments", "published", "topic", "confidence", "reason"])
    
    for i, row in enumerate(reader):
        if i >= 10:
            break
        print(row["title"])

        prompt = PROMPT_TEMPLATE.format(title=row["title"], url=row["hn_url"])
        topic = "ERROR"
        confidence = ""
        reason = ""
        messages = [{"role": "user", "content": prompt}]
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
                "messages": messages
            },
            timeout=30,
            )

        
            data = response.json()

            if data["stop_reason"] == "tool_use":
                for block in data["content"]:
                    if block["type"] == "tool_use" and block["name"] == "save_classification":
                        tool_id = block["id"]
                        page_url = block["input"]["url"]
                        page_text = fetch_page(page_url)
                        print(page_text[:200])

            for block in data["content"]:
                if block["type"] == "tool_use":
                    parsed = block["input"]
                    topic = parsed["topic"]
                    confidence = parsed["confidence"]
                    reason = parsed["reason"]
                    print(f"→ вызвала {block['name']}")
        except Exception as exc:
            print(f"ошибка: {exc}")
            print(f"ответ: {response.json()}")


        writer.writerow([row["title"], row["score"], row["comments"], row["published"], topic, confidence, reason])