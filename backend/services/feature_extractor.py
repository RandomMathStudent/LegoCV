from typing import Dict, Any

def extract_features(aligned_face: Any) -> Dict[str, Any]:
    """Stub: analyze hair color, facial hair, glasses, expression, etc.
    Return a JSON-serializable feature object.
    """
    return {
        "hair": {"color": "brown", "length": "short", "style": "straight"},
        "eyes": {"shape": "round"},
        "facial_hair": {"beard": False, "mustache": False},
        "glasses": False,
        "expression": "neutral",
        "headwear": None
    }
