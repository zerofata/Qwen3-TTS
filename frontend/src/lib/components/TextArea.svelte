<script lang="ts">
  let {
    label,
    value = $bindable(""),
    placeholder = "",
    hint,
    rows = 4,
    id = crypto.randomUUID(),
  }: {
    label: string;
    value?: string;
    placeholder?: string;
    hint?: string;
    rows?: number;
    id?: string;
  } = $props();
</script>

<div class="field">
  <label for={id}>{label}</label>
  <textarea {id} {rows} bind:value {placeholder}></textarea>
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
  textarea {
    width: 100%;
    padding: 0.6rem 0.75rem;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
    resize: vertical;
    line-height: var(--leading-normal);
    transition: border-color 0.12s ease, box-shadow 0.12s ease;
  }
  textarea:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--focus-ring);
  }
  .hint {
    font-size: var(--text-xs);
    color: var(--muted);
  }
</style>
