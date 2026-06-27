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

  let text = $state("");
  let speaker = $state("");
  let language = $state("Auto");
  let instruct = $state("");

  let speakers = $state<string[]>([]);
  let languages = $state<string[]>(["Auto"]);

  let audio = $state<Blob | null>(null);
  let loading = $state(false);

  $effect(() => {
    api
      .getSpeakers()
      .then((s) => {
        speakers = s.speakers;
        languages = s.languages;
        if (!speaker && s.speakers.length) speaker = s.speakers[0];
      })
      .catch((e) => pushToast(e.message, "error"));
  });

  async function generate() {
    if (!text.trim()) {
      pushToast("Enter some text to speak.", "error");
      return;
    }
    loading = true;
    try {
      audio = await api.customVoice({ text, speaker, language, instruct });
    } catch (e) {
      pushToast((e as Error).message, "error");
    } finally {
      loading = false;
    }
  }
</script>

<div class="grid-2">
  <Panel>
    <SectionHeader
      title="Custom Voice"
      description="Generate speech with a premium preset speaker and optional style direction."
    />
    <div class="stack">
      <TextArea label="Text to speak" bind:value={text} rows={5} placeholder="Enter text here..." />
      <div class="row">
        <div class="flex-1">
          <Select label="Speaker" bind:value={speaker} options={speakers} />
        </div>
        <div class="flex-1">
          <Select label="Language" bind:value={language} options={languages} />
        </div>
      </div>
      <TextField
        label="Style instruction (optional)"
        bind:value={instruct}
        placeholder="e.g. Speak in a calm, narrating tone"
      />
      <Button variant="primary" {loading} onclick={generate}>Generate</Button>
    </div>
  </Panel>

  <Panel>
    <SectionHeader title="Output" description="Preview and download the generated clip." />
    <AudioPlayer blob={audio} {loading} downloadName="custom-voice" />
  </Panel>
</div>
