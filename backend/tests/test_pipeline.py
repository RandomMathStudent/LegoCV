from services.detector import detect_and_align
from services.feature_extractor import extract_features
from services.embedding import embed_image
from services.lego_matcher import search
from services.pipeline import run_analysis_pipeline


def test_pipeline_stub_outputs_expected_shapes():
    image_bytes = b"fake-image-bytes"
    aligned = detect_and_align(image_bytes)
    features = extract_features(aligned)
    embedding = embed_image(aligned)
    matches = search(embedding, top_k=3)

    assert isinstance(aligned, dict)
    assert isinstance(features, dict)
    assert isinstance(embedding, list)
    assert len(embedding) == 512
    assert isinstance(matches, list)
    assert len(matches) >= 1


def test_feature_extractor_handles_insightface_payload():
    payload = {
        "status": "aligned_face",
        "face_confidence": 0.95,
        "landmarks": [[0, 0], [10, 10]],
    }

    features = extract_features(payload)

    assert features["glasses"] is False
    assert features["facial_hair"]["beard"] is False
    assert features["expression"] == "neutral"
    assert features["source"] == "insightface"
    assert features["landmark_count"] == 2


def test_new_orchestrator_returns_architecture_sections():
    result = run_analysis_pipeline(b"fake-image-bytes", top_k=5)

    assert "detected_face" in result
    assert "features" in result
    assert "ranking" in result
    assert "hair" in result["ranking"]
    assert isinstance(result["ranking"]["hair"], list)
    assert result["embedding_length"] == 512
