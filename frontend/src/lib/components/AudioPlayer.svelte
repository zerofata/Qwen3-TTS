<script lang="ts">
  let {
    blob = null,
    downloadName = "qwen3-tts",
    loading = false,
    busyLabel = "Generating",
  }: {
    blob?: Blob | null;
    downloadName?: string;
    loading?: boolean;
    busyLabel?: string;
  } = $props();

  let url = $state<string | null>(null);
  let audioEl = $state<HTMLAudioElement | null>(null);
  let canvasEl = $state<HTMLCanvasElement | null>(null);
  let peaks = $state<number[]>([]);
  let progress = $state(0); // 0..1 playback position
  let elapsed = $state(0); // seconds since generation began

  const ext = $derived(blob?.type.includes("mpeg") ? "mp3" : "wav");

  // Object URL lifecycle for the native <audio> element + download link.
  $effect(() => {
    if (blob) {
      const u = URL.createObjectURL(blob);
      url = u;
      return () => URL.revokeObjectURL(u);
    }
    url = null;
    peaks = [];
    progress = 0;
  });

  // Live elapsed timer while a generation is in flight.
  $effect(() => {
    if (!loading) return;
    const start = performance.now();
    elapsed = 0;
    const id = setInterval(() => {
      elapsed = (performance.now() - start) / 1000;
    }, 100);
    return () => clearInterval(id);
  });

  // Decode the clip into normalized peaks for the waveform (decoding only;
  // playback still goes through the native <audio> element).
  $effect(() => {
    const b = blob;
    if (!b) return;
    let cancelled = false;
    (async () => {
      try {
        const buf = await b.arrayBuffer();
        const Ctx =
          window.AudioContext ||
          (window as unknown as { webkitAudioContext: typeof AudioContext })
            .webkitAudioContext;
        const ctx = new Ctx();
        const audioBuf = await ctx.decodeAudioData(buf.slice(0));
        await ctx.close();
        if (!cancelled) peaks = computePeaks(audioBuf, 240);
      } catch {
        if (!cancelled) peaks = [];
      }
    })();
    return () => {
      cancelled = true;
    };
  });

  // Redraw whenever peaks or playback progress change.
  $effect(() => {
    // touch reactive deps so the effect re-runs
    void peaks;
    void progress;
    draw();
  });

  function computePeaks(buf: AudioBuffer, count: number): number[] {
    const data = buf.getChannelData(0);
    const block = Math.floor(data.length / count) || 1;
    const out: number[] = [];
    let max = 0.0001;
    for (let i = 0; i < count; i++) {
      let peak = 0;
      const start = i * block;
      for (let j = 0; j < block; j++) {
        const v = Math.abs(data[start + j] || 0);
        if (v > peak) peak = v;
      }
      out.push(peak);
      if (peak > max) max = peak;
    }
    return out.map((p) => p / max);
  }

  function draw() {
    const c = canvasEl;
    if (!c) return;
    const dpr = window.devicePixelRatio || 1;
    const cssW = c.clientWidth || 300;
    const cssH = c.clientHeight || 56;
    c.width = Math.round(cssW * dpr);
    c.height = Math.round(cssH * dpr);
    const ctx = c.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, cssW, cssH);
    const n = peaks.length;
    if (n === 0) return;
    const styles = getComputedStyle(c);
    const played = styles.getPropertyValue("--accent").trim() || "#4f46e5";
    const base = styles.getPropertyValue("--border-strong").trim() || "#cfd5de";
    const slot = cssW / n;
    const barW = Math.max(1, slot - 1);
    for (let i = 0; i < n; i++) {
      const h = Math.max(2, peaks[i] * (cssH - 4));
      const x = i * slot;
      const y = (cssH - h) / 2;
      ctx.fillStyle = i / n <= progress ? played : base;
      ctx.fillRect(x, y, barW, h);
    }
  }

  function onTime() {
    const a = audioEl;
    if (a && a.duration) progress = a.currentTime / a.duration;
  }

  function seekToClientX(clientX: number) {
    const a = audioEl;
    const c = canvasEl;
    if (!a || !c || !a.duration) return;
    const rect = c.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
    a.currentTime = ratio * a.duration;
  }

  function onKeydown(e: KeyboardEvent) {
    const a = audioEl;
    if (!a || !a.duration) return;
    if (e.key === "ArrowRight") {
      a.currentTime = Math.min(a.duration, a.currentTime + 2);
      e.preventDefault();
    } else if (e.key === "ArrowLeft") {
      a.currentTime = Math.max(0, a.currentTime - 2);
      e.preventDefault();
    }
  }
</script>

<div class="player">
  {#if loading}
    <div class="busy">
      <div class="track"><div class="indeterminate"></div></div>
      <div class="busy-row">
        <span class="spinner" aria-hidden="true"></span>
        <span>{busyLabel}… <span class="mono">{elapsed.toFixed(1)}s</span></span>
      </div>
    </div>
  {:else if url}
    <button
      type="button"
      class="wave-btn"
      aria-label="Seek audio (use arrow keys)"
      onclick={(e) => seekToClientX(e.clientX)}
      onkeydown={onKeydown}
    >
      <canvas bind:this={canvasEl} class="wave"></canvas>
    </button>
    <audio
      bind:this={audioEl}
      controls
      src={url}
      class="full"
      ontimeupdate={onTime}
      onseeked={onTime}
      onplay={onTime}
    ></audio>
    <a class="download" href={url} download={`${downloadName}.${ext}`}>
      Download .{ext}
    </a>
  {:else}
    <div class="empty muted text-sm">No audio yet. Generate to preview here.</div>
  {/if}
</div>

<style>
  .player {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }
  audio {
    border-radius: var(--radius-md);
  }
  .download {
    align-self: flex-start;
    font-size: var(--text-sm);
    font-weight: 560;
  }
  .empty {
    display: grid;
    place-items: center;
    min-height: 64px;
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    text-align: center;
  }

  .wave-btn {
    display: block;
    width: 100%;
    padding: var(--space-2);
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    cursor: pointer;
  }
  .wave-btn:hover {
    border-color: var(--border-strong);
  }
  .wave {
    display: block;
    width: 100%;
    height: 56px;
  }

  .busy {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    padding: var(--space-4);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--surface-2);
  }
  .track {
    position: relative;
    height: 6px;
    border-radius: var(--radius-full);
    background: var(--border);
    overflow: hidden;
  }
  .indeterminate {
    position: absolute;
    height: 100%;
    width: 40%;
    border-radius: var(--radius-full);
    background: var(--accent);
    animation: slide 1.1s ease-in-out infinite;
  }
  @keyframes slide {
    0% {
      left: -40%;
    }
    100% {
      left: 100%;
    }
  }
  .busy-row {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-sm);
    color: var(--muted);
  }
  .spinner {
    width: 0.85em;
    height: 0.85em;
    border: 2px solid var(--accent);
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
