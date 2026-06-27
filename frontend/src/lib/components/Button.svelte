<script lang="ts">
  import type { Snippet } from "svelte";

  type Variant = "primary" | "secondary" | "ghost" | "danger";

  let {
    variant = "secondary",
    type = "button",
    disabled = false,
    loading = false,
    full = false,
    size = "md",
    onclick,
    children,
  }: {
    variant?: Variant;
    type?: "button" | "submit";
    disabled?: boolean;
    loading?: boolean;
    full?: boolean;
    size?: "sm" | "md";
    onclick?: (e: MouseEvent) => void;
    children?: Snippet;
  } = $props();
</script>

<button
  class="btn {variant} {size}"
  class:full
  {type}
  disabled={disabled || loading}
  {onclick}
>
  {#if loading}<span class="spinner" aria-hidden="true"></span>{/if}
  <span class="label"><!-- -->{@render children?.()}</span>
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    border: 1px solid transparent;
    border-radius: var(--radius-md);
    font-weight: 560;
    cursor: pointer;
    transition: background-color 0.12s ease, border-color 0.12s ease,
      color 0.12s ease, opacity 0.12s ease;
    white-space: nowrap;
  }
  .btn.md {
    padding: 0.55rem 1rem;
    font-size: var(--text-sm);
  }
  .btn.sm {
    padding: 0.35rem 0.7rem;
    font-size: var(--text-xs);
  }
  .btn.full {
    width: 100%;
  }
  .btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .primary {
    background: var(--accent);
    color: var(--accent-contrast);
  }
  .primary:not(:disabled):hover {
    background: var(--accent-hover);
  }

  .secondary {
    background: var(--surface);
    color: var(--text);
    border-color: var(--border-strong);
  }
  .secondary:not(:disabled):hover {
    background: var(--surface-2);
  }

  .ghost {
    background: transparent;
    color: var(--muted);
  }
  .ghost:not(:disabled):hover {
    background: var(--surface-2);
    color: var(--text);
  }

  .danger {
    background: transparent;
    color: var(--danger);
    border-color: var(--border-strong);
  }
  .danger:not(:disabled):hover {
    background: var(--danger-soft);
    border-color: var(--danger);
  }

  .spinner {
    width: 0.85em;
    height: 0.85em;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: var(--radius-full);
    animation: spin 0.6s linear infinite;
  }
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
