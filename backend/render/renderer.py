from __future__ import annotations

from typing import Dict, Tuple


def render_avatar(_avatar_spec: Dict[str, str]) -> Tuple[str, bytes]:
    """Return a data URI placeholder and raw bytes placeholder for avatar rendering."""
    data_uri = "data:image/png;base64,REPLACE_WITH_REAL_IMAGE"
    return data_uri, b""
