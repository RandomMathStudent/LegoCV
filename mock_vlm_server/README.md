# LegoCV CPU-Only Mock VLM Server

This standalone FastAPI service is a CPU-only HTTP mock of the future Qwen VLM
inference server. It returns deterministic, schema-valid LEGO semantic data and
never imports or requires a GPU, CUDA, PyTorch, torchvision, Qwen,
Transformers, or `qwen-vl-utils`.

## Why it exists

Use it to exercise the same network boundary used in production without
provisioning a model server:

```text
Next.js
  ↓
FastAPI
  ↓ HTTP
Mock VLM :9000
```

The main backend treats this server exactly like the future GPU deployment.

## Start the service

From the repository root, install the small service dependency set in a
CPU-only Python environment, then run:

```text
uvicorn mock_vlm_server.main:app --host 0.0.0.0 --port 9000 --reload
```

Endpoints:

- `GET /health` returns `{"status": "ok"}`.
- `POST /analyze` accepts multipart field `image` and returns the shared
  semantic response contract.

## Configure LegoCV FastAPI

Set these environment variables when starting the main backend:

```text
VLM_MODE=remote
VLM_URL=http://localhost:9000/analyze
VLM_TIMEOUT_SECONDS=60
```

The main backend sends the uploaded image to this service over HTTP. It does
not import this package or otherwise know that its configured remote endpoint
is a mock.

## Test controls

Both controls are optional and default to zero:

- `MOCK_VLM_DELAY_SECONDS=2` delays each `/analyze` response by approximately
  two seconds. Use it to test loading and timeouts.
- `MOCK_VLM_FAILURE_RATE=0.2` causes approximately 20% of `/analyze` requests
  to return HTTP 503. Use it only to test failure handling.

The controls are read by this service, not by the main FastAPI backend.

## Production replacement

The CPU-only service and [the GPU VLM service](../vlm_server/README.md) expose
matching endpoints: `GET /health` and `POST /analyze`. Production changes only
`VLM_URL`, for example to `http://gpu-server:9000/analyze`; the GPU service
then hosts `Qwen/Qwen2.5-VL-7B-Instruct` behind the same application-facing
contract.
