"""Static presets shared by the API and front-end.

These used to live inside the Gradio ``custom_voice_tab`` module. They are moved
here so the values survive the removal of the Gradio UI and can be served to the
SPA via ``GET /api/speakers``.
"""

from __future__ import annotations

# Supported Custom Voice speakers. These four lower entries replace upstream's
# Chloe/Luna/Owen/Zoe, which the CustomVoice model does not ship and which raise
# "Unsupported speakers" at generation time.
SPEAKERS = [
    "Vivian",
    "Ryan",
    "Serena",
    "Aiden",
    "Dylan",
    "Eric",
    "Uncle_Fu",
    "Ono_Anna",
    "Sohee",
]

# Supported target languages ("Auto" lets the model detect).
LANGUAGES = [
    "Auto",
    "English",
    "Chinese",
    "French",
    "Japanese",
    "Korean",
    "German",
    "Russian",
    "Portuguese",
    "Spanish",
    "Italian",
]
