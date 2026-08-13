from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

try:
    from ..clients.vlm import VLMClientError
    from ..services.pipeline import run_analysis_pipeline
except ImportError:  # pragma: no cover
    from clients.vlm import VLMClientError
    from services.pipeline import run_analysis_pipeline

router = APIRouter()


@router.post('/analyze')
async def analyze(image: UploadFile = File(...)):
    img_bytes = await image.read()

    try:
        response = run_analysis_pipeline(img_bytes, top_k=5)
    except VLMClientError as error:
        raise HTTPException(status_code=502, detail=f"VLM inference failed: {error}") from error
    return JSONResponse(content=response)
