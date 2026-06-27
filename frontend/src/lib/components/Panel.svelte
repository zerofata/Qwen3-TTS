<script lang="ts">
  import type { Snippet } from "svelte";
  let { children }: { children?: Snippet } = $props();
</script>

<section class="panel">
  {@render children?.()}
</section>

<style>
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    /* Gold left-accent is the blog's card signature (see post-entry). */
    border-left: 2px solid var(--accent);
    border-radius: var(--radius-sm) var(--radius-lg) var(--radius-lg)
      var(--radius-sm);
    padding: var(--space-5);
    box-shadow: var(--shadow-sm);
    transition: border-color var(--transition-smooth),
      box-shadow var(--transition-smooth);
    /* Equal-height columns in the grid so paired panels always align. */
    height: 100%;
  }
  .panel:hover {
    border-left-color: var(--accent-hover);
  }
</style>
