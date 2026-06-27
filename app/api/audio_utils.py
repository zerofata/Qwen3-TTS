"""Audio encoding helpers shared by the API routes.

Centralizes waveform -> WAV/MP3 serialization so both the OpenAI-compatible
``/v1`` routes and the front-end ``/api`` routes use one implementation.
"""

# pyright: reportMissingImports=false

from __future__ import annotations

import io
import wave

import numpy as np
from pydub import AudioSegment


def to_pcm16(wav: "np.ndarray") -> "np.ndarray":
    """Convert a waveform to 16-bit PCM samples."""
    wav_array = np.asarray(wav)
    if np.issubdtype(wav_array.dtype, np.floating):
        wav_array = np.clip(wav_array, -1.0, 1.0)
        wav_array = (wav_array * 32767).astype(np.int16)
    elif wav_array.dtype != np.int16:
        wav_array = wav_array.astype(np.int16)
    return wav_array


def wav_bytes(wav: "np.ndarray", sample_rate: int) -> bytes:
    """Serialize a waveform to WAV (PCM16) bytes."""
    wav_array = to_pcm16(wav)
    channels = 1 if wav_array.ndim == 1 else wav_array.shape[1]
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(int(sample_rate))
        wav_file.writeframes(wav_array.tobytes())
    return buffer.getvalue()


def mp3_bytes_from_wav(raw_wav: bytes) -> bytes:
    """Transcode WAV bytes to MP3 bytes."""
    audio = AudioSegment.from_file(io.BytesIO(raw_wav), format="wav")
    out = io.BytesIO()
    audio.export(out, format="mp3")
    return out.getvalue()
