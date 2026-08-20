from typing import List, Dict, Any, Optional
import math


class SemanticMemory:
    """Manages semantic facts and domain knowledge with similarity scoring."""

    def __init__(self):
        self._facts: List[Dict[str, Any]] = []

    def store_fact(self, key: str, value: str, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        self._facts.append({
            "key": key.lower(),
            "value": value,
            "tags": [t.lower() for t in (tags or [])],
            "metadata": metadata or {}
        })

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        tokens = set(query.lower().split())
        results = []

        for fact in self._facts:
            match_count = sum(1 for t in tokens if t in fact["key"] or any(t in tag for tag in fact["tags"]) or t in fact["value"].lower())
            if match_count > 0:
                score = match_count / (math.sqrt(len(tokens)) + 1e-5)
                results.append({"fact": fact, "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return [r["fact"] for r in results[:top_k]]
