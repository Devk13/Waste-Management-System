// frontend/src/components/BinAssignmentsAdmin.tsx
import React, { useState } from "react";
import { api, pretty } from "../api";

type Props = {
  onResult?: (title: string, payload: unknown) => void;
};

export default function BinAssignmentsAdmin({ onResult }: Props) {
  const [qr, setQr] = useState("QR123");
  const [contractorId, setContractorId] = useState("");
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<any>(null);

  const push = (title: string, payload: unknown) => {
    setOut({ title, payload, at: new Date().toLocaleTimeString() });
    onResult?.(title, payload);
  };

  const lookup = async () => {
    if (!qr) return;
    setBusy(true);
    try {
      const res = await api.listCurrentOwner(qr);
      push("Current owner", res);
    } catch (e: any) {
      push("Current owner (ERR)", e?.response?.data ?? { error: e?.message });
    } finally {
      setBusy(false);
    }
  };

  const assign = async () => {
    if (!qr || !contractorId) return;
    setBusy(true);
    try {
      const res = await api.assignBin({ qr, contractor_id: contractorId });
      push("Assign bin", res);
      await lookup();
    } catch (e: any) {
      push("Assign bin (ERR)", e?.response?.data ?? { error: e?.message });
    } finally {
      setBusy(false);
    }
  };

  const unassign = async () => {
    if (!qr) return;
    setBusy(true);
    try {
      const res = await api.unassignBin({ qr });
      push("Unassign bin", res);
      await lookup();
    } catch (e: any) {
      push("Unassign bin (ERR)", e?.response?.data ?? { error: e?.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card">
      <h2>Admin: Bin Assignments</h2>

      <div className="grid3">
        <label>Bin QR
          <input value={qr} onChange={(e)=>setQr(e.target.value)} placeholder="QR123" />
        </label>
        <label>Contractor ID
          <input value={contractorId} onChange={(e)=>setContractorId(e.target.value)} placeholder="uuid-or-id" />
        </label>
        <div className="row" style={{alignItems:"end"}}>
          <button disabled={busy || !qr} onClick={lookup}>Lookup</button>
          <button disabled={busy || !qr || !contractorId} onClick={assign}>Assign</button>
          <button className="ghost" disabled={busy || !qr} onClick={unassign}>Unassign</button>
        </div>
      </div>

      {out ? (
        <details open className="result" style={{marginTop:10}}>
          <summary>
            <strong>{out.title}</strong> <span className="muted">at {out.at}</span>
          </summary>
          <pre>{pretty(out.payload)}</pre>
        </details>
      ) : null}
    </section>
  );
}
