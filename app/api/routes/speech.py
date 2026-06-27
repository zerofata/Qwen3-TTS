"""OpenAI-compatible speech synthesis endpoint."""

# pyright: reportMissingImports=false

from __future__ import annotations

import io
import wave

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydub import AudioSegment

from app.api.dependencies import get_model_manager, get_voice_library
from app.api.schemas.openai import SpeechRequest
from app.core.model_manager import ModelManager
from app.core.voice_library import VoiceLibrary

router = APIRouter()


def _to_pcm16(wav: np.ndarray) -> np.ndarray:
    """Convert waveform to 16-bit PCM."""

    wav_array = np.asarray(wav)
    if np.issubdtype(wav_array.dtype, np.floating):
        wav_array = np.clip(wav_array, -1.0, 1.0)
        wav_array = (wav_array * 32767).astype(np.int16)
    elif wav_array.dtype != np.int16:
        wav_array = wav_array.astype(np.int16)
    return wav_array


def _wav_bytes(wav: np.ndarray, sample_rate: int) -> bytes:
    """Serialize waveform to WAV bytes."""

    wav_array = _to_pcm16(wav)
    channels = 1 if wav_array.ndim == 1 else wav_array.shape[1]
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wav_array.tobytes())
    return buffer.getvalue()


def _mp3_bytes_from_wav(wav_bytes: bytes) -> bytes:
    """Convert WAV bytes to MP3 bytes."""

    wav_buffer = io.BytesIO(wav_bytes)
    audio = AudioSegment.from_file(wav_buffer, format="wav")
    mp3_buffer = io.BytesIO()
    audio.export(mp3_buffer, format="mp3")
    return mp3_buffer.getvalue()


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

    wav_bytes = _wav_bytes(wavs[0], sample_rate)
    if response_format == "wav":
        return Response(content=wav_bytes, media_type="audio/wav")

    mp3_bytes = _mp3_bytes_from_wav(wav_bytes)
    return Response(content=mp3_bytes, media_type="audio/mpeg")
