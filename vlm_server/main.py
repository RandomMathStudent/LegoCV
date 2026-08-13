"""Single-process HTTP service for GPU-hosted Qwen2.5-VL inference."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile

from model import analyze_image, load_model
from schema import normalize


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_model()
    yield


app = FastAPI(title="LegoCV VLM Inference", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)) -> dict[str, object]:
    try:
        return normalize(analyze_image(await image.read()))
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=500, detail=f"VLM inference failed: {error}") from error
