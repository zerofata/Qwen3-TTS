"""Voice Design tab for Qwen3-TTS Gradio UI.

Allows generation of speech by describing the desired voice, and freezing a
designed voice into the persistent Voice Library so it sounds identical on every
later use (the frozen sample is cloned into a stable voice-clone prompt).
"""

import os
import tempfile
import gradio as gr
import numpy as np
from typing import Tuple, Optional, Any

from app.core.model_manager import model_manager
from app.core.voice_library import voice_library, _write_wav
from app.ui.components.model_status_bar import create_model_status_bar


def generate_audio(
    text: str,
    description: str,
    language: str,
) -> Tuple[int, np.ndarray]:
    """Generate audio using the Voice Design model.

    Returns:
        Tuple of (sample_rate, audio_array) for Gradio Audio component.
    """
    if not text:
        raise gr.Error("Please enter text to generate.")
    if not description:
        raise gr.Error("Please provide a voice description.")

    try:
        # Ensure correct model is loaded
        if not model_manager.is_loaded("voice_design"):
            model_manager.load_model("voice_design")

        model = model_manager.get_model()

        # Handle 'Auto' language selection
        lang_arg = None if language == "Auto" else language

        # Generate
        wavs, sr = model.generate_voice_design(
            text=text,
            instruct=description,
            language=lang_arg,
        )

        # Gradio Audio expects (sample_rate, audio_data)
        audio_data = wavs[0]
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data)

        return (sr, audio_data)

    except Exception as e:
        import traceback

        print(f"Error in generate_audio: {e}")
        print(traceback.format_exc())
        raise gr.Error(f"Generation failed: {str(e)}")


def freeze_and_save(
    name: str,
    audio: Optional[Tuple[int, np.ndarray]],
    text: str,
) -> str:
    """Freeze the generated designed voice into the library.

    The previewed audio is written to a temporary WAV, cloned with the Base
    model (using the spoken text as the reference transcript), and stored as a
    reusable library voice. This makes the designed voice consistent across
    future generations.
    """
    if audio is None or not isinstance(audio, tuple) or len(audio) != 2:
        raise gr.Error("Generate a designed voice first, then freeze it.")
    if not name or not name.strip():
        raise gr.Error("Enter a voice name before saving.")
    if not text or not text.strip():
        raise gr.Error("The text used for generation is required to freeze the voice.")

    sr, wav = audio
    tmp_path = None
    try:
        # Persist the previewed audio to a temp WAV for cloning.
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        _write_wav(tmp_path, sr, wav)

        # Cloning requires the Base (voice_clone) model.
        if not model_manager.is_loaded("voice_clone"):
            model_manager.load_model("voice_clone")
        model = model_manager.get_model()

        prompt = model.create_voice_clone_prompt(
            ref_audio=tmp_path,
            ref_text=text.strip(),
        )

        slug = voice_library.save(
            name=name,
            prompt_item=prompt,
            source="design",
            ref_text=text.strip(),
            preview=(sr, wav),
        )
    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(f"Freeze failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    return f"✅ Frozen '{name.strip()}' into the library (id: {slug})."


def load_model_on_select():
    """Load the voice design model when tab is selected."""
    try:
        model_manager.load_model("voice_design")
    except Exception as e:
        print(f"Error loading model: {e}")


def create_voice_design_tab() -> gr.Tab:
    """Create the Voice Design tab."""
    with gr.Tab("Voice Design") as tab:
        # Status bar to show model loading state
        create_model_status_bar()

        gr.Markdown("### Voice Design")
        gr.Markdown(
            "Create a new voice by describing it in natural language. "
            "Describe gender, age, tone, emotion, and speaking style."
        )

        with gr.Row():
            with gr.Column():
                text_input = gr.TextArea(
                    label="Text to Speak",
                    placeholder="Enter text here...",
                    lines=4,
                )

                language_input = gr.Dropdown(
                    choices=[
                        "Auto",
                        "Chinese",
                        "English",
                        "Japanese",
                        "Korean",
                        "German",
                        "French",
                        "Russian",
                        "Portuguese",
                        "Spanish",
                        "Italian",
                    ],
                    value="Auto",
                    label="Language",
                    info="Select target language or use Auto for detection.",
                )

                description_input = gr.TextArea(
                    label="Voice Description",
                    placeholder=(
                        "E.g., 'A young female voice, energetic and happy, "
                        "high pitch, speaking quickly.'"
                    ),
                    lines=3,
                    info="Describe the voice characteristics in detail.",
                )
                generate_btn = gr.Button("Generate", variant="primary")

            with gr.Column():
                audio_output = gr.Audio(
                    label="Generated Audio",
                    type="numpy",
                    interactive=False,
                )

                gr.Markdown("#### Freeze to Library")
                gr.Markdown(
                    "Save this designed voice so it sounds identical every time "
                    "and can be selected from the Voice Library tab and the API."
                )
                voice_name_input = gr.Textbox(
                    label="Voice Name",
                    placeholder="e.g. Forest Spirit",
                )
                freeze_btn = gr.Button(
                    "❄️ Freeze & Save to Library", variant="secondary"
                )
                freeze_status = gr.Textbox(
                    label="Save Status",
                    interactive=False,
                    placeholder="Save status will appear here...",
                )

        # Event handlers
        generate_btn.click(
            fn=generate_audio,
            inputs=[text_input, description_input, language_input],
            outputs=[audio_output],
        )

        freeze_btn.click(
            fn=freeze_and_save,
            inputs=[voice_name_input, audio_output, text_input],
            outputs=[freeze_status],
        )

        # Load model when tab is selected
        tab.select(fn=load_model_on_select, outputs=None)

    return tab
