from typing import List, Dict, Any
import math


LEGOCARDS = [
    {"name": "Emmet", "theme": "LEGO Movie", "score": 95},
    {"name": "Pirate Captain", "theme": "Pirates", "score": 92},
    {"name": "Scientist", "theme": "City", "score": 90},
    {"name": "Police Officer", "theme": "City", "score": 89},
    {"name": "Astronaut", "theme": "Space", "score": 87},
]


def search(embedding, top_k: int = 5) -> List[Dict[str, Any]]:
    """Return a ranked list of LEGO character matches using a lightweight heuristic."""
    if not embedding:
        return []

    magnitude = sum(value * value for value in embedding) ** 0.5
    if magnitude == 0:
        magnitude = 1.0

    normalized = [value / magnitude for value in embedding]
    base = sum(normalized[:16])

    results: List[Dict[str, Any]] = []
    for card in LEGOCARDS:
        score = round(min(99, max(70, int((base * 100) % 30) + card["score"] - 70)), 2)
        results.append({
            "name": card["name"],
            "theme": card["theme"],
            "score": score,
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]
