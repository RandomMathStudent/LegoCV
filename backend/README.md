Backend (FastAPI)

Minimal scaffold for the LEGO Lookalike backend.

Setup:

1. From the repository root, create the shared virtualenv: `python -m venv .venv`
2. Activate it: `source .venv/bin/activate`
3. Install backend dependencies: `pip install -r backend/requirements.txt`
4. Change into `backend/` and run: `uvicorn main:app --reload --env-file .env --port 8000`

Endpoints:
- `POST /analyze` accepts `multipart/form-data` with `image` file and returns matches + avatar stub.

## Hosted VLM extraction (optional)

The backend returns schema-stable `unknown` semantic attributes by default. To
enable image-based semantic extraction through an OpenAI-compatible vision API,
set these environment variables before starting the server:

- `VLM_API_KEY` (required)
- `VLM_API_URL` (optional; defaults to OpenAI chat completions)
- `VLM_MODEL` (optional; defaults to `gpt-4.1-mini`)
- `VLM_TIMEOUT_SECONDS` (optional; defaults to `20`)

Put local values in `backend/.env`; it is ignored by Git. Start the backend with
`--env-file .env` so those values are loaded. The key is sent only to the
configured `VLM_API_URL`; do not commit it to the repository.
