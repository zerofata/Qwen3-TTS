<script lang="ts">
  import { api, type Voice } from "./lib/api";
  import { pushToast } from "./lib/toast";
  import Tabs from "./lib/components/Tabs.svelte";
  import StatusBar from "./lib/components/StatusBar.svelte";
  import Toast from "./lib/components/Toast.svelte";
  import CustomVoice from "./views/CustomVoice.svelte";
  import VoiceDesign from "./views/VoiceDesign.svelte";
  import VoiceClone from "./views/VoiceClone.svelte";
  import VoiceLibrary from "./views/VoiceLibrary.svelte";

  const tabs = [
    { id: "custom", label: "Custom Voice" },
    { id: "design", label: "Voice Design" },
    { id: "clone", label: "Voice Clone" },
    { id: "library", label: "Voice Library" },
  ];

  let active = $state("custom");
  let voices = $state<Voice[]>([]);

  async function refreshVoices() {
    try {
      voices = await api.listVoices();
    } catch (e) {
      pushToast((e as Error).message, "error");
    }
  }

  $effect(() => {
    refreshVoices();
  });

  function goLibrary() {
    refreshVoices();
    active = "library";
  }
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <span class="logo" aria-hidden="true">Q3</span>
      <div>
        <h1>Qwen 3 TTS</h1>
        <p class="muted text-sm">Custom voices, voice design, and cloning for your table.</p>
      </div>
    </div>
    <StatusBar />
  </header>

  <main class="container">
    <Tabs {tabs} bind:active />

    <div class="view">
      {#if active === "custom"}
        <CustomVoice />
      {:else if active === "design"}
        <VoiceDesign onSaved={goLibrary} />
      {:else if active === "clone"}
        <VoiceClone onSaved={goLibrary} />
      {:else if active === "library"}
        <VoiceLibrary {voices} onChanged={refreshVoices} />
      {/if}
    </div>
  </main>
</div>

<Toast />

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-5);
    flex-wrap: wrap;
    padding: var(--space-4) var(--space-6);
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }
  .logo {
    display: grid;
    place-items: center;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: var(--radius-md);
    background: var(--accent);
    color: var(--accent-contrast);
    font-weight: 700;
    font-size: var(--text-sm);
    letter-spacing: 0.02em;
  }
  h1 {
    font-size: var(--text-xl);
  }
  .container {
    width: 100%;
    max-width: 1080px;
    margin: 0 auto;
    padding: var(--space-6);
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
    flex: 1;
  }
</style>
