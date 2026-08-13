"""CPU-only HTTP mock implementing the LegoCV VLM service contract."""

from __future__ import annotations

import asyncio
import os
import random

from fastapi import FastAPI, File, HTTPException, UploadFile, status

from .schemas import SemanticResponse, deterministic_semantics


app = FastAPI(title="LegoCV Mock VLM Inference")
_SUPPORTED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/octet-stream"}


def _non_negative_float(name: str, default: float = 0.0) -> float:
    """Read a non-negative test setting without accepting malformed values."""
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as error:
        raise HTTPException(status_code=500, detail=f"Invalid {name} configuration") from error
    if value < 0:
        raise HTTPException(status_code=500, detail=f"Invalid {name} configuration")
    return value


def _failure_rate() -> float:
    rate = _non_negative_float("MOCK_VLM_FAILURE_RATE")
    if rate > 1:
        raise HTTPException(status_code=500, detail="Invalid MOCK_VLM_FAILURE_RATE configuration")
    return rate


@app.get("/health")
def health() -> dict[str, str]:
    """Report process availability without requiring a model or image."""
    return {"status": "ok"}


@app.post("/analyze", response_model=SemanticResponse)
async def analyze(image: UploadFile = File(...)) -> SemanticResponse:
    """Validate an uploaded image and return deterministic semantic data."""
    if image.content_type not in _SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported image content type")

    try:
        image_bytes = await image.read()
    except OSError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image could not be read") from error
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Uploaded image is empty")

    delay = _non_negative_float("MOCK_VLM_DELAY_SECONDS")
    if delay:
        await asyncio.sleep(delay)
    if random.random() < _failure_rate():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Intentional mock VLM failure")

    return deterministic_semantics()
