"""Semantic response normalization shared by the GPU service boundary."""

from __future__ import annotations

from typing import Any, Mapping


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _enum(value: object, allowed: set[str], aliases: Mapping[str, str] | None = None) -> str:
    result = str(value or "").strip().lower()
    result = (aliases or {}).get(result, result)
    return result if result in allowed else "unknown"


def normalize(payload: object) -> dict[str, object]:
    """Return the LegoCV semantic schema from untrusted Qwen JSON."""
    source = _mapping(payload)
    hair = _mapping(source.get("hair"))
    glasses = _mapping(source.get("glasses"))
    facial_hair = _mapping(source.get("facial_hair"))
    age = source.get("estimated_age")
    return {
        "hair": {
            "colour": _enum(hair.get("colour"), {"black", "brown", "blonde", "red", "grey", "white"}, {"gray": "grey", "blond": "blonde"}),
            "length": str(hair.get("length") or "unknown").strip().lower(),
            "style": _enum(hair.get("style"), {"straight", "curly", "wavy", "afro", "buzz", "ponytail", "braids"}),
            "fringe": str(hair.get("fringe") or "unknown").strip().lower(),
        },
        "glasses": {
            "present": glasses.get("present") if isinstance(glasses.get("present"), bool) else False,
            "shape": str(glasses.get("shape") or "unknown").strip().lower(),
            "frame_colour": str(glasses.get("frame_colour") or "unknown").strip().lower(),
        },
        "facial_hair": {
            "beard": str(facial_hair.get("beard") or "unknown").strip().lower(),
            "mustache": str(facial_hair.get("mustache") or "unknown").strip().lower(),
            "goatee": str(facial_hair.get("goatee") or "unknown").strip().lower(),
        },
        "expression": _enum(source.get("expression"), {"smile", "neutral", "frown", "open_mouth"}),
        "skin_tone": _enum(source.get("skin_tone"), {"light", "medium", "dark"}),
        "estimated_age": age if isinstance(age, int) and not isinstance(age, bool) and 0 <= age <= 120 else None,
        "gender_presentation": None,
    }