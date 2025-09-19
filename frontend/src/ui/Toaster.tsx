// frontend/src/ui/Toaster.tsx
import React from "react";
import { onToast, dismiss, Toast } from "./toast";

function Badge({ kind }: { kind: Toast["kind"] }) {
  return <span className={`badge ${kind}`}>{kind}</span>;
}

export default function Toaster() {
  const [toasts, setToasts] = React.useState<Toast[]>([]);
  React.useEffect(() => onToast(setToasts), []);
  return (
    <div className="toaster">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.kind}`} role="status" onClick={() => dismiss(t.id)}>
          <div className="row">
            <Badge kind={t.kind} />
            <strong>{t.title ?? (t.kind === "error" ? "Error" : "Notice")}</strong>
          </div>
          {t.msg ? <div className="muted">{t.msg}</div> : null}
        </div>
      ))}
    </div>
  );
}
