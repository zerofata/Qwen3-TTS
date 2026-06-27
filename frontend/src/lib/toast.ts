import { writable } from "svelte/store";

export type ToastKind = "info" | "success" | "error";

export interface ToastItem {
  id: number;
  kind: ToastKind;
  message: string;
}

export const toasts = writable<ToastItem[]>([]);

let counter = 0;

export function pushToast(
  message: string,
  kind: ToastKind = "info",
  ttl = 4500
): void {
  const id = ++counter;
  toasts.update((list) => [...list, { id, kind, message }]);
  if (ttl > 0) setTimeout(() => dismissToast(id), ttl);
}

export function dismissToast(id: number): void {
  toasts.update((list) => list.filter((t) => t.id !== id));
}
