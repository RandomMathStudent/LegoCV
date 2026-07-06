from typing import Tuple, Dict, Any

def build_avatar(features: Dict[str, Any]) -> Tuple[Dict[str, str], bytes]:
    """Stub: pick parts from asset library and composite PNG bytes.
    Return (avatar_spec, png_bytes).
    """
    spec = {
        "hair": "brown_short",
        "face": "smile",
        "torso": "blue_hoodie",
        "legs": "jeans",
        "accessory": "coffee"
    }
    # Placeholder empty PNG bytes
    png = b""
    return spec, png
