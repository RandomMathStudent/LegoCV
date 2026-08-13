"""External service clients used by the FastAPI application."""

from .vlm import VLMClientError, analyze_image

__all__ = ["VLMClientError", "analyze_image"]