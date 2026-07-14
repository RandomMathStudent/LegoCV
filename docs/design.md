# LEGO Lookalike & Custom Minifigure Generator

## 1. Product Summary

This project builds a web application that lets users capture a photo, identify the LEGO minifigure they most resemble, generate a custom LEGO-style avatar from reusable parts, and download or share the result.

For the detailed technical pipeline and model-stage specification, see [architecture-spec.md](architecture-spec.md).

## 2. Goals

- Let users capture or upload a face photo from the browser.
- Match the face against a LEGO character database.
- Generate a layered LEGO-style avatar using reusable asset parts.
- Expose a simple frontend and backend workflow for future CV/model upgrades.

## 3. User Experience

### Core Flow
1. Open the app.
2. Grant webcam access.
3. Capture a photo.
4. Send the image to the backend.
5. Receive top LEGO matches and an avatar proposal.
6. Download or share the generated avatar.

## 4. Functional Scope

### MVP Features
- Webcam capture
- Image upload and analysis request
- Backend analysis pipeline stub
- Top 5 LEGO match results
- Avatar generation placeholder
- Download/share-ready UI shell

### Later Phases
- Real face detection and alignment
- Feature extraction and embeddings
- FAISS-backed similarity search
- Reusable LEGO asset composition
- Export/share flow polish
- 3D viewer and customization editor

## 5. System Architecture

### Frontend
- Next.js
- React
- TypeScript
- Webcam capture UI
- API proxy route to the backend

### Backend
- FastAPI
- Python
- OpenCV / Pillow / NumPy / FAISS-based pipeline
- Modular services for each analysis step

### Processing Pipeline
1. Receive image
2. Detect and align face
3. Extract appearance features
4. Generate an embedding
5. Search matching LEGO characters
6. Construct an avatar spec and image

## 6. Backend Service Boundaries

- detector: face detection and alignment
- feature_extractor: hair, eyes, glasses, facial hair, expression
- embedding: image embedding generation
- lego_matcher: similarity search over LEGO metadata
- avatar_builder: choose parts and compose avatar

## 7. Data Contracts

### Analysis Request
- Multipart form-data with an image file

### Analysis Response
```json
{
  "matches": [
    { "name": "Emmet", "score": 95 }
  ],
  "avatar": {
    "hair": "brown_short",
    "face": "smile",
    "torso": "blue_hoodie",
    "legs": "jeans",
    "accessory": "coffee"
  },
  "avatar_image": "data:image/png;base64,..."
}
```

## 8. Implementation Notes

- Keep each stage modular so models or asset libraries can be swapped later.
- Prefer processing images in memory and avoid permanent storage unless requested.
- Keep API responses JSON-serializable for easy frontend integration.
- Store logic and architecture decisions in the docs folder for transparency.

## 9. Milestones

### Milestone 1 — Foundation
- Frontend capture screen
- Backend API scaffold
- Basic analysis endpoint

### Milestone 2 — CV Processing
- Face detection
- Feature extraction
- Embedding generation
- LEGO matching

### Milestone 3 — Avatar Generation
- Asset selection
- Layer composition
- PNG export and preview

### Milestone 4 — Polish
- Loading states
- Better UI
- Mobile support
- Share/download flow
