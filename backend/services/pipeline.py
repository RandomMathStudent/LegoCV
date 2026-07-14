from __future__ import annotations

from typing import Any, Dict

try:
    from ..features.geometry import extract_geometry
    from ..features.semantics import extract_semantics
    from ..features.engineering import build_feature_vector
    from ..ranking.ranker import rank_hair_parts
    from ..render.renderer import render_avatar
    from . import detector, embedding, lego_matcher, avatar_builder
except ImportError:  # pragma: no cover
    from features.geometry import extract_geometry
    from features.semantics import extract_semantics
    from features.engineering import build_feature_vector
    from ranking.ranker import rank_hair_parts
    from render.renderer import render_avatar
    from services import detector, embedding, lego_matcher, avatar_builder


def run_analysis_pipeline(image_bytes: bytes, top_k: int = 5) -> Dict[str, Any]:
    """Architecture-aligned pipeline orchestrator for analyze endpoint."""
    aligned = detector.detect_and_align(image_bytes)
    geometry = extract_geometry(aligned)
    semantics = extract_semantics(aligned)
    feature_vector = build_feature_vector(geometry, semantics)

    emb = embedding.embed_image(aligned)
    legacy_matches = lego_matcher.search(emb, top_k=top_k)
    ranked_hair = rank_hair_parts(feature_vector, top_k=min(10, max(top_k, 3)))

    # Keep current API-compatible avatar contract while the new renderer is scaffolded.
    avatar_spec, _ = avatar_builder.build_avatar(
        {
            "geometry": geometry,
            "semantics": semantics,
            "feature_vector": feature_vector,
            "ranked_hair": ranked_hair,
        }
    )
    avatar_image, _ = render_avatar(avatar_spec)

    response = {
        "detected_face": {
            "status": aligned.get("status", "aligned_placeholder") if isinstance(aligned, dict) else "aligned_placeholder",
            "face_confidence": aligned.get("face_confidence", 0.0) if isinstance(aligned, dict) else 0.0,
        },
        "features": {
            "geometry": geometry,
            "semantics": semantics,
            "engineered": {
                "dense_dim": len(feature_vector.get("dense", [])),
                "sparse_dim": len(feature_vector.get("sparse", {})),
                "face_shape": feature_vector.get("face_shape", "unknown"),
            },
        },
        "embedding_length": len(emb),
        "matches": legacy_matches,
        "avatar": avatar_spec,
        "avatar_image": avatar_image,
        "ranking": {
            "hair": ranked_hair,
        },
    }

    return response
