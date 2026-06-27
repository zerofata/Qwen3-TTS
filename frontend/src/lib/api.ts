// Typed client for the Qwen 3 TTS JSON/audio API (served under /api).
// All audio-producing calls resolve to a Blob the UI turns into an object URL.

export interface Status {
  current_model: string | null;
  asr_loaded: boolean;
  device: string;
  gpu_name?: string;
  gpu_memory_total_gb?: number;
  gpu_memory_allocated_gb?: number;
}

export interface Voice {
  slug: string;
  name: string;
  source: string;
  ref_text: string;
  created_at: number;
}

export interface Speakers {
  speakers: string[];
  languages: string[];
}

export class ApiError extends Error {}

async function detail(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (data && typeof data.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return `${res.status} ${res.statusText}`;
  }
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new ApiError(await detail(res));
  return (await res.json()) as T;
}

async function blob(res: Response): Promise<Blob> {
  if (!res.ok) throw new ApiError(await detail(res));
  return await res.blob();
}

export const api = {
  getStatus: () => fetch("/api/status").then((r) => json<Status>(r)),

  getSpeakers: () => fetch("/api/speakers").then((r) => json<Speakers>(r)),

  listVoices: () => fetch("/api/voices").then((r) => json<Voice[]>(r)),

  voicePreviewUrl: (slug: string) =>
    `/api/voices/${encodeURIComponent(slug)}/preview`,

  speakVoice: (slug: string, text: string, language = "auto") =>
    fetch(`/api/voices/${encodeURIComponent(slug)}/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language }),
    }).then(blob),

  renameVoice: (slug: string, name: string) =>
    fetch(`/api/voices/${encodeURIComponent(slug)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }).then((r) => json<{ ok: boolean }>(r)),

  deleteVoice: (slug: string) =>
    fetch(`/api/voices/${encodeURIComponent(slug)}`, {
      method: "DELETE",
    }).then((r) => json<{ ok: boolean }>(r)),

  customVoice: (body: {
    text: string;
    speaker: string;
    language: string;
    instruct?: string;
  }) =>
    fetch("/api/custom-voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(blob),

  voiceDesign: (body: { text: string; instruct: string; language: string }) =>
    fetch("/api/voice-design", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(blob),

  transcribe: (audio: Blob) => {
    const form = new FormData();
    form.append("audio", audio, fileName(audio, "clip"));
    return fetch("/api/transcribe", { method: "POST", body: form }).then((r) =>
      json<{ text: string }>(r)
    );
  },

  voiceClone: (audio: Blob, refText: string, text: string) => {
    const form = new FormData();
    form.append("ref_audio", audio, fileName(audio, "ref"));
    form.append("ref_text", refText);
    form.append("text", text);
    return fetch("/api/voice-clone", { method: "POST", body: form }).then(blob);
  },

  voiceCloneSave: (audio: Blob, refText: string, name: string) => {
    const form = new FormData();
    form.append("ref_audio", audio, fileName(audio, "ref"));
    form.append("ref_text", refText);
    form.append("name", name);
    return fetch("/api/voice-clone/save", { method: "POST", body: form }).then(
      (r) => json<{ slug: string }>(r)
    );
  },

  freezeVoice: (audio: Blob, refText: string, name: string) => {
    const form = new FormData();
    form.append("audio", audio, fileName(audio, "design"));
    form.append("ref_text", refText);
    form.append("name", name);
    return fetch("/api/voices/freeze", { method: "POST", body: form }).then(
      (r) => json<{ slug: string }>(r)
    );
  },
};

function fileName(b: Blob, base: string): string {
  const ext = extFromType(b.type);
  if (b instanceof File && b.name) return b.name;
  return `${base}.${ext}`;
}

function extFromType(type: string): string {
  if (type.includes("wav")) return "wav";
  if (type.includes("mpeg") || type.includes("mp3")) return "mp3";
  if (type.includes("webm")) return "webm";
  if (type.includes("ogg")) return "ogg";
  if (type.includes("flac")) return "flac";
  return "wav";
}
