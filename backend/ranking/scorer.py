from __future__ import annotations

from typing import Dict


DEFAULT_WEIGHTS = {
    "hair": 0.40,
    "face": 0.30,
    "expression": 0.10,
    "accessories": 0.10,
    "geometry": 0.10,
}


def weighted_score(component_scores: Dict[str, float], weights: Dict[str, float] | None = None) -> float:
    active_weights = weights or DEFAULT_WEIGHTS
    total = 0.0
    for key, weight in active_weights.items():
        total += float(component_scores.get(key, 0.0)) * float(weight)
    return round(total, 4)
