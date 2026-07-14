from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

try:
    from ..services.pipeline import run_analysis_pipeline
except ImportError:  # pragma: no cover
    from services.pipeline import run_analysis_pipeline

router = APIRouter()


@router.post('/analyze')
async def analyze(image: UploadFile = File(...)):
    img_bytes = await image.read()

    response = run_analysis_pipeline(img_bytes, top_k=5)
    return JSONResponse(content=response)
