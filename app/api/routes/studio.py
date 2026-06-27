"""JSON API for the bundled "Qwen 3 TTS" front-end (SPA).

These routes expose the generation logic that used to live inside the Gradio
callbacks (custom voice, voice design, voice cloning, transcription) plus the
voice-library CRUD, as a small JSON/audio API consumed by the Svelte SPA.

GPU work is serialized through a single module-level ``asyncio.Lock`` and run in
a worker thread (``run_in_threadpool``) so a long synthesis never blocks the
event loop and two requests never touch the model concurrently. The separate
OpenAI-compatible ``/v1`` routes are unaffected and remain available for Open
WebUI.
"""

# pyright: reportMissingImports=false

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.api.audio_utils import wav_bytes
from app.api.dependencies import get_model_manager, get_voice_library
from app.core.model_manager import ModelManager
from app.core.presets import LANGUAGES, SPEAKERS
from app.core.voice_library import VoiceLibrary, _write_wav

router = APIRouter()

# Serializes all GPU access across requests (model load + generate + ASR).
_gpu_lock = asyncio.Lock()

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".opus", ".m4a", ".ogg", ".webm"}


async def _run_gpu(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run a blocking GPU operation, serialized and off the event loop."""
    async with _gpu_lock:
        return await run_in_threadpool(fn, *args, **kwargs)


async def _save_upload(upload: UploadFile) -> str:
    """Persist an uploaded audio file to a temp path and return it."""
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        suffix = ".wav"
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(await upload.read())
    return path


def _lang_arg(language: Optional[str]) -> Optional[str]:
    """Map the UI's 'Auto' sentinel to the model's None (auto-detect)."""
    if not language or language.strip().lower() == "auto":
        return None
    return language


def _wav_response(wavs: Any, sample_rate: int) -> Response:
    return Response(content=wav_bytes(wavs[0], sample_rate), media_type="audio/wav")


# --------------------------------------------------------------------------- #
# Status / presets
# --------------------------------------------------------------------------- #
@router.get("/status")
async def status(
    model_manager: ModelManager = Depends(get_model_manager),
) -> dict:
    """Current model + GPU status for the SPA status bar."""
    return model_manager.get_status()


@router.get("/speakers")
async def speakers() -> dict:
    """Custom Voice preset speakers and supported languages."""
    return {"speakers": SPEAKERS, "languages": LANGUAGES}


# --------------------------------------------------------------------------- #
# Voice library CRUD
# --------------------------------------------------------------------------- #
@router.get("/voices")
async def list_voices(
    voice_library: VoiceLibrary = Depends(get_voice_library),
) -> list:
    """All saved voices, newest first."""
    return voice_library.list_voices()


@router.get("/voices/{slug}/preview")
async def voice_preview(
    slug: str,
    voice_library: VoiceLibrary = Depends(get_voice_library),
) -> FileResponse:
    """Stream the stored preview/source clip for a voice."""
    path = voice_library.preview_path(slug)
    if not path:
        raise HTTPException(status_code=404, detail="No preview available for this voice.")
    return FileResponse(path, media_type="audio/wav")


class SpeakRequest(BaseModel):
    text: str
    language: Optional[str] = "auto"


@router.post("/voices/{slug}/speak")
async def voice_speak(
    slug: str,
    payload: SpeakRequest,
    voice_library: VoiceLibrary = Depends(get_voice_library),
    model_manager: ModelManager = Depends(get_model_manager),
) -> Response:
    """Generate speech for ``text`` using a saved voice."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")
    if not voice_library.exists(slug):
        raise HTTPException(status_code=404, detail=f"Voice not found: {slug}")

    try:
        prompt = voice_library.get(slug)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    def _work() -> tuple:
        if not model_manager.is_loaded("voice_clone"):
            model_manager.load_model("voice_clone")
        model = model_manager.get_model()
        return model.generate_voice_clone(
            text=payload.text,
            voice_clone_prompt=prompt,
            language=_lang_arg(payload.language) or "auto",
        )

    try:
        wavs, sr = await _run_gpu(_work)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")
    return _wav_response(wavs, sr)


class RenameRequest(BaseModel):
    name: str


@router.patch("/voices/{slug}")
async def rename_voice(
    slug: str,
    payload: RenameRequest,
    voice_library: VoiceLibrary = Depends(get_voice_library),
) -> dict:
    """Rename a saved voice."""
    try:
        ok = voice_library.rename(slug, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not ok:
        raise HTTPException(status_code=404, detail=f"Voice not found: {slug}")
    return {"ok": True}


@router.delete("/voices/{slug}")
async def delete_voice(
    slug: str,
    voice_library: VoiceLibrary = Depends(get_voice_library),
) -> dict:
    """Delete a saved voice."""
    if not voice_library.delete(slug):
        raise HTTPException(status_code=404, detail=f"Voice not found: {slug}")
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Generation: custom voice / voice design
# --------------------------------------------------------------------------- #
class CustomVoiceRequest(BaseModel):
    text: str
    speaker: str
    language: Optional[str] = "Auto"
    instruct: Optional[str] = None


@router.post("/custom-voice")
async def custom_voice(
    payload: CustomVoiceRequest,
    model_manager: ModelManager = Depends(get_model_manager),
) -> Response:
    """Generate speech with a preset speaker and optional style instruction."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")

    def _work() -> tuple:
        if not model_manager.is_loaded("custom_voice"):
            model_manager.load_model("custom_voice")
        model = model_manager.get_model()
        return model.generate_custom_voice(
            text=payload.text,
            speaker=payload.speaker,
            instruct=payload.instruct or None,
            language=_lang_arg(payload.language),
        )

    try:
        wavs, sr = await _run_gpu(_work)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")
    return _wav_response(wavs, sr)


class VoiceDesignRequest(BaseModel):
    text: str
    instruct: str
    language: Optional[str] = "Auto"


@router.post("/voice-design")
async def voice_design(
    payload: VoiceDesignRequest,
    model_manager: ModelManager = Depends(get_model_manager),
) -> Response:
    """Generate speech from a natural-language voice description."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")
    if not payload.instruct.strip():
        raise HTTPException(status_code=400, detail="Voice description is required.")

    def _work() -> tuple:
        if not model_manager.is_loaded("voice_design"):
            model_manager.load_model("voice_design")
        model = model_manager.get_model()
        return model.generate_voice_design(
            text=payload.text,
            instruct=payload.instruct,
            language=_lang_arg(payload.language),
        )

    try:
        wavs, sr = await _run_gpu(_work)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")
    return _wav_response(wavs, sr)


# --------------------------------------------------------------------------- #
# Transcription (ASR)
# --------------------------------------------------------------------------- #
@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    model_manager: ModelManager = Depends(get_model_manager),
) -> dict:
    """Transcribe an uploaded clip using Whisper (for voice-clone ref text)."""
    path = await _save_upload(audio)

    def _work() -> str:
        if not model_manager.is_loaded("voice_clone"):
            model_manager.load_model("voice_clone", with_asr=True)
        if not model_manager.get_status().get("asr_loaded"):
            model_manager.load_model("voice_clone", with_asr=True)
        asr = model_manager._asr_model
        if asr is None:
            raise RuntimeError("ASR model not loaded.")
        result = asr(path, return_timestamps=True)
        return result["text"].strip()

    try:
        text = await _run_gpu(_work)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")
    finally:
        _cleanup(path)
    return {"text": text}


# --------------------------------------------------------------------------- #
# Voice cloning (+ save) and design "freeze"
# --------------------------------------------------------------------------- #
@router.post("/voice-clone")
async def voice_clone(
    text: str = Form(...),
    ref_text: str = Form(...),
    ref_audio: UploadFile = File(...),
    model_manager: ModelManager = Depends(get_model_manager),
) -> Response:
    """Clone a voice from a reference clip and synthesize ``text`` (no save)."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")
    if not ref_text.strip():
        raise HTTPException(status_code=400, detail="Reference text is required.")

    path = await _save_upload(ref_audio)

    def _work() -> tuple:
        if not model_manager.is_loaded("voice_clone"):
            model_manager.load_model("voice_clone")
        model = model_manager.get_model()
        prompt = model.create_voice_clone_prompt(ref_audio=path, ref_text=ref_text)
        return model.generate_voice_clone(
            text=text, voice_clone_prompt=prompt, language="auto"
        )

    try:
        wavs, sr = await _run_gpu(_work)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Cloning failed: {exc}")
    finally:
        _cleanup(path)
    return _wav_response(wavs, sr)


@router.post("/voice-clone/save")
async def voice_clone_save(
    name: str = Form(...),
    ref_text: str = Form(...),
    ref_audio: UploadFile = File(...),
    model_manager: ModelManager = Depends(get_model_manager),
    voice_library: VoiceLibrary = Depends(get_voice_library),
) -> JSONResponse:
    """Clone a reference clip and persist it as a named library voice."""
    if not name.strip():
        raise HTTPException(status_code=400, detail="Voice name is required.")
    if not ref_text.strip():
        raise HTTPException(status_code=400, detail="Reference text is required.")

    path = await _save_upload(ref_audio)

    def _work() -> str:
        if not model_manager.is_loaded("voice_clone"):
            model_manager.load_model("voice_clone")
        model = model_manager.get_model()
        prompt = model.create_voice_clone_prompt(ref_audio=path, ref_text=ref_text)
        return voice_library.save(
            name=name,
            prompt_item=prompt,
            source="clone",
            ref_text=ref_text,
            preview=path,
        )

    try:
        slug = await _run_gpu(_work)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Save failed: {exc}")
    finally:
        _cleanup(path)
    return JSONResponse({"slug": slug})


@router.post("/voices/freeze")
async def freeze_voice(
    name: str = Form(...),
    ref_text: str = Form(...),
    audio: UploadFile = File(...),
    model_manager: ModelManager = Depends(get_model_manager),
    voice_library: VoiceLibrary = Depends(get_voice_library),
) -> JSONResponse:
    """Freeze a designed clip into a stable, reusable library voice.

    The supplied audio (a previously designed preview) is cloned with the Base
    model so the voice sounds identical on every later use.
    """
    if not name.strip():
        raise HTTPException(status_code=400, detail="Voice name is required.")
    if not ref_text.strip():
        raise HTTPException(
            status_code=400,
            detail="The text spoken in the clip is required to freeze the voice.",
        )

    path = await _save_upload(audio)

    def _work() -> str:
        if not model_manager.is_loaded("voice_clone"):
            model_manager.load_model("voice_clone")
        model = model_manager.get_model()
        prompt = model.create_voice_clone_prompt(ref_audio=path, ref_text=ref_text)
        return voice_library.save(
            name=name,
            prompt_item=prompt,
            source="design",
            ref_text=ref_text,
            preview=path,
        )

    try:
        slug = await _run_gpu(_work)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Freeze failed: {exc}")
    finally:
        _cleanup(path)
    return JSONResponse({"slug": slug})


def _cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
