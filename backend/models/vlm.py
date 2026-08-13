"""Deprecated GPU-free compatibility wrapper for the VLM client.

Qwen inference belongs exclusively to ``vlm_server``. New backend code should
import :func:`clients.vlm.analyze_image` directly.
"""

from __future__ import annotations

try:
    from ..clients.vlm import _normalise_enum, _normalise_response, analyze_image
except ImportError:  # pragma: no cover
    from clients.vlm import _normalise_enum, _normalise_response, analyze_image


def extract_semantics_from_image(image_bytes: bytes) -> dict[str, object]:
    """Preserve the former public entry point without importing model packages."""
    return analyze_image(image_bytes)


__all__ = ["_normalise_enum", "_normalise_response", "extract_semantics_from_image"]
