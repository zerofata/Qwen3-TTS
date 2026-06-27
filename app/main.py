"""FastAPI application entry point for Qwen 3 TTS.

Serves three things from one process (``uvicorn app.main:app``):

* the OpenAI-compatible ``/v1`` API (kept for Open WebUI),
* the SPA-facing JSON/audio API under ``/api`` (see ``routes/studio.py``),
* the built Svelte single-page app as static files at ``/``.
"""

# pyright: reportMissingImports=false

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    models_router,
    speech_router,
    status_router,
    studio_router,
    transcribe_router,
    voices_router,
)
from app.config import Settings

settings = Settings()

# Built SPA assets land here in the container image (see Dockerfile node stage).
WEB_DIR = os.environ.get("WEB_DIR", "/app/web")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown."""
    print(f"Starting Qwen 3 TTS on {settings.API_HOST}:{settings.API_PORT}")
    yield
    print("Shutting down Qwen 3 TTS")


app = FastAPI(
    title="Qwen 3 TTS",
    description="OpenAI-compatible TTS API with a custom Svelte front-end",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI-compatible API (unchanged; consumed by Open WebUI).
app.include_router(speech_router, prefix="/v1", tags=["audio"])
app.include_router(voices_router, prefix="/v1", tags=["audio"])
app.include_router(models_router, prefix="/v1", tags=["models"])
app.include_router(transcribe_router, prefix="/v1", tags=["audio"])
app.include_router(status_router, prefix="/v1", tags=["status"])

# SPA-facing API.
app.include_router(studio_router, prefix="/api", tags=["studio"])


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


# Serve the built SPA at the root. ``html=True`` makes StaticFiles fall back to
# index.html for client-side routes and returns it for "/". Mounted last so it
# never shadows the API routers above. When the build is absent (local dev
# before ``npm run build``), skip the mount so the API still boots.
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="spa")
else:
    print(f"SPA assets not found at {WEB_DIR}; serving API only.")
