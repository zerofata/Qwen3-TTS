"""Voice Library tab for Qwen3-TTS Gradio UI.

Lists every saved voice (cloned or frozen-from-design), lets you preview the
source sample, generate new speech from a selected voice, and rename or delete
voices. Generation uses the Base (voice_clone) model with the saved prompt, so
each character sounds consistent.
"""

import gradio as gr
import numpy as np
from typing import List, Optional, Tuple, Any

from app.core.model_manager import model_manager
from app.core.voice_library import voice_library


def _choices() -> List[Tuple[str, str]]:
    """Build (label, slug) choices for the voice dropdown."""
    out: List[Tuple[str, str]] = []
    for v in voice_library.list_voices():
        label = f"{v.get('name', v['slug'])}  ·  {v.get('source', 'clone')}"
        out.append((label, v["slug"]))
    return out


def refresh_voices() -> gr.Dropdown:
    """Reload the voice dropdown choices."""
    return gr.Dropdown(choices=_choices())


def on_select(slug: Optional[str]) -> Optional[str]:
    """Return the preview audio path for the selected voice."""
    if not slug:
        return None
    return voice_library.preview_path(slug)


def generate_from_library(
    slug: Optional[str], text: str
) -> Tuple[int, np.ndarray]:
    """Generate speech using a saved library voice."""
    if not slug:
        raise gr.Error("Select a voice from the library first.")
    if not text or not text.strip():
        raise gr.Error("Enter some text to speak.")

    try:
        prompt = voice_library.get(slug)
    except Exception as e:
        raise gr.Error(f"Could not load voice: {str(e)}")

    try:
        if not model_manager.is_loaded("voice_clone"):
            model_manager.load_model("voice_clone")
        model = model_manager.get_model()

        wavs, sr = model.generate_voice_clone(
            text=text,
            voice_clone_prompt=prompt,
            language=None,
        )
        audio_data = wavs[0]
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data)
        return (sr, audio_data)
    except Exception as e:
        raise gr.Error(f"Generation failed: {str(e)}")


def rename_voice(
    slug: Optional[str], new_name: str
) -> Tuple[gr.Dropdown, str]:
    """Rename the selected voice (its slug/id is unchanged)."""
    if not slug:
        raise gr.Error("Select a voice to rename.")
    if not new_name or not new_name.strip():
        raise gr.Error("Enter a new name.")
    try:
        ok = voice_library.rename(slug, new_name)
    except Exception as e:
        raise gr.Error(f"Rename failed: {str(e)}")
    if not ok:
        raise gr.Error("Voice not found.")
    return gr.Dropdown(choices=_choices(), value=slug), f"✅ Renamed to '{new_name.strip()}'."


def delete_voice(
    slug: Optional[str],
) -> Tuple[gr.Dropdown, Optional[str], str]:
    """Delete the selected voice."""
    if not slug:
        raise gr.Error("Select a voice to delete.")
    ok = voice_library.delete(slug)
    if not ok:
        raise gr.Error("Voice not found.")
    return gr.Dropdown(choices=_choices(), value=None), None, f"🗑️ Deleted '{slug}'."


def create_voice_library_tab() -> gr.Tab:
    """Create the Voice Library tab."""
    with gr.Tab("Voice Library") as tab:
        gr.Markdown("### Voice Library")
        gr.Markdown(
            "Reuse any voice you saved from the Voice Clone or Voice Design "
            "tabs. Saved voices are also selectable through the API "
            "(`/v1/audio/speech` with `voice` set to the voice id)."
        )

        with gr.Row():
            with gr.Column(scale=1):
                voice_dropdown = gr.Dropdown(
                    label="Saved Voices",
                    choices=_choices(),
                    interactive=True,
                    info="Pick a saved character voice.",
                )
                refresh_btn = gr.Button("🔄 Refresh", size="sm")

                preview_player = gr.Audio(
                    label="Voice Sample",
                    type="filepath",
                    interactive=False,
                )

                with gr.Accordion("Manage", open=False):
                    rename_input = gr.Textbox(
                        label="New Name",
                        placeholder="Rename selected voice...",
                    )
                    rename_btn = gr.Button("✏️ Rename", size="sm")
                    delete_btn = gr.Button(
                        "🗑️ Delete", size="sm", variant="stop"
                    )
                    manage_status = gr.Textbox(
                        label="Status",
                        interactive=False,
                        placeholder="Management status will appear here...",
                    )

            with gr.Column(scale=1):
                gr.Markdown("#### Generate")
                text_input = gr.TextArea(
                    label="Text to Speak",
                    placeholder="Enter text to speak with the selected voice...",
                    lines=4,
                )
                generate_btn = gr.Button("Generate", variant="primary")
                audio_output = gr.Audio(
                    label="Generated Audio",
                    type="numpy",
                    interactive=False,
                )

        # Event handlers
        refresh_btn.click(fn=refresh_voices, outputs=[voice_dropdown])

        voice_dropdown.change(
            fn=on_select, inputs=[voice_dropdown], outputs=[preview_player]
        )

        generate_btn.click(
            fn=generate_from_library,
            inputs=[voice_dropdown, text_input],
            outputs=[audio_output],
        )

        rename_btn.click(
            fn=rename_voice,
            inputs=[voice_dropdown, rename_input],
            outputs=[voice_dropdown, manage_status],
        )

        delete_btn.click(
            fn=delete_voice,
            inputs=[voice_dropdown],
            outputs=[voice_dropdown, preview_player, manage_status],
        )

        # Refresh the list whenever the tab is opened.
        tab.select(fn=refresh_voices, outputs=[voice_dropdown])

    return tab
