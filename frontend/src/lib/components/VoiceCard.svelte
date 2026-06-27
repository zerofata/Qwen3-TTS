<script lang="ts">
  import { api, type Voice } from "../api";
  import { pushToast } from "../toast";
  import Button from "./Button.svelte";
  import TextArea from "./TextArea.svelte";
  import AudioPlayer from "./AudioPlayer.svelte";

  let { voice, onChanged }: { voice: Voice; onChanged: () => void } = $props();

  let speakText = $state("");
  let audio = $state<Blob | null>(null);
  let generating = $state(false);

  let editing = $state(false);
  let editName = $state("");
  let busy = $state(false);

  const created = $derived(
    new Date(voice.created_at * 1000).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    })
  );

  async function speak() {
    if (!speakText.trim()) {
      pushToast("Enter text for this voice to speak.", "error");
      return;
    }
    generating = true;
    try {
      audio = await api.speakVoice(voice.slug, speakText);
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      generating = false;
    }
  }

  async function saveName() {
    if (!editName.trim()) return pushToast("Name cannot be empty.", "error");
    busy = true;
    try {
      await api.renameVoice(voice.slug, editName);
      editing = false;
      onChanged();
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      busy = false;
    }
  }

  async function remove() {
    if (!confirm(`Delete voice "${voice.name}"? This cannot be undone.`)) return;
    busy = true;
    try {
      await api.deleteVoice(voice.slug);
      pushToast(`Deleted "${voice.name}".`, "success");
      onChanged();
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      busy = false;
    }
  }
</script>

<article class="card">
  <header class="card-head">
    <div class="head-main">
      {#if editing}
        <input class="name-edit" bind:value={editName} />
      {:else}
        <h4>{voice.name}</h4>
      {/if}
      <div class="meta text-xs muted">
        <span class="badge">{voice.source}</span>
        <span>{created}</span>
      </div>
    </div>
    <div class="head-actions">
      {#if editing}
        <Button size="sm" variant="primary" onclick={saveName} loading={busy}>Save</Button>
        <Button size="sm" variant="ghost" onclick={() => (editing = false)}>Cancel</Button>
      {:else}
        <Button size="sm" variant="ghost" onclick={() => { editName = voice.name; editing = true; }}>
          Rename
        </Button>
        <Button size="sm" variant="danger" onclick={remove} loading={busy}>Delete</Button>
      {/if}
    </div>
  </header>

  <div class="body">
    <div class="preview">
      <span class="label text-xs muted">Reference</span>
      <audio controls src={api.voicePreviewUrl(voice.slug)} class="full"></audio>
    </div>

    <div class="speak">
      <TextArea label="Speak with this voice" bind:value={speakText} rows={2} placeholder="Text to synthesize..." />
      <Button size="sm" variant="primary" onclick={speak} loading={generating}>Generate</Button>
      {#if generating || audio}
        <AudioPlayer blob={audio} loading={generating} downloadName={voice.slug} />
      {/if}
    </div>
  </div>
</article>

<style>
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 2px solid var(--accent);
    border-radius: var(--radius-sm) var(--radius-lg) var(--radius-lg)
      var(--radius-sm);
    padding: var(--space-5);
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    transition: border-color var(--transition-smooth);
  }
  .card:hover {
    border-left-color: var(--accent-hover);
  }
  .card-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-3);
  }
  .head-main {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    min-width: 0;
  }
  h4 {
    font-size: var(--text-lg);
    overflow-wrap: anywhere;
  }
  .name-edit {
    padding: 0.4rem 0.6rem;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-sm);
    background: var(--surface);
  }
  .meta {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }
  .badge {
    padding: 0.1rem 0.45rem;
    border-radius: var(--radius-sm);
    background: var(--accent-soft);
    color: var(--accent-ink);
    font-family: var(--font-mono);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .head-actions {
    display: flex;
    gap: var(--space-2);
    flex-shrink: 0;
  }
  .body {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-5);
    align-items: start;
  }
  @media (max-width: 640px) {
    .body {
      grid-template-columns: 1fr;
    }
  }
  .preview .label {
    display: block;
    margin-bottom: var(--space-2);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .speak {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    align-items: flex-start;
  }
  .speak :global(.field),
  .speak :global(.player) {
    width: 100%;
  }
</style>
