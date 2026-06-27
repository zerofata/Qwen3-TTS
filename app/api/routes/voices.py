"""OpenAI-compatible voices endpoint."""

# pyright: reportMissingImports=false

from fastapi import APIRouter, Depends

from app.api.dependencies import get_voice_library
from app.api.schemas.openai import VoiceInfo, VoicesResponse
from app.core.voice_library import VoiceLibrary

router = APIRouter()


@router.get("/audio/voices", response_model=VoicesResponse)
async def list_voices(
    voice_library: VoiceLibrary = Depends(get_voice_library),
) -> VoicesResponse:
    """List all saved voices in the library."""

    voices = [
        VoiceInfo(id=meta["slug"], name=meta.get("name", meta["slug"]))
        for meta in voice_library.list_voices()
    ]
    return VoicesResponse(voices=voices)
