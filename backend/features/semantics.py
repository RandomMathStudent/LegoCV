from __future__ import annotations

from typing import Any, Dict

try:
    from ..clients.vlm import analyze_image
except ImportError:  # pragma: no cover
    from clients.vlm import analyze_image


def extract_semantics(aligned_face: Any) -> Dict[str, Any]:
    """Route to VLM semantic extraction using available image bytes."""
    if isinstance(aligned_face, dict):
        image_bytes = aligned_face.get("raw_bytes", b"")
    else:
        image_bytes = b""
    return analyze_image(image_bytes)
