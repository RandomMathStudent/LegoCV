# Implementation Notes

## Purpose
This document records the reasoning, architecture decisions, and implementation patterns used in the project so future contributors can understand the system and maintain it more easily.

The canonical stage-by-stage architecture reference is in [architecture-spec.md](architecture-spec.md). Use this file for implementation rationale, trade-offs, and change history.

## Current Status
- The repository has a frontend scaffold and a backend scaffold.
- The frontend includes a camera capture screen and analysis button.
- The backend exposes an analysis endpoint that currently returns placeholder data while the CV pipeline is being implemented.

## Frontend Notes
- The app uses Next.js and a client-side webcam component.
- The capture screen is intentionally simple so the CV pipeline can be integrated without changing the entire UI structure.
- The frontend uses a route at /api/analyze to proxy requests to the backend.

## Backend Notes
- The backend uses FastAPI and modular service files.
- Each stage of the pipeline is isolated in a dedicated module to support future replacement of models and logic.
- The current implementation uses placeholder stub logic to keep the API contract stable while CV work is developed.

## Design Decisions
- Keep the API response JSON-serializable and simple.
- Avoid storing user images by default.
- Make each pipeline stage replaceable so CLIP, InsightFace, FAISS, or asset composition can be swapped later.
- Document each architecture choice in this file as the project evolves.

## Maintenance Guidance
- Update this file whenever a new major component or workflow is added.
- Keep the design and todo files in sync with implementation progress.
- Prefer small, clearly named modules over large monolithic service files.
