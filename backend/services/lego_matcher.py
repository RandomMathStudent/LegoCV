from typing import List, Dict, Any

# TODO: integrate FAISS index and metadata store

def search(embedding, top_k: int = 5) -> List[Dict[str, Any]]:
    """Stub: return top-k matching LEGO characters with scores.
    """
    # Example fixed results for now
    return [
        {"name": "Emmet", "score": 95},
        {"name": "Pirate Captain", "score": 92},
        {"name": "Scientist", "score": 90},
        {"name": "Police Officer", "score": 89},
        {"name": "Astronaut", "score": 87}
    ]
