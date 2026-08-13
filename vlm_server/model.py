"""Qwen2.5-VL inference adapter used only by the GPU-hosted VLM service."""

from __future__ import annotations

import base64
import json
import re
from typing import Any, Mapping


MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"
_model: Any | None = None
_processor: Any | None = None


def _image_data_uri(image_bytes: bytes) -> str:
    mime_type = "image/png" if image_bytes.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg"
    return f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def _parse_json(content: str) -> Mapping[str, Any]:
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        raise ValueError("Qwen response did not contain a JSON object")
    payload = json.loads(match.group(0))
    if not isinstance(payload, Mapping):
        raise ValueError("Qwen response was not a JSON object")
    return payload


def load_model() -> None:
    """Load one Qwen model instance for one GPU-serving process."""
    global _model, _processor
    if _model is not None:
        return
    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    _model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, torch_dtype=torch.bfloat16, device_map="auto"
    )
    _processor = AutoProcessor.from_pretrained(MODEL_NAME)


def analyze_image(image_bytes: bytes) -> Mapping[str, Any]:
    """Run one image through the already loaded Qwen model."""
    if _model is None or _processor is None:
        raise RuntimeError("Qwen model has not been loaded")
    import torch
    from qwen_vl_utils import process_vision_info

    prompt = """Return exactly one JSON object with hair, glasses, facial_hair, expression, skin_tone, estimated_age, and gender_presentation. Use unknown for uncertain fields and null for estimated_age and gender_presentation."""
    messages = [{"role": "user", "content": [{"type": "image", "image": _image_data_uri(image_bytes)}, {"type": "text", "text": prompt}]}]
    text = _processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = _processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt").to(_model.device)
    with torch.inference_mode():
        generated = _model.generate(**inputs, max_new_tokens=256, do_sample=False)
    response = _processor.batch_decode(
        [output[len(source):] for source, output in zip(inputs.input_ids, generated)],
        skip_special_tokens=True,
    )[0]
    return _parse_json(response)
