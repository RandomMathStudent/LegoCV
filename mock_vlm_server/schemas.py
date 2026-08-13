"""The public semantic response contract shared with the GPU VLM service."""

from __future__ import annotations

from pydantic import BaseModel


class HairSemantics(BaseModel):
    colour: str
    length: str
    style: str
    fringe: str


class GlassesSemantics(BaseModel):
    present: bool
    shape: str
    frame_colour: str


class FacialHairSemantics(BaseModel):
    beard: str
    mustache: str
    goatee: str


class SemanticResponse(BaseModel):
    hair: HairSemantics
    glasses: GlassesSemantics
    facial_hair: FacialHairSemantics
    expression: str
    skin_tone: str
    estimated_age: int | None
    gender_presentation: str | None


def deterministic_semantics() -> SemanticResponse:
    """Return the schema-stable response used for local HTTP testing."""
    return SemanticResponse(
        hair=HairSemantics(colour="brown", length="medium", style="wavy", fringe="unknown"),
        glasses=GlassesSemantics(present=True, shape="round", frame_colour="black"),
        facial_hair=FacialHairSemantics(beard="unknown", mustache="unknown", goatee="unknown"),
        expression="neutral",
        skin_tone="light",
        estimated_age=None,
        gender_presentation=None,
    )
