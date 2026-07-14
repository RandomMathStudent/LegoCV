from __future__ import annotations

from typing import Dict


def infer_face_shape(geometry: Dict[str, float]) -> str:
    """Infer coarse face shape from geometric ratios.

    This is a placeholder heuristic that keeps the pipeline deterministic until
    a stronger classifier is introduced.
    """
    face_width = geometry.get("face_width", 0.0)
    face_height = geometry.get("face_height", 1.0)
    ratio = face_width / max(face_height, 1e-6)

    if ratio > 0.95:
        return "round"
    if ratio < 0.75:
        return "long"
    return "oval"
