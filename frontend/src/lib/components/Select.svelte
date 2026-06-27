<script lang="ts">
  let {
    label,
    value = $bindable(""),
    options,
    hint,
    id = crypto.randomUUID(),
  }: {
    label: string;
    value?: string;
    options: string[];
    hint?: string;
    id?: string;
  } = $props();
</script>

<div class="field">
  <label for={id}>{label}</label>
  <div class="select-wrap">
    <select {id} bind:value>
      {#each options as opt (opt)}
        <option value={opt}>{opt}</option>
      {/each}
    </select>
    <svg class="chev" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5" />
    </svg>
  </div>
  {#if hint}<p class="hint">{hint}</p>{/if}
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
  .select-wrap {
    position: relative;
  }
  select {
    width: 100%;
    appearance: none;
    padding: 0.6rem 2rem 0.6rem 0.75rem;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: border-color 0.12s ease, box-shadow 0.12s ease;
  }
  select:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--focus-ring);
  }
  .chev {
    position: absolute;
    right: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    width: 12px;
    height: 12px;
    color: var(--muted);
    pointer-events: none;
  }
  .hint {
    font-size: var(--text-xs);
    color: var(--muted);
  }
</style>
