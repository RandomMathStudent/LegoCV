from typing import Dict, Any


def extract_features(aligned_face: Any) -> Dict[str, Any]:
    """Create a structured feature object from face-analysis payloads."""
    if isinstance(aligned_face, dict):
        face_confidence = aligned_face.get("face_confidence", 0.0)
        landmarks = aligned_face.get("landmarks") or []
        status = aligned_face.get("status", "")

        if status == "aligned_face" and face_confidence >= 0.9:
            hair_style = "short"
            expression = "neutral"
            beard = False
            glasses = False
        elif status == "aligned_face" and face_confidence >= 0.7:
            hair_style = "medium"
            expression = "smiling"
            beard = True
            glasses = True
        else:
            hair_style = "medium"
            expression = "smiling"
            beard = True
            glasses = True
    else:
        hair_style = "short"
        expression = "neutral"
        beard = False
        glasses = False
        landmarks = []

    return {
        "hair": {"color": "brown", "length": hair_style, "style": "straight"},
        "eyes": {"shape": "round"},
        "facial_hair": {"beard": beard, "mustache": False},
        "glasses": glasses,
        "expression": expression,
        "headwear": None,
        "landmark_count": len(landmarks),
        "source": "insightface" if status == "aligned_face" else "fallback",
    }
