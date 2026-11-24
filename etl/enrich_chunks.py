import argparse
import csv
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
from dotenv import load_dotenv

MODEL = "claude-haiku-5-5"
CHUNKS_PATH = "data/chunks.csv"
CONTEXTS_PATH = "data/contexts_haiku.csv"

PROMPT = """<thread>
<title>{title}</title>
{comments}
</thread>

Here is one comment from this thread:
<comment>
{comment}
</comment>

Write a short context for this comment, to improve search retrieval of the comment. One or two sentences, at most 50 words.
- Start with the concrete topic: the product, technology or event the comment is about.
- If the comment says "it", "this" or "they", name what they refer to, but only when the thread makes it clear. Do not guess.
- Describe only what this comment says. Use the other comments only to understand it; do not summarize them.
- Do not mention usernames or Hacker News, and do not judge the comment.
Answer only with the context, nothing else."""


def load_threads():
    rows = list(csv.DictReader(open(CHUNKS_PATH, encoding="utf-8")))
    threads = defaultdict(list)
    for r in rows:
        threads[r["story_id"]].append(r)
    return rows, threads


def build_prompt(chunk, thread):
    comments = "\n".join(
        f'<c author="{r["author"]}">{r["text"]}</c>' for r in thread
    )
    return PROMPT.format(title=chunk["title"], comments=comments, comment=chunk["text"])


def enrich(client, chunk, thread):
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": build_prompt(chunk, thread)}],
    )
    if response.stop_reason == "refusal":
        return "", response.usage
    text = next(b.text for b in response.content if b.type == "text")
    return text.strip(), response.usage


def pick_smoke(rows):
    by_len = sorted(rows, key=lambda r: len(r["text"].split()))
    n = len(by_len)
    return [by_len[n // 10], by_len[n // 2], by_len[n * 9 // 10]]


def run_smoke(client, rows, threads):
    for chunk in pick_smoke(rows):
        context, usage = enrich(client, chunk, threads[chunk["story_id"]])
        print("=" * 80)
        print(f'chunk {chunk["chunk_id"]} | {len(chunk["text"].split())} words | {chunk["title"]}')
        print(f'COMMENT: {chunk["text"][:400]}')
        print(f"CONTEXT: {context}")
        print(f"tokens in/out: {usage.input_tokens}/{usage.output_tokens}")


def load_done():
    if not os.path.exists(CONTEXTS_PATH):
        return set()
    with open(CONTEXTS_PATH, encoding="utf-8") as f:
        return {r["chunk_id"] for r in csv.DictReader(f)}


def run_full(client, rows, threads, workers, limit):
    done = load_done()
    todo = [r for r in rows if r["chunk_id"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"already done: {len(done)}, to do now: {len(todo)}, workers: {workers}", flush=True)

    new_file = not os.path.exists(CONTEXTS_PATH)
    tokens_in = tokens_out = failed = 0
    start = time.time()

    with (
        open(CONTEXTS_PATH, "a", encoding="utf-8", newline="") as f,
        ThreadPoolExecutor(max_workers=workers) as pool,
    ):
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["chunk_id", "context"])
        futures = {
            pool.submit(enrich, client, r, threads[r["story_id"]]): r["chunk_id"]
            for r in todo
        }
        for i, future in enumerate(as_completed(futures), 1):
            chunk_id = futures[future]
            try:
                context, usage = future.result()
            except Exception as e:
                failed += 1
                print(f"FAILED {chunk_id}: {e}", flush=True)
                continue
            writer.writerow([chunk_id, context])
            f.flush()
            tokens_in += usage.input_tokens
            tokens_out += usage.output_tokens
            if i % 100 == 0:
                print(f"{i}/{len(todo)} | {time.time() - start:.0f}s", flush=True)

    print(f"finished: {len(todo) - failed} ok, {failed} failed, {time.time() - start:.0f}s")
    print(f"tokens in/out: {tokens_in}/{tokens_out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    load_dotenv()
    client = anthropic.Anthropic(max_retries=5)
    rows, threads = load_threads()

    if args.smoke:
        run_smoke(client, rows, threads)
    else:
        run_full(client, rows, threads, args.workers, args.limit)


if __name__ == "__main__":
    main()