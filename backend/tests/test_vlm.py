import json

from models import vlm


def test_extract_semantics_uses_unknown_fallback_without_key(monkeypatch):
    monkeypatch.delenv("VLM_API_KEY", raising=False)

    result = vlm.extract_semantics_from_image(b"image-bytes")

    assert result["hair"]["colour"] == "unknown"
    assert result["hair"]["style"] == "unknown"
    assert result["expression"] == "unknown"


def test_extract_semantics_normalises_hosted_response(monkeypatch):
    monkeypatch.setenv("VLM_API_KEY", "test-key")
    hosted_response = {
        "hair": {"colour": "Gray", "length": "Short", "style": "Curly", "fringe": "None"},
        "glasses": {"present": True, "shape": "Round", "frame_colour": "Black"},
        "facial_hair": {"beard": "None", "mustache": "Light", "goatee": "None"},
        "expression": "Smile",
        "skin_tone": "Medium",
        "estimated_age": 30,
        "gender_presentation": "woman",
    }
    monkeypatch.setattr(vlm, "_call_hosted_vlm", lambda image_bytes, api_key: hosted_response)

    result = vlm.extract_semantics_from_image(b"image-bytes")

    assert result["hair"] == {"colour": "grey", "length": "short", "style": "curly", "fringe": "none"}
    assert result["expression"] == "smile"
    assert result["estimated_age"] == 30
    assert result["gender_presentation"] is None


def test_parse_json_object_accepts_fenced_json():
    parsed = vlm._parse_json_object("```json\n{\"expression\": \"neutral\"}\n```")

    assert json.dumps(parsed) == '{"expression": "neutral"}'