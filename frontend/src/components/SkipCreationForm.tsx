// frontend/src/components/SkipCreationForm.tsx
import React, { useEffect, useMemo, useState } from "react";
import { api, pretty, adminCreateSkip, type SkipCreateIn } from "../api";
import { getConfig } from "../lib/devConfig";
import { toast } from "../ui/toast";

type MetaColors = Record<string, any>;
type MetaSizes = Record<string, Array<string | number>>;
type MetaShape = { skip: { colors: MetaColors; sizes: MetaSizes } };

// quick UUID detector
function looksLikeUuid(s: string) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(s.trim());
}

async function resolveContractorIdByName(name: string): Promise<string | null> {
  try {
    const list = await api.listContractors(); // [{id, org_name, ...}]
    const lower = name.trim().toLowerCase();
    // exact match first
    let hit = list.find((c: any) => String(c.org_name || "").toLowerCase() === lower);
    if (hit) return hit.id;
    // then lenient "starts with"
    hit = list.find((c: any) => String(c.org_name || "").toLowerCase().startsWith(lower));
    return hit?.id ?? null;
  } catch {
    return null;
  }
}

export default function SkipCreateForm({ onSeed }: { onSeed?: (qr: string) => void }) {
  const [meta, setMeta] = useState<MetaShape | null>(null);
  const [qr, setQr] = useState("QR-NEW-001");
  const [color, setColor] = useState("");
  const [size, setSize] = useState("");           // UI keeps it a string; we coerce to number on submit
  const [notes, setNotes] = useState("");
  const [ownerOrg, setOwnerOrg] = useState("");   // free text: name OR uuid
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<any>(null);

  // ✅ NEW: store the server-generated skip id for label buttons
  const [seededId, setSeededId] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const m = await api.meta(); // normalized meta
        if (alive) setMeta(m);
      } catch {
        if (alive) setMeta(null);
      }
    })();
    return () => { alive = false; };
  }, []);

  const colorOptions = useMemo(() => {
    const colors = meta?.skip?.colors ?? {};
    return Object.entries(colors).map(([key, val]) => {
      const label = val?.label ?? val?.name ?? val?.meaning ?? key;
      return { value: key, label: `${key} — ${label}` };
    });
  }, [meta]);

  const groupedSizeOptions = useMemo(() => {
    const sizes = meta?.skip?.sizes ?? {};
    return Object.entries(sizes).map(([group, items]) => {
      const arr = (items as Array<string | number>).map((v) => {
        const s = String(v);
        return { value: s, label: s };
      });
      return { group, items: arr };
    });
  }, [meta]);

  // ✅ NEW: open a backend URL in a new tab with ?key=<ADMIN_API_KEY>
  const openWithAdminKey = (path: string) => {
    const { baseUrl, adminKey } = getConfig(); // import from "../lib/devConfig"
    if (!baseUrl || !adminKey) {
      // optional toast if you use it:
      // toast.error("Set Base URL + Admin Key in Config");
      return;
    }
    const url = `${baseUrl}${path}${path.includes("?") ? "&" : "?"}key=${encodeURIComponent(adminKey)}`;
    window.open(url, "_blank", "noopener");
  };

  const submit = async () => {
    if (!qr || !color || !size) {
      setOut({ error: "Missing required fields" });
      return;
    }
    setBusy(true);
    try {
      // Resolve owner org: allow uuid or name
      let owner_org_id: string | undefined;
      if (ownerOrg.trim()) {
        if (looksLikeUuid(ownerOrg)) {
          owner_org_id = ownerOrg.trim();
        } else {
          const found = await resolveContractorIdByName(ownerOrg);
          if (!found) {
            const msg = `No contractor found named "${ownerOrg}". Create it in Contractors Admin first, then try again.`;
            setOut({ error: msg });
            toast.error(msg);
            return;
          }
          owner_org_id = found;
        }
      }

      // Build payload; adminCreateSkip will send size_m3 internally
      const payload: SkipCreateIn = {
        qr,
        color,
        size: Number(size),                 // important: backend expects size_m3 as a number
        notes: notes || undefined,
        owner_org_id,                       // uuid or undefined
      };

      const res = await adminCreateSkip(payload);
      setOut(res);

      // ✅ NEW: capture the created/seeded skip id for label buttons
      const id = String((res as any)?.id ?? "");
      if (id) setSeededId(id);

      const seeded = (res as any)?.qr_code ?? (res as any)?.qr ?? qr;
      onSeed?.(seeded);
      toast.success("Skip created/seeded");
    } catch (e: any) {
      setOut({ error: e?.message || "Request failed", detail: e?.response?.data ?? e });
      toast.error(e?.message || "Seed failed");
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
        <label>Owner Org (optional)
          <input
            value={ownerOrg}
            onChange={(e) => setOwnerOrg(e.target.value)}
            placeholder="e.g. ACME LTD or UUID"
          />
        </label>
      </div>

      <div className="row" style={{ marginTop: 10 }}>
        <button disabled={busy || !meta} onClick={submit}>Create / Seed</button>
        <span className="muted">
          Uses color + size from <code>/meta/config</code>. Falls back to dev seeding if needed.
        </span>
      </div>

      <div style={{ marginTop: 12 }}>
        {out ? (
          <details open className="result">
            <summary><strong>Result</strong></summary>
            <pre>{pretty(out)}</pre>

            {(() => {
              // get skip id from result
              const skipId = out?.id ? String(out.id) : out?.skip_id ? String(out.skip_id) : null;
              if (!skipId) return null;

              // Base URL + Admin Key from Config
              const { baseUrl, adminKey } = getConfig(); // make sure this is imported from "../lib/devConfig"
              const cleanBase = (baseUrl || "").replace(/\/+$/, "");

              // helper to append ?key=... correctly
              const withKey = (path: string) =>
                adminKey
                  ? `${cleanBase}${path}${path.includes("?") ? "&" : "?"}key=${encodeURIComponent(adminKey)}`
                  : null;

              const pdf  = withKey(`/skips/${skipId}/labels.pdf`);
              const png1 = withKey(`/skips/${skipId}/labels/1.png`);
              const png2 = withKey(`/skips/${skipId}/labels/2.png`);
              const png3 = withKey(`/skips/${skipId}/labels/3.png`);

              if (!pdf) {
                return <div className="muted text-sm">Set Config → <strong>Admin Key</strong> to open labels.</div>;
              }

              return (
                <div className="row" style={{ gap: 8, marginTop: 8 }}>
                  <a className="btn" href={pdf}  target="_blank" rel="noreferrer">Open Labels (PDF)</a>
                  <a className="btn" href={png1!} target="_blank" rel="noreferrer">PNG 1</a>
                  <a className="btn" href={png2!} target="_blank" rel="noreferrer">PNG 2</a>
                  <a className="btn" href={png3!} target="_blank" rel="noreferrer">PNG 3</a>
                </div>
              );
            })()}

          </details>
        ) : null}
      </div>
    </section>
  );
}
