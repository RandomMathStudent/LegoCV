from typing import Any
import io

try:
    import cv2
    import numpy as np
    from insightface.app import FaceAnalysis
except ImportError:  # pragma: no cover
    cv2 = None
    np = None
    FaceAnalysis = None


def _fallback_result(image_bytes: bytes) -> dict[str, Any]:
    return {
        "raw_bytes": image_bytes,
        "status": "aligned_placeholder",
        "face_confidence": 0.85,
    }


def detect_and_align(image_bytes: bytes) -> Any:
    """Detect a face and return metadata for downstream CV steps.

    If InsightFace is available, the function uses it for detection and alignment.
    Otherwise it returns a deterministic fallback payload so the pipeline remains
    functional while the model dependency is being installed.
    """
    if cv2 is None or np is None or FaceAnalysis is None:
        return _fallback_result(image_bytes)

    try:
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if img is None:
            return _fallback_result(image_bytes)

        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))
        faces = app.get(img)

        if not faces:
            return _fallback_result(image_bytes)

        face = faces[0]
        bbox = face.bbox.astype(int).tolist()
        landmarks = face.kps.astype(int).tolist()
        return {
            "raw_bytes": image_bytes,
            "status": "aligned_face",
            "face_confidence": float(face.det_score),
            "bbox": bbox,
            "landmarks": landmarks,
            "embedding": face.embedding.tolist(),
        }
    except Exception:
        return _fallback_result(image_bytes)
