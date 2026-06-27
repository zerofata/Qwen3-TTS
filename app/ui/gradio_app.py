"""Main Gradio Application for Qwen 3 TTS.

Combines all tabs and components into a single themed interface. The visual
identity ("Arcane Studio") is driven by app/ui/assets/theme.css and a subtle
ambient canvas in app/ui/assets/background.js, both loaded at runtime so they
can be tweaked without touching Python.
"""

from pathlib import Path

import gradio as gr

from app.ui.tabs.custom_voice_tab import create_custom_voice_tab
from app.ui.tabs.voice_design_tab import create_voice_design_tab
from app.ui.tabs.voice_clone_tab import create_voice_clone_tab
from app.ui.tabs.voice_library_tab import create_voice_library_tab
from app.ui.components.model_status_bar import create_model_status_bar
from app.config import Settings

settings = Settings()

_ASSETS = Path(__file__).parent / "assets"


def _read_asset(name: str) -> str:
    """Load a CSS/JS asset; tolerate a missing file so the app still boots."""
    try:
        return (_ASSETS / name).read_text(encoding="utf-8")
    except OSError:
        return ""


THEME_CSS = _read_asset("theme.css")
BACKGROUND_JS = _read_asset("background.js")

# Display serif (Cinzel) for headings + clean sans (Inter) for body.
HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    "family=Cinzel:wght@500;600;700&family=Inter:wght@400;500;600&display=swap"
    '" rel="stylesheet">'
)

THEME = gr.themes.Base(
    primary_hue="amber",
    secondary_hue="purple",
    neutral_hue="slate",
).set(
    body_background_fill="transparent",
    body_background_fill_dark="transparent",
    block_background_fill="transparent",
)


def create_app() -> gr.Blocks:
    """Create the main Gradio Blocks app.

    Note: in Gradio 6.0 the theme/css/js/head params were moved off the Blocks
    constructor. They are applied where this app is mounted (see app/main.py
    passing THEME/THEME_CSS/BACKGROUND_JS/HEAD to mount_gradio_app).
    """
    with gr.Blocks(
        title="Qwen 3 TTS",
        elem_id="app-root",
    ) as demo:
        # Branded hero header
        with gr.Column(elem_id="app-hero"):
            gr.HTML(
                '<h1>Qwen 3 TTS</h1>'
                '<div class="arc-tagline">Voice cloning &middot; design &middot; '
                'style control</div>'
            )

        # Single global status strip (the only place it is rendered)
        create_model_status_bar()

        # Main tabs
        with gr.Tabs(elem_classes="arcane-tabs"):
            create_custom_voice_tab()
            create_voice_design_tab()
            create_voice_clone_tab()
            create_voice_library_tab()

        # Footer
        with gr.Column(elem_id="app-footer"):
            gr.HTML(
                '<div class="arc-rule"></div>'
                "<p>Powered by Qwen3-TTS models &middot; one model resident at a "
                "time (24GB+ GPU recommended).</p>"
            )

    return demo
