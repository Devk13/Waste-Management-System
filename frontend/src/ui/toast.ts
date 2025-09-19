// frontend/src/ui/toast.ts  (fix cleanup type)
type ToastKind = "info" | "success" | "error";
export type Toast = { id: string; kind: ToastKind; title?: string; msg?: string; ms?: number };

type Listener = (toasts: Toast[]) => void;
const listeners = new Set<Listener>();
let queue: Toast[] = [];

function emit() { for (const l of listeners) l(queue); }
function id() { return Math.random().toString(36).slice(2); }
function push(t: Toast) {
  queue = [t, ...queue].slice(0, 5); emit();
  const ttl = t.ms ?? (t.kind === "error" ? 6000 : 3000);
  setTimeout(() => dismiss(t.id), ttl);
}

export function dismiss(tid: string) { queue = queue.filter(x => x.id !== tid); emit(); }

/** Subscribe; returns unsubscribe (void cleanup). */
export function onToast(cb: Listener): () => void {
  listeners.add(cb);
  cb(queue);
  return () => { listeners.delete(cb); }; // <- ensure void
}

export const toast = {
  info: (msg: string, title?: string, ms?: number) => push({ id: id(), kind: "info", title, msg, ms }),
  success: (msg: string, title?: string, ms?: number) => push({ id: id(), kind: "success", title, msg, ms }),
  error: (msg: string, title?: string, ms?: number) => push({ id: id(), kind: "error", title, msg, ms }),
};
