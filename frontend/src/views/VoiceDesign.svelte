<script lang="ts">
  import { api } from "../lib/api";
  import { pushToast } from "../lib/toast";
  import Panel from "../lib/components/Panel.svelte";
  import SectionHeader from "../lib/components/SectionHeader.svelte";
  import TextArea from "../lib/components/TextArea.svelte";
  import TextField from "../lib/components/TextField.svelte";
  import Select from "../lib/components/Select.svelte";
  import Button from "../lib/components/Button.svelte";
  import AudioPlayer from "../lib/components/AudioPlayer.svelte";

  let { onSaved }: { onSaved?: () => void } = $props();

  const LANGUAGES = [
    "Auto",
    "English",
    "Chinese",
    "French",
    "Japanese",
    "Korean",
    "German",
    "Russian",
    "Portuguese",
    "Spanish",
    "Italian",
  ];

  let text = $state("");
  let description = $state("");
  let language = $state("Auto");

  let audio = $state<Blob | null>(null);
  let lastText = $state("");
  let loading = $state(false);

  let freezeName = $state("");
  let freezing = $state(false);

  async function generate() {
    if (!text.trim()) {
      pushToast("Enter some text to speak.", "error");
      return;
    }
    if (!description.trim()) {
      pushToast("Describe the voice you want.", "error");
      return;
    }
    loading = true;
    try {
      audio = await api.voiceDesign({ text, instruct: description, language });
      lastText = text;
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      loading = false;
    }
  }

  async function freeze() {
    if (!audio) {
      pushToast("Generate a voice first, then freeze it.", "error");
      return;
    }
    if (!freezeName.trim()) {
      pushToast("Name the voice before freezing.", "error");
      return;
    }
    freezing = true;
    try {
      const { slug } = await api.freezeVoice(audio, lastText, freezeName);
      pushToast(`Frozen "${freezeName}" into the library (${slug}).`, "success");
      freezeName = "";
      onSaved?.();
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      freezing = false;
    }
  }
</script>

<div class="grid-2">
  <Panel>
    <SectionHeader
      title="Voice Design"
      description="Describe a voice in natural language and the model invents it."
    />
    <div class="stack">
      <TextArea label="Text to speak" bind:value={text} rows={4} placeholder="Enter text here..." />
      <TextArea
        label="Voice description"
        bind:value={description}
        rows={3}
        placeholder="e.g. An older male narrator, warm and gravelly, slow and deliberate."
      />
      <Select label="Language" bind:value={language} options={LANGUAGES} />
      <Button variant="primary" {loading} onclick={generate}>Generate</Button>
    </div>
  </Panel>

  <Panel>
    <SectionHeader title="Output" description="Preview, then freeze to reuse this exact voice." />
    <div class="stack">
      <AudioPlayer blob={audio} downloadName="voice-design" />
      <div class="freeze">
        <SectionHeader
          title="Freeze to library"
          description="Saves this designed voice so it sounds identical on every later use."
        />
        <div class="row items-center">
          <div class="flex-1">
            <TextField label="Voice name" bind:value={freezeName} placeholder="e.g. Forest Spirit" />
          </div>
          <Button onclick={freeze} loading={freezing}>Freeze &amp; Save</Button>
        </div>
      </div>
    </div>
  </Panel>
</div>

<style>
  .freeze {
    padding-top: var(--space-4);
    border-top: 1px solid var(--border);
  }
  .row {
    align-items: flex-end;
  }
</style>
