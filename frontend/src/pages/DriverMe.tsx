import { useEffect, useState } from "react";
import { getDriverMe, DriverMe } from "../api";

export default function DriverMePage() {
  const [data, setData] = useState<DriverMe | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getDriverMe().then(setData).catch(e => setErr(String(e)));
  }, []);

  if (err) return <div className="p-4 text-red-600">Error: {err}</div>;
  if (!data) return <div className="p-4">Loading…</div>;

  return (
    <div className="p-4 space-y-3">
      <h1 className="text-xl font-semibold">Driver Status</h1>
      <div className="rounded-xl border p-4">
        <div><b>User</b>: {data.user_id}</div>
        <div><b>Status</b>: {data.status}</div>
        <div><b>Updated</b>: {new Date(data.updated_at).toLocaleString()}</div>
      </div>

      <h2 className="text-lg font-medium mt-4">Open Assignment</h2>
      {!data.open_assignment ? (
        <div className="text-slate-500">None</div>
      ) : (
        <div className="rounded-xl border p-4">
          <div><b>ID</b>: {data.open_assignment.id}</div>
          <div><b>Skip</b>: {data.open_assignment.skip_id}</div>
          <div><b>QR</b>: {data.open_assignment.skip_qr_code ?? "—"}</div>
          <div><b>Status</b>: {data.open_assignment.status}</div>
        </div>
      )}
    </div>
  );
}
