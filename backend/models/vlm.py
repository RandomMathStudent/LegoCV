from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any, Dict, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LOGGER = logging.getLogger(__name__)

_DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"
_DEFAULT_MODEL = "gpt-4.1-mini"
_HAIR_COLOURS = {"black", "brown", "blonde", "red", "grey", "white"}
_HAIR_STYLES = {"straight", "curly", "wavy", "afro", "buzz", "ponytail", "braids"}
_EXPRESSIONS = {"smile", "neutral", "frown", "open_mouth"}
_SKIN_TONES = {"light", "medium", "dark"}

_SYSTEM_PROMPT = """You extract only visible, LEGO-minifigure-relevant facial attributes.
Return one JSON object and no markdown. Use unknown when an attribute is not visible.
Use these exact enums where applicable:
- hair.colour: black, brown, blonde, red, grey, white, unknown
- hair.style: straight, curly, wavy, afro, buzz, ponytail, braids, unknown
- expression: smile, neutral, frown, open_mouth, unknown
- skin_tone: light, medium, dark, unknown
Return this shape:
{
  "hair": {"colour": "...", "length": "...", "style": "...", "fringe": "..."},
  "glasses": {"present": false, "shape": "...", "frame_colour": "..."},
  "facial_hair": {"beard": "...", "mustache": "...", "goatee": "..."},
  "expression": "...",
  "skin_tone": "...",
  "estimated_age": null,
  "gender_presentation": null
}
Do not guess estimated_age or gender_presentation; set both to null unless clearly supplied by the person."""


def _fallback_semantics() -> Dict[str, object]:
    """Return a contract-compliant result when VLM extraction is unavailable."""
    return {
        "hair": {"colour": "unknown", "length": "unknown", "style": "unknown", "fringe": "unknown"},
        "glasses": {"present": False, "shape": "unknown", "frame_colour": "unknown"},
        "facial_hair": {"beard": "unknown", "mustache": "unknown", "goatee": "unknown"},
        "expression": "unknown",
        "skin_tone": "unknown",
        "estimated_age": None,
        "gender_presentation": None,
    }


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _normalise_enum(value: object, allowed: set[str], aliases: Mapping[str, str] | None = None) -> str:
    normalized = str(value or "").strip().lower()
    normalized = (aliases or {}).get(normalized, normalized)
    return normalized if normalized in allowed else "unknown"


def _normalise_response(payload: object) -> Dict[str, object]:
    """Defensively convert untrusted VLM JSON into the API's stable schema."""
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
            "present": bool(glasses.get("present", False)),
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


def _parse_json_object(content: str) -> Mapping[str, Any]:
    """Parse plain or fenced JSON returned by a compatible chat-completions API."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    parsed = json.loads(content)
    if not isinstance(parsed, Mapping):
        raise ValueError("VLM response was not a JSON object")
    return parsed


def _call_hosted_vlm(image_bytes: bytes, api_key: str) -> Mapping[str, Any]:
    mime_type = "image/png" if image_bytes.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg"
    image_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    request_body = {
        "model": os.getenv("VLM_MODEL", _DEFAULT_MODEL),
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the requested visible attributes from this image."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
    }
    request = Request(
        os.getenv("VLM_API_URL", _DEFAULT_API_URL),
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=float(os.getenv("VLM_TIMEOUT_SECONDS", "20"))) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    choices = _as_mapping(response_payload).get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("VLM response did not contain choices")
    message = _as_mapping(_as_mapping(choices[0]).get("message"))
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError("VLM response did not contain text content")
    return _parse_json_object(content)


def extract_semantics_from_image(image_bytes: bytes) -> Dict[str, object]:
    """Extract semantic attributes through a configured hosted VLM.

    Set ``VLM_API_KEY`` to enable extraction. ``VLM_API_URL`` and ``VLM_MODEL``
    support OpenAI-compatible providers. A schema-stable unknown result is
    returned if the provider is not configured or cannot complete the request.
    """
    api_key = os.getenv("VLM_API_KEY")
    if not api_key or not image_bytes:
        return _fallback_semantics()

    try:
        return _normalise_response(_call_hosted_vlm(image_bytes, api_key))
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError) as error:
        LOGGER.warning("VLM feature extraction failed; using unknown semantics: %s", error)
        return _fallback_semantics()
