<script lang="ts">
  let {
    blob = null,
    downloadName = "qwen3-tts",
  }: { blob?: Blob | null; downloadName?: string } = $props();

  let url = $state<string | null>(null);

  $effect(() => {
    if (blob) {
      const u = URL.createObjectURL(blob);
      url = u;
      return () => URL.revokeObjectURL(u);
    }
    url = null;
  });

  const ext = $derived(blob?.type.includes("mpeg") ? "mp3" : "wav");
</script>

<div class="player">
  {#if url}
    <audio controls src={url} class="full"></audio>
    <a class="download" href={url} download={`${downloadName}.${ext}`}>
      Download .{ext}
    </a>
  {:else}
    <div class="empty muted text-sm">No audio yet. Generate to preview here.</div>
  {/if}
</div>

<style>
  .player {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }
  audio {
    border-radius: var(--radius-md);
  }
  .download {
    align-self: flex-start;
    font-size: var(--text-sm);
    font-weight: 560;
  }
  .empty {
    display: grid;
    place-items: center;
    min-height: 64px;
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    text-align: center;
  }
</style>
