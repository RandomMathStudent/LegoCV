from __future__ import annotations

from typing import Any, Dict, List


def _safe_span(points: List[List[float]], a: int, b: int) -> float:
    if len(points) <= max(a, b):
        return 0.0
    return abs(float(points[a][0]) - float(points[b][0]))


def extract_geometry(aligned_face: Any) -> Dict[str, float]:
    """Extract lightweight geometric features from detector output.

    The function is intentionally conservative and tolerant of partial payloads.
    """
    if not isinstance(aligned_face, dict):
        return {
            "face_width": 0.0,
            "face_height": 0.0,
            "jaw_width": 0.0,
            "jaw_angle": 0.0,
            "eye_spacing": 0.0,
            "smile": 0.0,
            "head_pitch": 0.0,
            "head_yaw": 0.0,
            "head_roll": 0.0,
        }

    bbox = aligned_face.get("bbox") or [0, 0, 0, 0]
    landmarks = aligned_face.get("landmarks") or []

    width = float(max(0, bbox[2] - bbox[0])) if len(bbox) >= 4 else 0.0
    height = float(max(0, bbox[3] - bbox[1])) if len(bbox) >= 4 else 0.0

    # Placeholders based on landmark spreads when available.
    eye_spacing = _safe_span(landmarks, 0, 1) if landmarks else 0.0
    jaw_width = _safe_span(landmarks, 2, 3) if len(landmarks) > 3 else width * 0.6

    return {
        "face_width": round(width / 512.0, 4),
        "face_height": round(height / 512.0, 4),
        "jaw_width": round(jaw_width / 512.0, 4),
        "jaw_angle": 118.0,
        "eye_spacing": round(eye_spacing / 512.0, 4),
        "smile": 0.5,
        "head_pitch": 0.0,
        "head_yaw": 0.0,
        "head_roll": 0.0,
    }
