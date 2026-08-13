Backend (FastAPI)

Minimal scaffold for the LEGO Lookalike backend.

Setup:

1. From the repository root, create the shared virtualenv: `python -m venv .venv`
2. Activate it: `source .venv/bin/activate`
3. Install backend dependencies: `pip install -r backend/requirements.txt`
4. Change into `backend/` and run: `uvicorn main:app --reload --env-file .env --port 8000`

Endpoints:
- `POST /analyze` accepts `multipart/form-data` with `image` file and returns matches + avatar stub.

## Local development

The default `VLM_MODE=mock` returns deterministic, schema-valid semantic
attributes. It does not load Qwen, PyTorch, CUDA, or any GPU package, so the
complete FastAPI analysis flow works on a CPU-only laptop.

This **direct mock** is the fastest option for unit tests: FastAPI calls its
in-process deterministic implementation and makes no network request.

Copy `.env.example` to `.env` if configuration is needed. The local default is:

`VLM_MODE=mock`

## Remote GPU VLM inference

For production, run the separate service in [vlm_server](../vlm_server/) on one
GPU with one Qwen model process. Configure this backend, not the browser:

`VLM_MODE=remote`

`VLM_URL=http://<GPU-SERVER>:9000/analyze`

`VLM_TIMEOUT_SECONDS=60`

The request path remains **Next.js → FastAPI → VLM server → Qwen**. If the
remote server fails, `/analyze` returns an error rather than a mock result.

For CPU-only end-to-end testing, start [mock_vlm_server](../mock_vlm_server/)
on port 9000 and set `VLM_MODE=remote`. This **HTTP mock** follows the same
multipart `/analyze` contract as the GPU service, so FastAPI sends the uploaded
image over HTTP exactly as it will in production.
