import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

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
            {"role": "user", "content": "Привет! Определи тему заголовка. Ответь одним словом из списка: AI, Security, Hardware, Programming, Business, Science, Other. Без объяснений. Заголовок: GitHub Incident with Git Operations, Pull Requests and Actions"}
        ],
    },
    timeout=30,
)
data = response.json()
for block in data["content"]:
    if block["type"] == "text":
        print(block["text"])

print(data["usage"]["output_tokens"])
