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
    color: var(--accent);
    font-size: var(--text-xs);
    font-weight: 700;
  }
  p {
    margin-top: var(--space-1);
  }
</style>
