"""Integration tests for the real HTTP boundary to the CPU-only mock VLM."""

from __future__ import annotations

import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest
import requests
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
from mock_vlm_server.main import app as mock_vlm_app
sys.path.pop(0)

from main import app as backend_app


_SMALL_PNG = b"\x89PNG\r\n\x1a\nmock-image"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def _running_server(app) -> Iterator[str]:
    """Run one ASGI app on localhost so tests cross a real HTTP boundary."""
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", access_log=False)
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            if requests.get(f"{base_url}/health", timeout=0.2).status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(0.02)
    else:
        server.should_exit = True
        thread.join(timeout=2)
        raise RuntimeError(f"Server did not start at {base_url}")

    try:
        yield base_url
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@pytest.fixture
def mock_vlm_url() -> Iterator[str]:
    with _running_server(mock_vlm_app) as url:
        yield url


def _image_upload() -> dict[str, tuple[str, bytes, str]]:
    return {"image": ("test.png", _SMALL_PNG, "image/png")}


def test_mock_vlm_health_analyze_and_validation(mock_vlm_url):
    assert requests.get(f"{mock_vlm_url}/health", timeout=2).json() == {"status": "ok"}

    response = requests.post(f"{mock_vlm_url}/analyze", files=_image_upload(), timeout=2)
    assert response.status_code == 200
    assert response.json()["hair"] == {
        "colour": "brown",
        "length": "medium",
        "style": "wavy",
        "fringe": "unknown",
    }
    assert response.json()["glasses"]["present"] is True

    assert requests.post(f"{mock_vlm_url}/analyze", timeout=2).status_code == 422
    assert requests.post(
        f"{mock_vlm_url}/analyze",
        files={"image": ("note.txt", b"not an image", "text/plain")},
        timeout=2,
    ).status_code == 415
    assert requests.post(
        f"{mock_vlm_url}/analyze",
        files={"image": ("empty.png", b"", "image/png")},
        timeout=2,
    ).status_code == 422


def test_mock_vlm_accepts_concurrent_requests(mock_vlm_url):
    def post_image() -> int:
        return requests.post(f"{mock_vlm_url}/analyze", files=_image_upload(), timeout=2).status_code

    with ThreadPoolExecutor(max_workers=4) as executor:
        statuses = list(executor.map(lambda _: post_image(), range(4)))

    assert statuses == [200, 200, 200, 200]


def test_mock_vlm_applies_optional_delay(monkeypatch, mock_vlm_url):
    monkeypatch.setenv("MOCK_VLM_DELAY_SECONDS", "0.05")

    started = time.monotonic()
    response = requests.post(f"{mock_vlm_url}/analyze", files=_image_upload(), timeout=2)

    assert response.status_code == 200
    assert time.monotonic() - started >= 0.04


def test_backend_remote_mode_uses_mock_vlm_over_http(monkeypatch, mock_vlm_url):
    monkeypatch.setenv("VLM_MODE", "remote")
    monkeypatch.setenv("VLM_URL", f"{mock_vlm_url}/analyze")
    monkeypatch.setenv("VLM_TIMEOUT_SECONDS", "2")

    with _running_server(backend_app) as backend_url:
        response = requests.post(f"{backend_url}/analyze", files=_image_upload(), timeout=5)

    assert response.status_code == 200
    semantics = response.json()["features"]["semantics"]
    assert semantics["hair"]["colour"] == "brown"
    assert semantics["hair"]["style"] == "wavy"
    assert semantics["glasses"]["present"] is True


def test_backend_returns_controlled_error_for_remote_failure(monkeypatch, mock_vlm_url):
    monkeypatch.setenv("VLM_MODE", "remote")
    monkeypatch.setenv("VLM_URL", f"{mock_vlm_url}/analyze")
    monkeypatch.setenv("VLM_TIMEOUT_SECONDS", "2")
    monkeypatch.setenv("MOCK_VLM_FAILURE_RATE", "1")

    with _running_server(backend_app) as backend_url:
        response = requests.post(f"{backend_url}/analyze", files=_image_upload(), timeout=5)

    assert response.status_code == 502
    assert response.json()["detail"].startswith("VLM inference failed:")
    assert "Traceback" not in response.text
