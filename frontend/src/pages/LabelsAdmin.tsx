// path: frontend/src/pages/LabelsAdmin.tsx
import React, { useMemo, useState } from "react";

type SkipCreatePayload = {
  owner_org_id: string;
  qr_code?: string | null;
  assigned_commodity_id?: string | null;
  zone_id?: string | null;
};

type SkipOut = {
  id: string;
  qr_code: string;
  owner_org_id: string;
  labels_pdf_url: string;
  label_png_urls: string[];
};

const apiBase = (import.meta as any).env?.VITE_API_URL || "http://127.0.0.1:8000"; // dev default

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-slate-600 mb-1">{children}</label>;
}

function TextInput(
  props: React.InputHTMLAttributes<HTMLInputElement> & { label?: string }
) {
  const { label, ...rest } = props;
  return (
    <div className="mb-4">
      {label && <FieldLabel>{label}</FieldLabel>}
      <input
        {...rest}
        className="w-full rounded-xl border px-3 py-2 outline-none focus:ring focus:ring-slate-300"
      />
    </div>
  );
}

function LinkRow({ href, label }: { href: string; label: string }) {
  const fileName = useMemo(() => href.split("/").pop() || label, [href, label]);
  return (
    <div className="flex items-center justify-between rounded-xl border p-3">
      <span className="truncate text-sm">{fileName}</span>
      <div className="flex items-center gap-2">
        <a
          href={`${apiBase}${href}`}
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border px-3 py-1 text-sm hover:bg-slate-50"
        >
          Open
        </a>
        <a
          href={`${apiBase}${href}`}
          download
          className="rounded-lg bg-slate-900 px-3 py-1 text-sm text-white hover:bg-slate-800"
        >
          Download
        </a>
      </div>
    </div>
  );
}

export default function LabelsAdmin() {
  const [form, setForm] = useState<SkipCreatePayload>({ owner_org_id: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SkipOut | null>(null);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!form.owner_org_id) {
      setError("Owner org ID is required");
      return;
    }

    setLoading(true);
    try {
      const r = await fetch(`${apiBase}/skips`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          owner_org_id: form.owner_org_id,
          qr_code: form.qr_code || null,
          assigned_commodity_id: form.assigned_commodity_id || null,
          zone_id: form.zone_id || null,
        } satisfies SkipCreatePayload),
      });

      if (!r.ok) {
        const msg = await r.text();
        throw new Error(`${r.status}: ${msg || r.statusText}`);
      }

      const data = (await r.json()) as SkipOut;
      setResult(data);
    } catch (err: any) {
      setError(err?.message ?? "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-4">
      <div className="mb-6 rounded-2xl border bg-white p-5 shadow-sm">
        <h2 className="mb-1 text-xl font-semibold">Create Labels</h2>
        <p className="mb-4 text-sm text-slate-600">
          POST <code className="rounded bg-slate-100 px-1 py-0.5">/skips</code> and get a PDF + 3 PNG label files.
        </p>

        <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <TextInput
              label="Owner Org ID (UUID)"
              placeholder="00000000-0000-0000-0000-000000000000"
              value={form.owner_org_id}
              onChange={(e) => setForm({ ...form, owner_org_id: e.target.value })}
              required
            />
          </div>

          <TextInput
            label="Custom QR Code (optional)"
            placeholder="SK-ABC123"
            value={form.qr_code ?? ""}
            onChange={(e) => setForm({ ...form, qr_code: e.target.value })}
          />

          <TextInput
            label="Assigned Commodity ID (optional)"
            placeholder="uuid"
            value={form.assigned_commodity_id ?? ""}
            onChange={(e) => setForm({ ...form, assigned_commodity_id: e.target.value })}
          />

          <TextInput
            label="Zone ID (optional)"
            placeholder="uuid"
            value={form.zone_id ?? ""}
            onChange={(e) => setForm({ ...form, zone_id: e.target.value })}
          />

          <div className="md:col-span-2 mt-2 flex items-center gap-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-slate-900 px-4 py-2 text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
            >
              {loading ? "Creating…" : "Create Labels"}
            </button>
            <button
              type="button"
              className="rounded-xl border px-4 py-2 hover:bg-slate-50"
              onClick={() => {
                setForm({ owner_org_id: "" });
                setError(null);
                setResult(null);
              }}
            >
              Reset
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <h3 className="mb-3 text-lg font-semibold">Assets generated</h3>

          <div className="mb-4 grid gap-3">
            <LinkRow href={result.labels_pdf_url} label="labels.pdf" />
            {result.label_png_urls.map((u, i) => (
              <LinkRow key={u} href={u} label={`labels/${i + 1}.png`} />
            ))}
          </div>

          <div className="text-sm text-slate-600">
            <div className="mb-1">Skip ID: {result.id}</div>
            <div className="mb-1">QR Code: {result.qr_code}</div>
            <div>Owner Org: {result.owner_org_id}</div>
          </div>
        </div>
      )}
    </div>
  );
}
