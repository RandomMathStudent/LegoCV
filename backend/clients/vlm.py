"""Schema-safe client for mock or remote visual-language-model inference."""

from __future__ import annotations

import os
from typing import Any, Mapping

import requests


_DEFAULT_TIMEOUT_SECONDS = 60.0
_HAIR_COLOURS = {"black", "brown", "blonde", "red", "grey", "white"}
_HAIR_STYLES = {"straight", "curly", "wavy", "afro", "buzz", "ponytail", "braids"}
_EXPRESSIONS = {"smile", "neutral", "frown", "open_mouth"}
_SKIN_TONES = {"light", "medium", "dark"}
_REQUIRED_GROUPS = {
    "hair": {"colour", "length", "style", "fringe"},
    "glasses": {"present", "shape", "frame_colour"},
    "facial_hair": {"beard", "mustache", "goatee"},
}
_REQUIRED_FIELDS = {"expression", "skin_tone", "estimated_age", "gender_presentation"}


class VLMClientError(RuntimeError):
    """Configured VLM inference cannot provide a valid response."""


def _mock_semantics() -> dict[str, object]:
    """Return stable development data without inspecting the uploaded image."""
    return {
        "hair": {"colour": "brown", "length": "medium", "style": "wavy", "fringe": "unknown"},
        "glasses": {"present": True, "shape": "round", "frame_colour": "black"},
        "facial_hair": {"beard": "unknown", "mustache": "unknown", "goatee": "unknown"},
        "expression": "neutral",
        "skin_tone": "light",
        "estimated_age": None,
        "gender_presentation": None,
    }


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _normalise_enum(value: object, allowed: set[str], aliases: Mapping[str, str] | None = None) -> str:
    normalized = str(value or "").strip().lower()
    normalized = (aliases or {}).get(normalized, normalized)
    return normalized if normalized in allowed else "unknown"


def _normalise_response(payload: object) -> dict[str, object]:
    """Convert untrusted VLM output into the stable semantic contract."""
    source = _as_mapping(payload)
    hair = _as_mapping(source.get("hair"))
    glasses = _as_mapping(source.get("glasses"))
    facial_hair = _as_mapping(source.get("facial_hair"))
    estimated_age = source.get("estimated_age")
    age = estimated_age if isinstance(estimated_age, int) and not isinstance(estimated_age, bool) and 0 <= estimated_age <= 120 else None
    return {
        "hair": {
            "colour": _normalise_enum(hair.get("colour"), _HAIR_COLOURS, {"gray": "grey", "blond": "blonde"}),
            "length": str(hair.get("length") or "unknown").strip().lower(),
            "style": _normalise_enum(hair.get("style"), _HAIR_STYLES),
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
        "expression": _normalise_enum(source.get("expression"), _EXPRESSIONS),
        "skin_tone": _normalise_enum(source.get("skin_tone"), _SKIN_TONES),
        "estimated_age": age,
        "gender_presentation": None,
    }


def _validate_response_structure(payload: object) -> Mapping[str, Any]:
    """Reject malformed remote responses before they reach the pipeline."""
    source = _as_mapping(payload)
    if not source:
        raise VLMClientError("VLM response must be a JSON object")
    for group, fields in _REQUIRED_GROUPS.items():
        value = _as_mapping(source.get(group))
        if not value or not fields.issubset(value):
            raise VLMClientError(f"VLM response has an invalid {group!r} object")
    if not _REQUIRED_FIELDS.issubset(source):
        raise VLMClientError("VLM response is missing required semantic fields")
    if not isinstance(source["glasses"].get("present"), bool):
        raise VLMClientError("VLM response glasses.present must be a boolean")
    return source


def _timeout_seconds() -> float:
    try:
        timeout = float(os.getenv("VLM_TIMEOUT_SECONDS", str(_DEFAULT_TIMEOUT_SECONDS)))
    except ValueError as error:
        raise VLMClientError("VLM_TIMEOUT_SECONDS must be a positive number") from error
    if timeout <= 0:
        raise VLMClientError("VLM_TIMEOUT_SECONDS must be a positive number")
    return timeout


def _remote_semantics(image_bytes: bytes) -> dict[str, object]:
    url = os.getenv("VLM_URL", "").strip()
    if not url:
        raise VLMClientError("VLM_URL is required when VLM_MODE=remote")
    try:
        response = requests.post(url, files={"image": ("upload.jpg", image_bytes, "application/octet-stream")}, timeout=_timeout_seconds())
        response.raise_for_status()
    except requests.Timeout as error:
        raise VLMClientError("VLM request timed out") from error
    except requests.ConnectionError as error:
        raise VLMClientError("VLM server could not be reached") from error
    except requests.RequestException as error:
        raise VLMClientError(f"VLM server returned an error: {error}") from error
    try:
        payload = response.json()
    except ValueError as error:
        raise VLMClientError("VLM server returned invalid JSON") from error
    return _normalise_response(_validate_response_structure(payload))


def analyze_image(image_bytes: bytes) -> dict[str, object]:
    """Use the configured mock or independently deployed VLM service."""
    mode = os.getenv("VLM_MODE", "mock").strip().lower()
    if mode == "mock":
        return _normalise_response(_mock_semantics())
    if mode == "remote":
        return _remote_semantics(image_bytes)
    raise VLMClientError("VLM_MODE must be either 'mock' or 'remote'")