from __future__ import annotations

from typing import Dict


def extract_semantics_from_image(_image_bytes: bytes) -> Dict[str, object]:
    """Placeholder VLM contract.

    Future implementations should call an on-device or hosted VLM and return a
    JSON-safe payload matching the architecture spec.
    """
    return {
        "hair": {
            "colour": "brown",
            "length": "medium",
            "style": "straight",
            "fringe": "unknown",
        },
        "glasses": {"present": False, "shape": "none", "frame_colour": "none"},
        "facial_hair": {"beard": "none", "mustache": "none", "goatee": "none"},
        "expression": "neutral",
        "skin_tone": "medium",
        "estimated_age": None,
        "gender_presentation": None,
    }
