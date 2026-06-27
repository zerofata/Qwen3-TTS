<script lang="ts">
  import { toasts, dismissToast } from "../toast";
</script>

<div class="toast-stack" role="region" aria-label="Notifications">
  {#each $toasts as t (t.id)}
    <div class="toast {t.kind}" role="status">
      <span class="msg">{t.message}</span>
      <button class="close" aria-label="Dismiss" onclick={() => dismissToast(t.id)}>×</button>
    </div>
  {/each}
</div>

<style>
  .toast-stack {
    position: fixed;
    bottom: var(--space-5);
    right: var(--space-5);
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    z-index: var(--z-toast);
    max-width: min(380px, calc(100vw - 2rem));
  }
  .toast {
    display: flex;
    align-items: flex-start;
    gap: var(--space-3);
    padding: 0.7rem 0.9rem;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-left-width: 4px;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    font-size: var(--text-sm);
  }
  .toast.success {
    border-left-color: var(--success);
  }
  .toast.error {
    border-left-color: var(--danger);
  }
  .toast.info {
    border-left-color: var(--accent);
  }
  .msg {
    flex: 1;
  }
  .close {
    border: none;
    background: transparent;
    color: var(--muted);
    font-size: 1.1rem;
    line-height: 1;
    cursor: pointer;
  }
  .close:hover {
    color: var(--text);
  }
</style>
