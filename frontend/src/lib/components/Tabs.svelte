<script lang="ts">
  interface Tab {
    id: string;
    label: string;
  }
  let {
    tabs,
    active = $bindable(""),
  }: { tabs: Tab[]; active?: string } = $props();
</script>

<div class="tabs" role="tablist" aria-label="Sections">
  {#each tabs as tab (tab.id)}
    <button
      role="tab"
      aria-selected={active === tab.id}
      class="tab"
      class:active={active === tab.id}
      onclick={() => (active = tab.id)}
    >
      {tab.label}
    </button>
  {/each}
</div>

<style>
  .tabs {
    display: flex;
    gap: var(--space-1);
    padding: var(--space-1);
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    overflow-x: auto;
  }
  .tab {
    flex: 1;
    min-width: max-content;
    padding: 0.5rem 0.9rem;
    border: none;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-weight: 500;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: background-color var(--transition-fast),
      color var(--transition-fast), border-color var(--transition-fast);
  }
  .tab:hover {
    color: var(--text);
  }
  .tab.active {
    background: var(--surface);
    color: var(--accent-ink);
    border-bottom-color: var(--accent);
    box-shadow: var(--shadow-sm);
  }
</style>
