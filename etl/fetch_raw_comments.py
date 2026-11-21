import csv
import time

import requests

from config import COMMENTS, COMMENTS_RAW

ITEM_URL = "https://hn.algolia.com/api/v1/items/{}"
SLEEP = 0.2
FIELDS = ["comment_id", "story_id", "parent_id", "parent_is_story", "html", "parent_html"]


def load_wanted():
    by_story = {}
    with open(COMMENTS, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_story.setdefault(row["story_id"], set()).add(row["comment_id"])
    return by_story


def load_done():
    if not COMMENTS_RAW.exists():
        return set()
    with open(COMMENTS_RAW, "r", encoding="utf-8") as f:
        return {row["comment_id"] for row in csv.DictReader(f)}


def flatten(story):
    nodes = {}
    stack = [(story, True)]
    while stack:
        node, is_story = stack.pop()
        for child in node.get("children", []):
            nodes[str(child["id"])] = {
                "parent_id": str(node["id"]),
                "parent_is_story": is_story,
                "html": child.get("text") or "",
                "parent_html": node.get("text") or "",
            }
            stack.append((child, False))
    return nodes


def main():
    by_story = load_wanted()
    done = load_done()
    total = sum(len(ids) for ids in by_story.values())
    print(f"stories: {len(by_story)}, comments: {total}, already fetched: {len(done)}")

    file_exists = COMMENTS_RAW.exists()
    written = 0
    missing = 0
    failed = []

    with open(COMMENTS_RAW, "a", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=FIELDS)
        if not file_exists:
            writer.writeheader()

        for i, (story_id, wanted) in enumerate(sorted(by_story.items()), start=1):
            todo = wanted - done
            if not todo:
                continue

            try:
                response = requests.get(ITEM_URL.format(story_id), timeout=30)
                response.raise_for_status()
                nodes = flatten(response.json())
            except Exception as exc:
                print(f"failed {story_id}: {exc}")
                failed.append(story_id)
                continue

            for comment_id in sorted(todo):
                node = nodes.get(comment_id)
                if node is None:
                    missing += 1
                    continue
                writer.writerow({"comment_id": comment_id, "story_id": story_id, **node})
                written += 1
            f_out.flush()

            if i % 50 == 0:
                print(f"{i}/{len(by_story)} stories, written {written}, missing {missing}")
            time.sleep(SLEEP)

    print(f"\nwritten: {written}")
    print(f"missing in tree (deleted or moved): {missing}")
    print(f"failed stories: {len(failed)} {failed[:10]}")


if __name__ == "__main__":
    main()