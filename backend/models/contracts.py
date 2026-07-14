from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class BoundingBox(TypedDict):
    x: int
    y: int
    width: int
    height: int


class FaceDetectionResult(TypedDict, total=False):
    status: str
    face_confidence: float
    bbox: BoundingBox
    landmarks: List[List[float]]
    raw_bytes: bytes
    primary_face_index: int


class GeometryFeatures(TypedDict, total=False):
    face_width: float
    face_height: float
    jaw_width: float
    jaw_angle: float
    eye_spacing: float
    smile: float
    head_pitch: float
    head_yaw: float
    head_roll: float


class SemanticAttributes(TypedDict, total=False):
    hair: Dict[str, Any]
    glasses: Dict[str, Any]
    facial_hair: Dict[str, Any]
    expression: str
    skin_tone: str
    estimated_age: Optional[int]
    gender_presentation: Optional[str]


class EngineeredFeatureVector(TypedDict):
    dense: List[float]
    sparse: Dict[str, float]


class PartScore(TypedDict):
    part_id: str
    category: str
    score: float
    metadata: Dict[str, Any]


class AnalyzeResult(TypedDict):
    detected_face: Dict[str, Any]
    features: Dict[str, Any]
    embedding_length: int
    matches: List[Dict[str, Any]]
    avatar: Dict[str, str]
    avatar_image: str
