Backend (FastAPI)

Minimal scaffold for the LEGO Lookalike backend.

Setup:

1. Create a virtualenv: `python -m venv .venv`
2. Activate it and install deps: `pip install -r requirements.txt`
3. Run: `uvicorn main:app --reload --port 8000`

Endpoints:
- `POST /analyze` accepts `multipart/form-data` with `image` file and returns matches + avatar stub.
