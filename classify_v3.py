import csv
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

PROMPT_TEMPLATE = """Determine the topic of the headline.

Topics and what belongs to each:
- AI — artificial intelligence or language models are what the news is about:
  models, agents, benchmarks, AI products, AI policy, or AI applied to some field.
- Security — vulnerabilities, exploits, authentication, privacy and surveillance
  seen from an attack or defence angle.
- Hardware — physical devices and components: chips, computers, sensors,
  networking equipment, vehicles, manufacturing of electronics.
- Programming — software development: languages, algorithms, libraries, tools,
  deployment, browser and operating system internals, software bugs.
- Business — companies, markets, money, pricing, funding, hiring, investing.
- Science — natural sciences and research: physics, chemistry, biology, materials.
  Mathematics belongs here only as a research subject; mathematics done with code
  or tooling is Programming.
- Society — people, politics, law, culture, history, human-interest stories.
- Design — visual and interaction design, typography, user experience.
- Other — last resort. Use it only when no definition above applies. Material
  being non-technical is not a reason to choose Other: Society, Science and
  Business all cover non-technical subjects.

Priority rules:
1. Answer AI when artificial intelligence is the subject of the news, including
   AI applied to another field. Do not answer AI when AI is only the means by
   which something else happened and the news is about that something else.
2. When a subject could sit in two topics, classify by who the material is for:
   hardware and mathematics in a development context are Programming.
3. If several topics apply, pick the main one — what the news is about, not what
   it mentions in passing.

Examples:
"Sharing AI progress in mathematics" → AI
"AI-assisted CAD plugin for Fusion 360" → AI
"MySQL 9 release slips after automated reviewers flag regressions" → Programming
"OpenAI raises funding at a $300B valuation" → Business
"Stolen Rembrandt sketch recovered from a storage unit" → Society
"Nobel Prize in Chemistry 2026" → Science
"ESP32-C3 Adblock" → Programming
"Integer multiplication below n log n" → Programming

If the headline alone is not enough, request the page text with fetch_page first,
then classify.

Headline: {title}
Discussion URL: {url}"""

PROMPT_VERSION = "v2-category-definitions"
print(f"prompt version: {PROMPT_VERSION}")

TOOLS = [
    {
        "name": "save_classification",
        "description": "Save the classification of a headline",
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
                    "enum": ["high", "medium", "low"],
                    "description": "high — the headline or page states the topic directly. medium — the topic follows from context. low — the topic was guessed, the material sits between two categories, or the page gave no useful information."
                },
                "reason": {
                    "type": "string",
                    "description": "Short justification, 10 words maximum"
                }
            },
            "required": ["topic", "confidence", "reason"]
        }
    },
    {
        "name": "fetch_page",
        "description": "Fetch the text of a page by URL. Use it if the headline alone is not enough to classify.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Page address"}
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
        if i >= 50:
            break
        print(row["title"])

        prompt = PROMPT_TEMPLATE.format(title=row["title"], url=row["hn_url"])
        topic = "ERROR"
        confidence = ""
        reason = ""
        messages = [{"role": "user", "content": prompt}]
        step = 0
        try:
            while True:
                step += 1
                print(f"step {step}")
                if step >5:
                    print("step limit exceeded")
                    break
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

                messages.append({
                    "role": "assistant",
                    "content": data["content"]
                })

                if data["stop_reason"] != "tool_use":
                    break
                tool_results = []
                done = False
                for block in data["content"]:
                    if block["type"] == "tool_use" and block["name"] == "save_classification":
                        parsed = block["input"]
                        topic = parsed["topic"]
                        confidence = parsed["confidence"]
                        reason = parsed["reason"]
                        done = True
                        print(f"→ called {block['name']}")
                    if block["type"] == "tool_use" and block["name"] == "fetch_page":
                        tool_id = block["id"]
                        page_url = block["input"]["url"]
                        page_text = fetch_page(page_url)
                        tool_results.append({    
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": page_text
                        })
                        print(page_text[:200])
                if done:
                    break
                if tool_results:
                    messages.append({"role": "user", "content": tool_results })

        except Exception as exc:
            print(f"error: {exc}")


        writer.writerow([row["title"], row["score"], row["comments"], row["published"], topic, confidence, reason])