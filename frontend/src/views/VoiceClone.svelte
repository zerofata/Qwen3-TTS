<script lang="ts">
  import { api } from "../lib/api";
  import { pushToast } from "../lib/toast";
  import Panel from "../lib/components/Panel.svelte";
  import SectionHeader from "../lib/components/SectionHeader.svelte";
  import TextArea from "../lib/components/TextArea.svelte";
  import TextField from "../lib/components/TextField.svelte";
  import Button from "../lib/components/Button.svelte";
  import AudioPlayer from "../lib/components/AudioPlayer.svelte";

  let { onSaved }: { onSaved?: () => void } = $props();

  let refAudio = $state<Blob | null>(null);
  let refUrl = $state<string | null>(null);
  let refText = $state("");
  let text = $state("");

  let transcribing = $state(false);
  let generating = $state(false);
  let saving = $state(false);

  let recording = $state(false);
  let recorder: MediaRecorder | null = null;
  let chunks: Blob[] = [];

  let audio = $state<Blob | null>(null);
  let saveName = $state("");

  $effect(() => {
    if (refAudio) {
      const u = URL.createObjectURL(refAudio);
      refUrl = u;
      return () => URL.revokeObjectURL(u);
    }
    refUrl = null;
  });

  function onFile(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      refAudio = file;
      audio = null;
    }
  }

  async function toggleRecord() {
    if (recording) {
      recorder?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (ev) => {
        if (ev.data.size > 0) chunks.push(ev.data);
      };
      recorder.onstop = () => {
        refAudio = new Blob(chunks, { type: recorder?.mimeType || "audio/webm" });
        audio = null;
        stream.getTracks().forEach((t) => t.stop());
        recording = false;
      };
      recorder.start();
      recording = true;
    } catch (e) {
      pushToast("Microphone unavailable: " + (e as Error).message, "error");
    }
  }

  async function transcribe() {
    if (!refAudio) {
      pushToast("Add reference audio first.", "error");
      return;
    }
    transcribing = true;
    try {
      const { text: t } = await api.transcribe(refAudio);
      refText = t;
      pushToast("Transcribed. Review the reference text.", "success");
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      transcribing = false;
    }
  }

  async function generate() {
    if (!refAudio) return pushToast("Add reference audio first.", "error");
    if (!refText.trim()) return pushToast("Reference text is required.", "error");
    if (!text.trim()) return pushToast("Enter text to speak.", "error");
    generating = true;
    try {
      audio = await api.voiceClone(refAudio, refText, text);
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      generating = false;
    }
  }

  async function save() {
    if (!refAudio) return pushToast("Add reference audio first.", "error");
    if (!refText.trim()) return pushToast("Reference text is required.", "error");
    if (!saveName.trim()) return pushToast("Name the voice before saving.", "error");
    saving = true;
    try {
      const { slug } = await api.voiceCloneSave(refAudio, refText, saveName);
      pushToast(`Saved "${saveName}" to the library (${slug}).`, "success");
      saveName = "";
      onSaved?.();
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      saving = false;
    }
  }
</script>

<div class="grid-2">
  <Panel>
    <SectionHeader
      step={1}
      title="Reference audio"
      description="Upload a short, clean clip or record one. 5-15 seconds works best."
    />
    <div class="stack">
      <div class="row row-wrap items-center">
        <label class="file-btn">
          <input type="file" accept="audio/*" onchange={onFile} />
          Upload file
        </label>
        <Button variant={recording ? "danger" : "secondary"} onclick={toggleRecord}>
          {recording ? "Stop recording" : "Record mic"}
        </Button>
        {#if recording}<span class="rec-dot" aria-hidden="true"></span>{/if}
      </div>

      {#if refUrl}
        <audio controls src={refUrl} class="full"></audio>
      {:else}
        <p class="muted text-sm">No reference selected yet.</p>
      {/if}

      <div class="row items-center">
        <Button onclick={transcribe} loading={transcribing}>Transcribe</Button>
        <span class="muted text-xs">Auto-fills the reference text via Whisper.</span>
      </div>
      <TextArea
        label="Reference text"
        bind:value={refText}
        rows={3}
        hint="Must match what is spoken in the reference clip."
      />
    </div>
  </Panel>

  <Panel>
    <SectionHeader step={2} title="Generate &amp; save" description="Synthesize with the cloned voice, then optionally save it." />
    <div class="stack">
      <TextArea label="Text to speak" bind:value={text} rows={4} placeholder="Enter text to generate..." />
      <Button variant="primary" onclick={generate} loading={generating}>Clone &amp; Generate</Button>
      <AudioPlayer blob={audio} downloadName="voice-clone" />

      <div class="save">
        <SectionHeader
          title="Save to library"
          description="Reuse this voice later from the Library tab and the API."
        />
        <div class="row items-center">
          <div class="flex-1">
            <TextField label="Voice name" bind:value={saveName} placeholder="e.g. Goblin King" />
          </div>
          <Button onclick={save} loading={saving}>Save</Button>
        </div>
      </div>
    </div>
  </Panel>
</div>

<style>
  .file-btn {
    display: inline-flex;
    align-items: center;
    padding: 0.55rem 1rem;
    font-size: var(--text-sm);
    font-weight: 560;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
    background: var(--surface);
    cursor: pointer;
  }
  .file-btn:hover {
    background: var(--surface-2);
  }
  .file-btn input {
    display: none;
  }
  .rec-dot {
    width: 10px;
    height: 10px;
    border-radius: var(--radius-full);
    background: var(--danger);
    animation: pulse 1s ease-in-out infinite;
  }
  @keyframes pulse {
    50% {
      opacity: 0.3;
    }
  }
  .save {
    padding-top: var(--space-4);
    border-top: 1px solid var(--border);
  }
  .save .row {
    align-items: flex-end;
  }
</style>
