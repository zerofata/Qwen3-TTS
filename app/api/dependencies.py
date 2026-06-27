"""FastAPI dependencies for API routes."""

from app.core.model_manager import ModelManager, model_manager
from app.core.voice_clone_cache import VoiceCloneCache, voice_cache
from app.core.voice_library import VoiceLibrary, voice_library


def get_voice_cache() -> VoiceCloneCache:
    """Provide the legacy single-slot voice clone cache instance."""

    return voice_cache


def get_voice_library() -> VoiceLibrary:
    """Provide the persistent multi-voice library instance."""

    return voice_library


def get_model_manager() -> ModelManager:
    """Provide the model manager instance."""

    return model_manager
