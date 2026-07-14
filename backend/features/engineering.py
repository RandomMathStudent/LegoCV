from __future__ import annotations

from typing import Any, Dict, List

try:
    from ..models import mediapipe, matcher
except ImportError:  # pragma: no cover
    from models import mediapipe, matcher


HAIR_COLOR_BUCKETS = ["black", "brown", "blonde", "red", "grey", "white"]
HAIR_STYLE_BUCKETS = ["straight", "curly", "wavy", "afro", "buzz", "ponytail", "braids"]


def _one_hot(value: str, buckets: List[str], prefix: str) -> Dict[str, float]:
    normalized = (value or "").strip().lower()
    return {f"{prefix}_{bucket}": 1.0 if normalized == bucket else 0.0 for bucket in buckets}


def build_feature_vector(geometry: Dict[str, float], semantics: Dict[str, Any]) -> Dict[str, Any]:
    """Combine geometry and semantics into a sparse+dense feature object."""
    hair = semantics.get("hair") if isinstance(semantics.get("hair"), dict) else {}

    sparse: Dict[str, float] = {}
    sparse.update(_one_hot(str(hair.get("colour", "")), HAIR_COLOR_BUCKETS, "hair_colour"))
    sparse.update(_one_hot(str(hair.get("style", "")), HAIR_STYLE_BUCKETS, "hair_style"))

    face_shape = mediapipe.infer_face_shape(geometry)
    sparse[f"face_shape_{face_shape}"] = 1.0

    dense = matcher.to_rank_features({
        "eye_spacing": float(geometry.get("eye_spacing", 0.0)),
        "face_height": float(geometry.get("face_height", 0.0)),
        "face_width": float(geometry.get("face_width", 0.0)),
        "jaw_width": float(geometry.get("jaw_width", 0.0)),
        "smile": float(geometry.get("smile", 0.0)),
    })

    return {
        "dense": dense,
        "sparse": sparse,
        "face_shape": face_shape,
    }
