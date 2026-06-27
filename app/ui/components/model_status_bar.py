"""Model status strip component for the Gradio UI.

Renders a compact, glowing status pill (Model / ASR / Device / VRAM) that polls
the model manager. Styled by app/ui/assets/theme.css via elem_id="status-strip".
"""

import gradio as gr
from app.core.model_manager import model_manager

_MODEL_LABELS = {
    "custom_voice": "Custom Voice",
    "voice_design": "Voice Design",
    "voice_clone": "Voice Clone",
}


def _dot(kind: str) -> str:
    return f'<span class="dot {kind}"></span>'


def get_status_html() -> str:
    """Build the compact status strip HTML."""
    status = model_manager.get_status()
    raw_model = status.get("current_model")
    model = _MODEL_LABELS.get(raw_model, "Idle") if raw_model else "Idle"
    asr_loaded = bool(status.get("asr_loaded"))
    device = status.get("device", "cpu")
    vram_alloc = status.get("gpu_memory_allocated_gb", 0.0) or 0.0
    vram_total = status.get("gpu_memory_total_gb", 0.0) or 0.0

    model_dot = "on" if raw_model else "idle"
    asr_dot = "on" if asr_loaded else "idle"

    return (
        '<div class="arc-status">'
        f'<span class="item">{_dot(model_dot)}Model&nbsp;<b>{model}</b></span>'
        f'<span class="item">{_dot(asr_dot)}ASR&nbsp;<b>{"Loaded" if asr_loaded else "Off"}</b></span>'
        f'<span class="item">{_dot("gpu")}Device&nbsp;<b>{device}</b></span>'
        f'<span class="item">{_dot("gpu")}VRAM&nbsp;<b>{vram_alloc:.1f} / {vram_total:.1f} GB</b></span>'
        "</div>"
    )


def create_model_status_bar() -> gr.HTML:
    """Create the polling status strip component."""
    return gr.HTML(value=get_status_html, every=2.0, elem_id="status-strip")
