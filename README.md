# LEGO Lookalike & Custom Minifigure Generator

This workspace contains an MVP scaffold for the LEGO Lookalike project (frontend + backend).

Project goal: capture a user photo, find the closest LEGO minifigure match, and assemble a custom minifigure avatar from reusable LEGO parts.

## Documentation
- [docs/design.md](docs/design.md) — product and technical design overview
- [docs/architecture-spec.md](docs/architecture-spec.md) — end-to-end pipeline and model architecture specification
- [docs/todo.md](docs/todo.md) — implementation checklist and roadmap
- [docs/implementation-notes.md](docs/implementation-notes.md) — maintainability and architecture notes

## Project Structure
- [frontend/](frontend/) — Next.js frontend and webcam capture UI
- [backend/](backend/) — FastAPI backend and analysis pipeline scaffold

See [frontend/README.md](frontend/README.md) and [backend/README.md](backend/README.md) for quick start instructions.

## Local Development

Activate the project environment with `source .venv/bin/activate`. Start the
CPU-only FastAPI backend from [backend](backend/) with `uvicorn main:app --reload`,
then start the frontend from [frontend](frontend/) with `npm run dev`.

The backend defaults to `VLM_MODE=mock`, so local analysis requires no GPU,
Qwen, PyTorch, or CUDA. Future production deployments use the private path:

`Next.js → FastAPI → VLM server → Qwen`

Set `VLM_MODE=remote` and `VLM_URL=http://<GPU-SERVER>:9000/analyze` in the
backend environment to use the separate GPU service.

## HTTP Mock VLM

To test the production network boundary on a CPU-only machine, start the
standalone mock service from the repository root with
`uvicorn mock_vlm_server.main:app --host 0.0.0.0 --port 9000 --reload`.
Then start the backend with `VLM_MODE=remote` and
`VLM_URL=http://localhost:9000/analyze`. See
[mock_vlm_server/README.md](mock_vlm_server/README.md) for its test latency and
failure controls.
