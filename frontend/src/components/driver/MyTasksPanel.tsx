// path: frontend/src/components/driver/MyTasksPanel.tsx

import { useCallback, useEffect, useMemo, useState } from "react";
import { loadCfg } from "../../lib/devConfig";
import { getConfig, api } from "../../api";

type Job = {
  id: string;
  type: "DELIVER_EMPTY" | "RELOCATE_EMPTY" | "COLLECT_FULL" | "RETURN_EMPTY";
  status: "PENDING" | "IN_PROGRESS" | "DONE" | "FAILED";
  skip_qr?: string | null;
  from_zone_id?: string | null;
  to_zone_id?: string | null;
  destination_type?: string | null;
  destination_name?: string | null;
  window_start?: string | null;
  window_end?: string | null;
  notes?: string | null;
};

function joinUrl(base: string | undefined, path: string) {
  const b = String(base ?? "").replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}

export default function MyTasksPanel() {
  const [items, setItems] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string>("");

  const dev = loadCfg();
  const cfg = getConfig(); // { base, apiKey, adminKey }

  // Heuristic: detect UUID-like
  const looksLikeId = (s: string) => /^[0-9a-fA-F-]{20,}$/.test(s);

  const resolveDriverId = useCallback(async (): Promise<string | null> => {
    const ref = (dev.driverRef || dev.driverId || "").trim();
    if (!ref) return null;
    if (looksLikeId(ref)) return ref;

    // Try admin driver lookup by name via existing list API (requires admin key)
    try {
      if (!cfg.adminKey) return null;
      const all = await api.listDrivers(); // already adds admin X-API-Key
      // Prefer exact (case-insensitive) match on full_name or name
      const lower = ref.toLowerCase();
      const exact = all.find((d: any) =>
        (d.full_name?.toLowerCase?.() === lower) || (d.name?.toLowerCase?.() === lower)
      );
      if (exact?.id) return String(exact.id);
      // Fallback: first contains match
      const contains = all.find((d: any) =>
        d.full_name?.toLowerCase?.().includes(lower) || d.name?.toLowerCase?.().includes(lower)
      );
      if (contains?.id) return String(contains.id);
      return null;
    } catch {
      return null;
    }
  }, [dev.driverRef, dev.driverId, cfg.adminKey]);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setMsg("");
    try {
      const id = await resolveDriverId();
      if (!id) {
        setItems([]);
        setMsg("Set Config → Driver (name or id).");
        return;
      }
      // Call driver schedule using driver_id param (backend also accepts legacy 'driver')
      const url = joinUrl(cfg.base, `/driver/schedule?driver_id=${encodeURIComponent(id)}`);
      const res = await fetch(url, {
        headers: { "X-API-Key": cfg.apiKey || "" },
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }
      const data = (await res.json()) as Job[];
      setItems(Array.isArray(data) ? data : []);
      if (!Array.isArray(data) || data.length === 0) setMsg("No assigned tasks.");
    } catch (e: any) {
      setMsg(e?.message || "Failed to fetch");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [cfg.base, cfg.apiKey, resolveDriverId]);

  const markDone = useCallback(async (taskId: string) => {
    try {
      const url = joinUrl(cfg.base, `/driver/schedule/${encodeURIComponent(taskId)}/done`);
      const res = await fetch(url, {
        method: "PATCH",
        headers: { "X-API-Key": cfg.apiKey || "" },
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }
      await fetchTasks();
    } catch (e: any) {
      alert(e?.message || "Mark done failed");
    }
  }, [cfg.base, cfg.apiKey, fetchTasks]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Driver · My Tasks</h3>
        <button className="border rounded px-3 py-1" onClick={fetchTasks} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {msg && <div className="text-sm opacity-70">{msg}</div>}

      <div className="space-y-2">
        {items.map((j) => (
          <div key={j.id} className="border rounded p-3">
            <div className="text-sm opacity-70">{j.id}</div>
            <div className="font-medium">{j.type} · {j.status}</div>
            <div className="text-sm">
              {j.skip_qr ? `QR ${j.skip_qr} · ` : ""}
              {j.from_zone_id ? `from ${j.from_zone_id} ` : ""}
              {j.to_zone_id ? `→ ${j.to_zone_id}` : ""}
            </div>
            <div className="mt-2">
              <button className="border rounded px-2 py-1" onClick={() => markDone(j.id)} disabled={j.status === "DONE"}>
                {j.status === "DONE" ? "Done" : "Mark Done"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}