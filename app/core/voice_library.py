"""Persistent, named voice library for Qwen3-TTS.

This module generalizes the original single-slot ``voice_clone_cache`` into a
multi-entry library. Each saved voice is a ``VoiceClonePromptItem`` (the same
picklable object produced by ``model.create_voice_clone_prompt``) plus a small
amount of metadata and an optional preview/source WAV.

Layout under ``{VOICES_DIR}/library/``::

    index.json            # {slug: {name, source, ref_text, created_at}}
    <slug>.pkl            # pickled VoiceClonePromptItem
    <slug>.wav            # preview / source clip (optional)

The library lives in the persistent ``voices`` volume, so saved characters
survive container restarts and image rebuilds. A one-time migration imports the
legacy ``last_voice_clone.pkl`` (if present) as a voice named ``default``.
"""

from __future__ import annotations

import json
import os
import pickle
import re
import threading
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import Settings

settings = Settings()


def _slugify(name: str) -> str:
    """Turn a display name into a filesystem/URL-safe slug."""
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "voice"


def _write_wav(path: Path, sample_rate: int, wav: Any) -> None:
    """Write a waveform (numpy array) to a 16-bit PCM WAV file."""
    arr = np.asarray(wav)
    if np.issubdtype(arr.dtype, np.floating):
        arr = np.clip(arr, -1.0, 1.0)
        arr = (arr * 32767).astype(np.int16)
    elif arr.dtype != np.int16:
        arr = arr.astype(np.int16)

    channels = 1 if arr.ndim == 1 else arr.shape[1]
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(int(sample_rate))
        wav_file.writeframes(arr.tobytes())


class VoiceLibrary:
    """Singleton, thread-safe library of named voice-clone prompts."""

    _instance: Optional["VoiceLibrary"] = None
    _new_lock = threading.Lock()

    def __new__(cls) -> "VoiceLibrary":
        if cls._instance is None:
            with cls._new_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._lock = threading.RLock()
        self.root = Path(settings.VOICES_DIR) / "library"
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_file = self.root / "index.json"

        self._index_mtime: float = 0.0
        self._index: Dict[str, Dict[str, Any]] = self._load_index()
        self._index_mtime = self._current_mtime()
        self._migrate_legacy()

    # ------------------------------------------------------------------ #
    # Index persistence
    # ------------------------------------------------------------------ #
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception as exc:  # noqa: BLE001
                print(f"VoiceLibrary: could not read index: {exc}")
        return {}

    def _save_index(self) -> None:
        tmp = self.index_file.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.index_file)
        self._index_mtime = self._current_mtime()

    def _current_mtime(self) -> float:
        try:
            return self.index_file.stat().st_mtime if self.index_file.exists() else 0.0
        except OSError:
            return 0.0

    def _reload_if_changed(self) -> None:
        """Reload the index from disk if another writer changed it.

        Keeps reads correct even if a second process (or uvicorn worker) wrote
        the index. The index is tiny, so this is cheap.
        """
        mtime = self._current_mtime()
        if mtime != self._index_mtime:
            self._index = self._load_index()
            self._index_mtime = mtime

    def _migrate_legacy(self) -> None:
        """Import the old single-slot cache as 'default' on first run."""
        if self._index:
            return
        legacy = Path(settings.CACHE_DIR) / "last_voice_clone.pkl"
        if not legacy.exists():
            return
        try:
            with open(legacy, "rb") as f:
                prompt_item = pickle.load(f)
            self.save(
                name="default",
                prompt_item=prompt_item,
                source="clone",
                ref_text="",
                preview=None,
            )
            print("VoiceLibrary: migrated last_voice_clone.pkl -> 'default'")
        except Exception as exc:  # noqa: BLE001
            print(f"VoiceLibrary: legacy migration skipped: {exc}")

    # ------------------------------------------------------------------ #
    # Paths
    # ------------------------------------------------------------------ #
    def _pkl_path(self, slug: str) -> Path:
        return self.root / f"{slug}.pkl"

    def _wav_path(self, slug: str) -> Path:
        return self.root / f"{slug}.wav"

    def _unique_slug(self, name: str) -> str:
        base = _slugify(name)
        slug = base
        counter = 2
        while slug in self._index:
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def save(
        self,
        name: str,
        prompt_item: Any,
        source: str = "clone",
        ref_text: str = "",
        preview: Optional[Any] = None,
    ) -> str:
        """Save a voice under ``name`` and return its slug.

        Args:
            name: Human-friendly voice name.
            prompt_item: The VoiceClonePromptItem to persist.
            source: "clone" or "design".
            ref_text: Reference transcript used to build the prompt.
            preview: Optional preview/source audio. Either a ``(sample_rate,
                ndarray)`` tuple or a path to an existing audio file.
        """
        if not name or not name.strip():
            raise ValueError("Voice name is required.")

        with self._lock:
            self._reload_if_changed()
            slug = self._unique_slug(name)

            tmp_pkl = self._pkl_path(slug).with_suffix(".pkl.tmp")
            with open(tmp_pkl, "wb") as f:
                pickle.dump(prompt_item, f)
            os.replace(tmp_pkl, self._pkl_path(slug))

            if preview is not None:
                try:
                    if isinstance(preview, tuple) and len(preview) == 2:
                        sr, wav = preview
                        _write_wav(self._wav_path(slug), sr, wav)
                    else:
                        src = Path(preview)
                        if src.exists():
                            import shutil

                            shutil.copy2(src, self._wav_path(slug))
                except Exception as exc:  # noqa: BLE001
                    print(f"VoiceLibrary: preview not saved for {slug}: {exc}")

            self._index[slug] = {
                "name": name.strip(),
                "source": source,
                "ref_text": ref_text or "",
                "created_at": time.time(),
            }
            self._save_index()
            print(f"VoiceLibrary: saved voice '{name}' as '{slug}'")
            return slug

    def get(self, slug_or_name: str) -> Any:
        """Return the prompt item for a voice (by slug or display name)."""
        with self._lock:
            self._reload_if_changed()
            slug = self._resolve(slug_or_name)
            if slug is None:
                raise RuntimeError(f"Voice not found: {slug_or_name}")
            with open(self._pkl_path(slug), "rb") as f:
                return pickle.load(f)

    def _resolve(self, slug_or_name: str) -> Optional[str]:
        if slug_or_name in self._index:
            return slug_or_name
        for slug, meta in self._index.items():
            if meta.get("name") == slug_or_name:
                return slug
        candidate = _slugify(slug_or_name)
        if candidate in self._index:
            return candidate
        return None

    def list_voices(self) -> List[Dict[str, Any]]:
        """Return metadata for all voices, newest first."""
        with self._lock:
            self._reload_if_changed()
            items = [
                {"slug": slug, **meta} for slug, meta in self._index.items()
            ]
        items.sort(key=lambda m: m.get("created_at", 0), reverse=True)
        return items

    def default(self) -> Optional[str]:
        """Slug of the most recently created voice, or None if empty."""
        voices = self.list_voices()
        return voices[0]["slug"] if voices else None

    def exists(self, slug_or_name: str) -> bool:
        with self._lock:
            self._reload_if_changed()
            return self._resolve(slug_or_name) is not None

    def preview_path(self, slug_or_name: str) -> Optional[str]:
        """Filesystem path to a voice's preview WAV, if one exists."""
        with self._lock:
            self._reload_if_changed()
            slug = self._resolve(slug_or_name)
            if slug is None:
                return None
            path = self._wav_path(slug)
            return str(path) if path.exists() else None

    def delete(self, slug_or_name: str) -> bool:
        with self._lock:
            self._reload_if_changed()
            slug = self._resolve(slug_or_name)
            if slug is None:
                return False
            self._pkl_path(slug).unlink(missing_ok=True)
            self._wav_path(slug).unlink(missing_ok=True)
            self._index.pop(slug, None)
            self._save_index()
            print(f"VoiceLibrary: deleted voice '{slug}'")
            return True

    def rename(self, slug_or_name: str, new_name: str) -> bool:
        if not new_name or not new_name.strip():
            raise ValueError("New name is required.")
        with self._lock:
            self._reload_if_changed()
            slug = self._resolve(slug_or_name)
            if slug is None:
                return False
            self._index[slug]["name"] = new_name.strip()
            self._save_index()
            return True


voice_library = VoiceLibrary()
