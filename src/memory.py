"""
memory.py
---------
Cross-run memory. Every time a check fails, we record which check_id
failed and why. Next time ANY lesson is generated, we surface the most
frequent past failure reasons as "avoid repeating these mistakes" notes
in the generation prompt.

This is what makes the system "self-evolving" across runs (not just
within a single run's retry loop): the prompt itself gets sharper over
time as the failure log accumulates, without any manual prompt editing.

Storage: a flat JSON file. Good enough for a take-home; swap for a real
DB/vector store if this needed to scale across many users/topics.
"""

import json
import os
from collections import Counter

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "memory.json")


def _load() -> dict:
    if not os.path.exists(MEMORY_PATH):
        return {"failures": []}
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_failures(topic: str, checks: dict) -> None:
    data = _load()
    for check_id, result in checks.items():
        if not result.get("pass", False):
            data["failures"].append({
                "topic": topic,
                "check_id": check_id,
                "reason": result.get("reason", ""),
            })
    _save(data)


def get_top_failure_notes(limit: int = 3) -> list[str]:
    """Surface the most common failure reasons seen so far, to pre-warn
    the generator before it even writes a first draft."""
    data = _load()
    if not data["failures"]:
        return []
    counter = Counter(f["check_id"] for f in data["failures"])
    top_ids = [cid for cid, _ in counter.most_common(limit)]

    notes = []
    for cid in top_ids:
        # grab the most recent reason text for that check_id as a concrete example
        example = next(
            (f["reason"] for f in reversed(data["failures"]) if f["check_id"] == cid),
            None,
        )
        if example:
            notes.append(f"({cid}) {example}")
    return notes
