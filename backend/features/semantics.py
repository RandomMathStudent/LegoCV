from __future__ import annotations

from typing import Any, Dict

try:
    from ..models import vlm
except ImportError:  # pragma: no cover
    from models import vlm


def extract_semantics(aligned_face: Any) -> Dict[str, Any]:
    """Route to VLM semantic extraction using available image bytes."""
    if isinstance(aligned_face, dict):
        image_bytes = aligned_face.get("raw_bytes", b"")
    else:
        image_bytes = b""
    return vlm.extract_semantics_from_image(image_bytes)
