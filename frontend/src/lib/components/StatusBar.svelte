<script lang="ts">
  import { api, type Status } from "../api";

  let status = $state<Status | null>(null);
  let online = $state(true);

  async function poll() {
    try {
      status = await api.getStatus();
      online = true;
    } catch {
      online = false;
    }
  }

  $effect(() => {
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  });

  function titleCase(slug: string): string {
    return slug
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  }

  // Friendly name of the resident model, or null when nothing is loaded.
  const modelLabel = $derived(
    status?.current_model ? titleCase(status.current_model) : null
  );

  // Human-readable state. A model loads on demand and unloads when idle, so
  // "Ready" (nothing resident, will load on first use) is a real, valid state.
  const stateText = $derived(
    !online ? "Offline" : modelLabel ? `${modelLabel} active` : "Ready"
  );

  // VRAM is only meaningful while a model is resident.
  const vram = $derived(
    modelLabel &&
      status?.gpu_memory_allocated_gb !== undefined &&
      status?.gpu_memory_total_gb !== undefined
      ? `${status.gpu_memory_allocated_gb.toFixed(1)} / ${status.gpu_memory_total_gb.toFixed(0)} GB`
      : null
  );
</script>

<div class="status">
  <span class="state">
    <span
      class="dot"
      class:offline={!online}
      class:active={online && !!modelLabel}
      title={online ? "Online" : "Unreachable"}
    ></span>
    <span class="state-text">{stateText}</span>
  </span>
  {#if status?.gpu_name}
    <span class="item">
      <span class="k">GPU</span><span class="v">{status.gpu_name}</span>
    </span>
  {/if}
  {#if vram}
    <span class="item">
      <span class="k">VRAM</span><span class="v mono">{vram}</span>
    </span>
  {/if}
  {#if status?.asr_loaded}
    <span class="badge">ASR</span>
  {/if}
</div>

<style>
  .status {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    flex-wrap: wrap;
    font-family: var(--font-mono);
    font-size: var(--text-xs);
  }
  .state {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
  }
  .state-text {
    color: var(--text);
    font-weight: 560;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: var(--radius-full);
    background: var(--muted);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--muted) 22%, transparent);
  }
  .dot.active {
    background: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 28%, transparent);
  }
  .dot.offline {
    background: var(--danger);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--danger) 25%, transparent);
  }
  .item {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
  }
  .k {
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
  }
  .v {
    color: var(--text);
    font-weight: 560;
  }
  .badge {
    padding: 0.1rem 0.4rem;
    border-radius: var(--radius-sm);
    background: var(--accent-soft);
    color: var(--accent-ink);
    font-weight: 600;
  }
</style>
