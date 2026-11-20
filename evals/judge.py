import csv
import random
import sys
import time
import json

from anthropic import Anthropic
from dotenv import load_dotenv

from config import CHUNKS, DATA, POOL, QRELS, QUERIES, REVIEW, JUDGE_PROMPT

load_dotenv()

PROMPT_VERSION = "judge-v2"
MODEL = "claude-haiku-5-5" if "--haiku" in sys.argv else "claude-sonnet-5-5"
BATCH_SIZE = 10
SEED = 42
SMOKE = "--smoke" in sys.argv
REVIEWED_ONLY = "--reviewed-only" in sys.argv

OUT = DATA / f"qrels-{PROMPT_VERSION}-{MODEL}-sample.csv" if REVIEWED_ONLY else QRELS

TOOL = {
    "name": "save_labels",
    "description": "Save a relevance label for every candidate",
    "input_schema": {
        "type": "object",
        "properties": {
            "labels": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "candidate": {"type": "integer"},
                        "label": {"type": "integer", "enum": [0, 1, 2]},
                        "borderline": {"type": "boolean"},
                        "reason": {"type": "string"},
                    },
                    "required": ["candidate", "label", "borderline", "reason"],
                },
            }
        },
        "required": ["labels"],
    },
}

with open(JUDGE_PROMPT, "r", encoding="utf-8") as f:
    system_prompt = f.read()
print(f"prompt: {PROMPT_VERSION}, model: {MODEL}")
print(f"output: {OUT.name}")

texts = {}
with open(CHUNKS, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        texts[row["chunk_id"]] = row["text_with_context"]

query_text = {}
with open(QUERIES, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        query_text[row["query_id"]] = row["query"]

candidates = {}
with open(POOL, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        candidates.setdefault(row["query_id"], []).append(row["comment_id"])

if REVIEWED_ONLY:
    keep = set()
    with open(REVIEW, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keep.add((row["query_id"], row["comment_id"]))
    candidates = {q: [c for c in ids if (q, c) in keep]
                  for q, ids in candidates.items()}
    candidates = {q: ids for q, ids in candidates.items() if ids}

pairs = sum(len(v) for v in candidates.values())
print(f"queries: {len(candidates)}, pairs: {pairs}")

done = set()
new_file = not OUT.exists()
if not new_file:
    with open(OUT, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            done.add((row["query_id"], row["comment_id"]))
print(f"already labelled: {len(done)}")

client = Anthropic()
labelled = 0
failed = 0
tokens_in = 0
tokens_out = 0

with open(OUT, "a", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)
    if new_file:
        writer.writerow(["query_id", "comment_id", "label",
                         "borderline", "reason", "prompt_version", "model"])

    for i, query_id in enumerate(sorted(candidates), start=1):
        ids = [c for c in candidates[query_id] if (query_id, c) not in done]
        if not ids:
            continue

        rng = random.Random(f"{SEED}-{query_id}")
        rng.shuffle(ids)

        batches = [ids[start:start + BATCH_SIZE]
                   for start in range(0, len(ids), BATCH_SIZE)]

        if SMOKE:
            batches = batches[:1]

        for batch in batches:
            lines = [f"Question: {query_text[query_id]}", ""]
            for n, comment_id in enumerate(batch, start=1):
                lines.append(f"Candidate {n}:")
                lines.append(texts[comment_id])
                lines.append("")

            try:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=4000,
                    system=system_prompt,
                    tools=[TOOL],
                    messages=[{"role": "user", "content": "\n".join(lines)}],
                )
            except Exception as e:
                print(f"FAILED {query_id}: {e}")
                failed += len(batch)
                continue

            tokens_in += response.usage.input_tokens
            tokens_out += response.usage.output_tokens

            if response.stop_reason == "max_tokens":
                print(f"TRUNCATED {query_id}: hit max_tokens, batch skipped")
                failed += len(batch)
                continue

            block = None
            for b in response.content:
                if b.type == "tool_use":
                    block = b
                    break
            if block is None:
                print(f"NO TOOL CALL {query_id}")
                failed += len(batch)
                continue

            labels = block.input.get("labels")
            if isinstance(labels, str):
                try:
                    labels = json.loads(labels)
                except json.JSONDecodeError:
                    labels = None
            if not isinstance(labels, list):
                print(f"BAD LABELS {query_id}")
                failed += len(batch)
                continue
            by_number = {item["candidate"]: item for item in labels
                         if isinstance(item, dict) and "candidate" in item}
            
            for n, comment_id in enumerate(batch, start=1):
                item = by_number.get(n)
                if item is None or any(k not in item for k in ("label", "borderline", "reason")) \
                        or item["label"] not in (0, 1, 2):
                    failed += 1
                    continue
                writer.writerow([query_id, comment_id, item["label"],
                                 item["borderline"], item["reason"],
                                 PROMPT_VERSION, MODEL])
                labelled += 1

            f_out.flush()
            time.sleep(0.3)

        if SMOKE:
            break

        if i % 10 == 0:
            print(f"{i}/{len(candidates)} queries · {labelled} labelled")

print(f"labelled: {labelled}")
print(f"failed: {failed}")
print(f"tokens in: {tokens_in}, out: {tokens_out}")