<script lang="ts">
  import type { Voice } from "../api";

  let {
    voices,
    selected = $bindable(""),
    label = "Voice",
    emptyHint = "No saved voices yet.",
  }: {
    voices: Voice[];
    selected?: string;
    label?: string;
    emptyHint?: string;
  } = $props();
</script>

<div class="field">
  <label for="voice-picker">{label}</label>
  {#if voices.length === 0}
    <p class="hint">{emptyHint}</p>
  {:else}
    <div class="select-wrap">
      <select id="voice-picker" bind:value={selected}>
        {#each voices as v (v.slug)}
          <option value={v.slug}>{v.name} · {v.source}</option>
        {/each}
      </select>
    </div>
  {/if}
</div>

<style>
  .field {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }
  label {
    font-size: var(--text-sm);
    font-weight: 560;
  }
  select {
    width: 100%;
    padding: 0.6rem 0.75rem;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
  }
  select:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--focus-ring);
  }
  .hint {
    font-size: var(--text-xs);
    color: var(--muted);
  }
</style>
