# LegoCV GPU VLM Service

This service hosts one `Qwen/Qwen2.5-VL-7B-Instruct` model per process on a GPU machine. It is intentionally separate from the CPU-only FastAPI application.

Install its dependencies on the GPU host, then start one worker:

`uvicorn main:app --host 0.0.0.0 --port 9000`

Endpoints:

- `GET /health`
- `POST /analyze` with multipart field `image`

Configure the main backend with `VLM_MODE=remote` and `VLM_URL=http://<GPU-SERVER>:9000/analyze`. Keep this service private; browsers must communicate only with the Next.js application.
