// ===========================
// frontend/src/components/SkipCreateForm.tsx  (complete)
// ===========================
import React, { useEffect, useMemo, useState } from "react";
import { api, pretty, adminCreateSkip, type SkipCreateIn } from "../api";

type MetaColors = Record<string, any>;
type MetaSizes = Record<string, string[]>;
type MetaShape = { skip: { colors: MetaColors; sizes: MetaSizes } };

export default function SkipCreateForm() {
  const [meta, setMeta] = useState<MetaShape | null>(null);
  const [qr, setQr] = useState("QR-NEW-001");
  const [color, setColor] = useState("");
  const [size, setSize] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<any>(null);

  useEffect(() => { api.meta().then(setMeta).catch(() => setMeta(null)); }, []);

  const colorOptions = useMemo(() => {
    const colors = meta?.skip?.colors ?? {};
    return Object.entries(colors).map(([key, val]) => {
      const label = val?.label ?? val?.name ?? val?.meaning ?? key;
      return { value: key, label: `${key} — ${label}` };
    });
  }, [meta]);

  const groupedSizeOptions = useMemo(() => {
    const sizes = meta?.skip?.sizes ?? {};
    return Object.entries(sizes).map(([group, items]) => ({
      group,
      items: (items as string[]).map((v) => ({ value: v, label: v })),
    }));
  }, [meta]);

  const submit = async () => {
    if (!qr || !color || !size) { setOut({ error:"Missing required fields" }); return; }
    setBusy(true);
    try {
      const payload: SkipCreateIn = { qr, color, size, notes: notes || undefined };
      const res = await adminCreateSkip(payload);
      setOut(res);
    } catch (e: any) {
      setOut({ error: e?.message, detail: e?.response?.data });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card">
      <h2>Create/Seed Skip</h2>
      {!meta ? <p className="muted">Loading meta…</p> : null}
      <div className="grid3">
        <label>QR
          <input value={qr} onChange={(e) => setQr(e.target.value)} placeholder="QR code" />
        </label>
        <label>Color (with meaning)
          <select value={color} onChange={(e) => setColor(e.target.value)}>
            <option value="">Select color</option>
            {colorOptions.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </label>
        <label>Size
          <select value={size} onChange={(e) => setSize(e.target.value)}>
            <option value="">Select size</option>
            {groupedSizeOptions.map((g) => (
              <optgroup key={g.group} label={g.group}>
                {g.items.map((it) => (
                  <option key={`${g.group}:${it.value}`} value={it.value}>{it.label}</option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>
      </div>
      <div className="grid2" style={{ marginTop: 8 }}>
        <label>Notes
          <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="optional" />
        </label>
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        <button disabled={busy || !meta} onClick={submit}>Create / Seed</button>
        <span className="muted">Uses color + size from <code>/meta/config</code>. Falls back to dev seeding if needed.</span>
      </div>

      <div style={{ marginTop: 12 }}>
        {out ? (
          <details open className="result">
            <summary><strong>Result</strong></summary>
            <pre>{pretty(out)}</pre>
          </details>
        ) : null}
      </div>
    </section>
  );
}
