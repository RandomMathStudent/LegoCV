from __future__ import annotations

from typing import Any, Dict, List

try:
    from ..database import repository
    from .scorer import weighted_score
except ImportError:  # pragma: no cover
    from database import repository
    from ranking.scorer import weighted_score


def rank_hair_parts(feature_vector: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
    """Return top-k ranked hair candidates using a simple weighted scaffold."""
    sparse = feature_vector.get("sparse", {}) if isinstance(feature_vector, dict) else {}
    candidates = repository.list_hair_parts()
    scored: List[Dict[str, Any]] = []

    for part in candidates:
        color_key = f"hair_colour_{part['colour'].lower()}"
        style_key = f"hair_style_{part['style'].lower()}"
        geometry_bonus = 0.6 + 0.4 * float(feature_vector.get("dense", [0.0])[0])

        final = weighted_score(
            {
                "hair": max(float(sparse.get(color_key, 0.0)), float(sparse.get(style_key, 0.0))),
                "face": 0.8,
                "expression": 0.8,
                "accessories": 0.7,
                "geometry": min(1.0, geometry_bonus),
            }
        )

        scored.append(
            {
                "part_id": part["part_id"],
                "category": "hair",
                "score": round(final, 4),
                "metadata": part,
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]
