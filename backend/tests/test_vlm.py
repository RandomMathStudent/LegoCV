import sys

import pytest
import requests

from clients import vlm


VALID_RESPONSE = {
    "hair": {"colour": "Gray", "length": "Short", "style": "Curly", "fringe": "None"},
    "glasses": {"present": True, "shape": "Round", "frame_colour": "Black"},
    "facial_hair": {"beard": "None", "mustache": "Light", "goatee": "None"},
    "expression": "Smile",
    "skin_tone": "Medium",
    "estimated_age": 30,
    "gender_presentation": "woman",
}


class Response:
    def __init__(self, payload=VALID_RESPONSE, status_error=None, json_error=None):
        self.payload = payload
        self.status_error = status_error
        self.json_error = json_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


def test_mock_mode_returns_deterministic_schema_without_gpu_imports(monkeypatch):
    monkeypatch.setenv("VLM_MODE", "mock")
    for module in ("torch", "torchvision", "transformers", "qwen_vl_utils"):
        monkeypatch.delitem(sys.modules, module, raising=False)

    result = vlm.analyze_image(b"not-an-image")

    assert result["hair"] == {"colour": "brown", "length": "medium", "style": "wavy", "fringe": "unknown"}
    assert result["glasses"]["present"] is True
    assert result["estimated_age"] is None
    assert result["gender_presentation"] is None
    assert not any(module in sys.modules for module in ("torch", "torchvision", "transformers", "qwen_vl_utils"))


def test_normalisation_handles_aliases_invalid_enums_and_invalid_age():
    payload = {**VALID_RESPONSE, "hair": {**VALID_RESPONSE["hair"], "colour": "blond", "style": "invalid"}, "estimated_age": "old"}

    result = vlm._normalise_response(payload)

    assert result["hair"]["colour"] == "blonde"
    assert result["hair"]["style"] == "unknown"
    assert result["estimated_age"] is None


def test_remote_mode_posts_multipart_and_normalises_response(monkeypatch):
    monkeypatch.setenv("VLM_MODE", "remote")
    monkeypatch.setenv("VLM_URL", "http://vlm.example/analyze")
    captured = {}

    def post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(vlm.requests, "post", post)
    result = vlm.analyze_image(b"image-bytes")

    assert captured["url"] == "http://vlm.example/analyze"
    assert captured["files"]["image"][1] == b"image-bytes"
    assert result["hair"]["colour"] == "grey"
    assert result["hair"]["style"] == "curly"
    assert result["expression"] == "smile"
    assert result["estimated_age"] == 30


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (requests.Timeout(), "timed out"),
        (requests.ConnectionError(), "could not be reached"),
        (requests.HTTPError("500 Server Error"), "returned an error"),
    ],
)
def test_remote_mode_raises_clear_errors_for_request_failures(monkeypatch, error, message):
    monkeypatch.setenv("VLM_MODE", "remote")
    monkeypatch.setenv("VLM_URL", "http://vlm.example/analyze")

    def post(*_args, **_kwargs):
        if isinstance(error, requests.HTTPError):
            return Response(status_error=error)
        raise error

    monkeypatch.setattr(vlm.requests, "post", post)
    with pytest.raises(vlm.VLMClientError, match=message):
        vlm.analyze_image(b"image-bytes")


def test_remote_mode_rejects_invalid_json_and_schema(monkeypatch):
    monkeypatch.setenv("VLM_MODE", "remote")
    monkeypatch.setenv("VLM_URL", "http://vlm.example/analyze")
    monkeypatch.setattr(vlm.requests, "post", lambda *_args, **_kwargs: Response(json_error=ValueError("bad json")))
    with pytest.raises(vlm.VLMClientError, match="invalid JSON"):
        vlm.analyze_image(b"image-bytes")

    monkeypatch.setattr(vlm.requests, "post", lambda *_args, **_kwargs: Response(payload={"hair": {}}))
    with pytest.raises(vlm.VLMClientError, match="invalid 'hair' object"):
        vlm.analyze_image(b"image-bytes")


def test_remote_mode_requires_url(monkeypatch):
    monkeypatch.setenv("VLM_MODE", "remote")
    monkeypatch.delenv("VLM_URL", raising=False)
    with pytest.raises(vlm.VLMClientError, match="VLM_URL"):
        vlm.analyze_image(b"image-bytes")
