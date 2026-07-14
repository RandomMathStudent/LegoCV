from typing import List, Any
import hashlib


def embed_image(aligned_face: Any) -> List[float]:
    """Create a deterministic pseudo-embedding for the placeholder pipeline stage."""
    if isinstance(aligned_face, dict):
        seed = str(aligned_face.get("status", "aligned_placeholder"))
    else:
        seed = str(aligned_face)

    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    values: List[float] = []
    for byte in digest:
        values.append(byte / 255.0)

    while len(values) < 512:
        values.extend(values[: min(32, 512 - len(values))])

    return values[:512]
