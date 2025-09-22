// frontend/src/components/BinAssignmentsAdmin.tsx
import React, { useEffect, useMemo, useState } from "react";
import { api, pretty } from "../api";
import type { Contractor } from "../api";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default function BinAssignmentsAdmin(
  { onResult }: { onResult?: (title: string, payload: any) => void }
) {
  const [qr, setQr] = useState("QR123");
  const [contractorInput, setContractorInput] = useState("");
  const [contractors, setContractors] = useState<Contractor[]>([]);
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<any>(null);

  // Load contractors once (needs admin key set in Config)
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const list = await api.listContractors();
        if (alive) setContractors(Array.isArray(list) ? list : []);
      } catch {
        if (alive) setContractors([]);
      }
    })();
    return () => { alive = false; };
  }, []);

  // helper: resolve user input -> UUID (accept UUID or org_name)
  const resolveContractorId = async (input: string): Promise<string> => {
    const v = (input || "").trim();
    if (!v) throw new Error("Enter contractor name or id");

    // UUID directly
    if (UUID_RE.test(v)) return v;

    // try exact org_name (case-insensitive)
    const exact = contractors.find(
      c => (c.org_name || "").toLowerCase() === v.toLowerCase()
    );
    if (exact?.id) return exact.id;

    // try partial contains
    const partial = contractors.find(
      c => (c.org_name || "").toLowerCase().includes(v.toLowerCase())
    );
    if (partial?.id) return partial.id;

    // fallback: refresh contractors once and retry exact
    try {
      const fresh = await api.listContractors();
      setContractors(Array.isArray(fresh) ? fresh : []);
      const again = (fresh as Contractor[]).find(
        c => (c.org_name || "").toLowerCase() === v.toLowerCase()
      );
      if (again?.id) return again.id;
    } catch {/* ignore */}

    throw new Error(`Contractor not found for "${v}"`);
  };

  const listInfo = useMemo(
    () =>
      contractors
        .map(c => ({ id: c.id, label: c.org_name || c.id }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    [contractors]
  );

  const setResult = (title: string, payload: any) => {
    setOut({ title, payload });
    onResult?.(title, payload);
  };

  const onLookup = async () => {
    setBusy(true);
    try {
      const r = await api.listCurrentOwner(qr);
      setResult("Lookup", r);
    } catch (e: any) {
      setResult("Lookup (ERR)", e?.response?.data || e?.message || e);
    } finally {
      setBusy(false);
    }
  };

  const onAssign = async () => {
    setBusy(true);
    try {
      const contractor_id = await resolveContractorId(contractorInput);
      const r = await api.assignBin({ qr, contractor_id });
      setResult("Assign bin", r);
    } catch (e: any) {
      setResult("Assign bin (ERR)", e?.response?.data || e?.message || e);
    } finally {
      setBusy(false);
    }
  };

  const onUnassign = async () => {
    setBusy(true);
    try {
      const contractor_id = contractorInput
        ? await resolveContractorId(contractorInput)
        : undefined;
      const r = await api.unassignBin({ qr, contractor_id });
      setResult("Unassign bin", r);
    } catch (e: any) {
      setResult("Unassign bin (ERR)", e?.response?.data || e?.message || e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card">
      <h2>Admin: Bin Assignments</h2>
      <div className="grid2">
        <label>Bin QR
          <input
            value={qr}
            onChange={e => setQr(e.target.value)}
            placeholder="QR123"
          />
        </label>

        <label>Contractor (name or id)
          <input
            value={contractorInput}
            onChange={e => setContractorInput(e.target.value)}
            placeholder="uuid-or-name"
            list="contractors-list"
          />
          <datalist id="contractors-list">
            {listInfo.map(c => (
              <option key={c.id} value={c.label}>{c.id}</option>
            ))}
          </datalist>
        </label>
      </div>

      <div className="row" style={{ marginTop: 8, gap: 8 }}>
        <button disabled={busy} onClick={onLookup}>Lookup</button>
        <button disabled={busy} onClick={onAssign}>Assign</button>
        <button className="ghost" disabled={busy} onClick={onUnassign}>Unassign</button>
      </div>

      {out ? (
        <details open className="result" style={{ marginTop: 8 }}>
          <summary>
            <strong>{out.title}</strong>
          </summary>
          <pre>{pretty(out.payload)}</pre>
        </details>
      ) : null}
    </section>
  );
}
