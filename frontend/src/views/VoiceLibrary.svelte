<script lang="ts">
  import type { Voice } from "../lib/api";
  import SectionHeader from "../lib/components/SectionHeader.svelte";
  import Button from "../lib/components/Button.svelte";
  import VoiceCard from "../lib/components/VoiceCard.svelte";

  let {
    voices,
    onChanged,
  }: { voices: Voice[]; onChanged: () => void } = $props();
</script>

<div class="lib">
  <div class="row items-center justify-between">
    <SectionHeader
      title="Voice Library"
      description="Saved voices from cloning and frozen designs. Reuse them here or via the API."
    />
    <Button size="sm" variant="secondary" onclick={onChanged}>Refresh</Button>
  </div>

  {#if voices.length === 0}
    <div class="empty">
      <p>No saved voices yet.</p>
      <p class="muted text-sm">
        Clone a voice in <strong>Voice Clone</strong>, or freeze one in
        <strong>Voice Design</strong>, then save it to build your library.
      </p>
    </div>
  {:else}
    <div class="cards">
      {#each voices as voice (voice.slug)}
        <VoiceCard {voice} {onChanged} />
      {/each}
    </div>
  {/if}
</div>

<style>
  .lib {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }
  .row {
    align-items: flex-start;
  }
  .cards {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }
  .empty {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    padding: var(--space-7);
    text-align: center;
    background: var(--surface);
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius-lg);
  }
</style>
