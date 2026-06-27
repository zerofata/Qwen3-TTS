"""OpenAI-compatible speech synthesis endpoint."""

# pyright: reportMissingImports=false

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.audio_utils import mp3_bytes_from_wav, wav_bytes
from app.api.dependencies import get_model_manager, get_voice_library
from app.api.schemas.openai import SpeechRequest
from app.core.model_manager import ModelManager
from app.core.voice_library import VoiceLibrary

router = APIRouter()


@router.post("/audio/speech")
async def create_speech(
    payload: SpeechRequest,
    voice_library: VoiceLibrary = Depends(get_voice_library),
    model_manager: ModelManager = Depends(get_model_manager),
) -> Response:
    """Generate speech using a named voice from the library.

    The OpenAI ``voice`` field selects a library voice by slug or name. When it
    is omitted, the most recently saved voice is used.
    """

    requested = (payload.voice or "").strip()
    if requested:
        if not voice_library.exists(requested):
            raise HTTPException(
                status_code=400,
                detail=f"Unknown voice '{requested}'. Save it in the Voice "
                "Library tab, or call GET /v1/audio/voices to list voices.",
            )
        target = requested
    else:
        target = voice_library.default()
        if target is None:
            raise HTTPException(
                status_code=400,
                detail="No voices saved yet. Create one in the Voice Library "
                "tab (clone a voice or freeze a designed voice).",
            )

    try:
        prompt = voice_library.get(target)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    response_format = (payload.response_format or "mp3").lower()
    if response_format not in {"mp3", "wav"}:
        raise HTTPException(
            status_code=400,
            detail="response_format must be 'mp3' or 'wav'",
        )

    if not model_manager.is_loaded("voice_clone"):
        model_manager.load_model("voice_clone")

    model = model_manager.get_model()
    wavs, sample_rate = model.generate_voice_clone(
        text=payload.input,
        voice_clone_prompt=prompt,
        language="auto",
    )

    raw_wav = wav_bytes(wavs[0], sample_rate)
    if response_format == "wav":
        return Response(content=raw_wav, media_type="audio/wav")

    mp3 = mp3_bytes_from_wav(raw_wav)
    return Response(content=mp3, media_type="audio/mpeg")
