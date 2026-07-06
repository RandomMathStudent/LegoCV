from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from services import detector, embedding, feature_extractor, lego_matcher, avatar_builder

router = APIRouter()

@router.post('/analyze')
async def analyze(image: UploadFile = File(...)):
    # Read image bytes
    img_bytes = await image.read()

    # Placeholder pipeline: the services contain stubs to be implemented
    aligned = detector.detect_and_align(img_bytes)
    features = feature_extractor.extract_features(aligned)
    emb = embedding.embed_image(aligned)
    matches = lego_matcher.search(emb, top_k=5)
    avatar_spec, avatar_png = avatar_builder.build_avatar(features)

    response = {
        "matches": matches,
        "avatar": avatar_spec,
        "avatar_image": "data:image/png;base64,REPLACE_WITH_REAL_IMAGE"
    }
    return JSONResponse(content=response)
