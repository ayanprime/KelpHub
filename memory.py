# this is vault's memory system
# I store it as a simple json file with a list of facts
# remember() saves a fact, recall() finds facts related to what I'm asking

import json
import os
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory_store.json")


def _load_all() -> list[dict]:
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def _save_all(memories: list[dict]) -> None:
    with open(MEMORY_FILE, "w") as f:
        json.dump(memories, f, indent=2)


def remember(fact: str) -> None:
    memories = _load_all()
    memories.append({
        "fact": fact,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    })
    _save_all(memories)


def recall(query: str, max_results: int = 5) -> list[str]:
    # this just matches on shared words, not real semantic search
    # good enough for now, I can upgrade it later if it's not cutting it
    memories = _load_all()
    if not memories:
        return []

    query_words = set(query.lower().split())

    def score(memory: dict) -> int:
        fact_words = set(memory["fact"].lower().split())
        return len(query_words & fact_words)

    scored = [(score(m), m["fact"]) for m in memories]
    scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [fact for _, fact in scored[:max_results]]


def all_facts() -> list[str]:
    return [m["fact"] for m in _load_all()]
