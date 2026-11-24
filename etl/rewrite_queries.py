import argparse
import csv

import anthropic
from dotenv import load_dotenv

from config import QUERIES, QUERIES_HYDE

MODEL = "claude-haiku-5-5"

PROMPT = """You help a search engine over Hacker News comments. Each stored document has this shape:
a one-sentence note that starts with the specific topic of the thread and says what the comment does, a blank line, then the comment text.

Write one such document that would answer the question below, as a plausible Hacker News comment.

Rules:
- Note: one sentence, at most 40 words, start with the specific topic.
- Comment: 40 to 100 words, first person, concrete, the way developers write on Hacker News.
- No usernames, no mention of Hacker News, no links.
- Output only the note, a blank line, and the comment.

Question: {query}"""


def load_queries(limit):
    with open(QUERIES, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def rewrite(client, query):
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": PROMPT.format(query=query)}],
    )
    if response.stop_reason == "refusal":
        return ""
    if response.stop_reason == "max_tokens":
            print("warning: cut off at max_tokens", flush=True)
            return ""
    texts = [b.text for b in response.content if b.type == "text"]
    return "\n".join(texts).strip()

def save(results):
    with open(QUERIES_HYDE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query_id", "hyde"])
        writer.writeheader()
        writer.writerows(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    load_dotenv(".env")
    client = anthropic.Anthropic()
    queries = load_queries(args.limit)

    results = []
    for q in queries:
        text = rewrite(client, q["query"])
        results.append({"query_id": q["query_id"], "hyde": text})
        print(f"--- {q['query_id']}: {q['query']}\n{text}\n", flush=True)

    empty = sum(1 for r in results if not r["hyde"])
    print(f"done: {len(results)} queries, {empty} empty")

    if args.limit:
        print("smoke run: nothing saved")
    else:
        save(results)
        print(f"saved: {QUERIES_HYDE}")


if __name__ == "__main__":
    main()