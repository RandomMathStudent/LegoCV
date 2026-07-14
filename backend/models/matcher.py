from __future__ import annotations

from typing import Dict, List


def to_rank_features(feature_vector: Dict[str, float]) -> List[float]:
    """Convert sparse named features into a stable dense order for rankers."""
    return [feature_vector[key] for key in sorted(feature_vector.keys())]
