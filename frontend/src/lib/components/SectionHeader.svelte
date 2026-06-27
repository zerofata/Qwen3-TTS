<script lang="ts">
  let {
    title,
    description,
    step,
  }: { title: string; description?: string; step?: number } = $props();
</script>

<header class="section-header">
  <div class="title-row">
    {#if step !== undefined}<span class="step">{step}</span>{/if}
    <h3>{title}</h3>
  </div>
  <span class="accent-rule" aria-hidden="true"></span>
  {#if description}<p class="muted text-sm">{description}</p>{/if}
</header>

<style>
  .section-header {
    margin-bottom: var(--space-4);
  }
  .title-row {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }
  h3 {
    font-size: var(--text-lg);
  }
  .step {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: var(--radius-full);
    background: var(--accent-soft);
    color: var(--accent-ink);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: 600;
  }
  .accent-rule {
    display: block;
    width: 2.25rem;
    height: 2px;
    margin-top: var(--space-2);
    border-radius: var(--radius-full);
    background: var(--accent);
  }
  p {
    margin-top: var(--space-2);
  }
</style>
