// path: frontend/src/components/admin/JobsCard.tsx
import { useCallback, useEffect, useMemo, useState } from "react";
import { getConfig, api } from "../../api";

type JobType = "DELIVER_EMPTY" | "RELOCATE_EMPTY" | "COLLECT_FULL" | "RETURN_EMPTY";
type JobStatus = "PENDING" | "IN_PROGRESS" | "DONE" | "FAILED";

type Job = {
  id: string;
  type: JobType;
  status: JobStatus;
  skip_qr?: string | null;
  from_zone_id?: string | null;
  to_zone_id?: string | null;
  site_id?: string | null;
  destination_type?: string | null;
  destination_name?: string | null;
  window_start?: string | null;
  window_end?: string | null;
  assigned_driver_id?: string | null;
  assigned_vehicle_id?: string | null;
  notes?: string | null;
  created_at?: string;
};

type DriverRow = { id: string; full_name?: string; name?: string; phone?: string };
type VehicleRow = { id: string; reg_no?: string; plate?: string; make?: string; model?: string };

function joinUrl(base: string | undefined, path: string) {
  const b = String(base ?? "").replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}
const looksLikeId = (s: string) => /^[0-9a-fA-F-]{20,}$/.test((s || "").trim());

export default function JobsCard() {
  const cfg = getConfig(); // { base, apiKey, adminKey }

  // form
  const [type, setType] = useState<JobType>("DELIVER_EMPTY");
  const [skipQr, setSkipQr] = useState("");
  const [fromZone, setFromZone] = useState("");
  const [toZone, setToZone] = useState("");
  const [siteId, setSiteId] = useState("");
  const [destType, setDestType] = useState("RECYCLING");
  const [destName, setDestName] = useState("");
  const [winStart, setWinStart] = useState("");
  const [winEnd, setWinEnd] = useState("");
  const [notes, setNotes] = useState("");
  // name-or-id refs for UX
  const [driverRef, setDriverRef] = useState("");
  const [vehicleRef, setVehicleRef] = useState("");

  // board
  const [items, setItems] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string>("");

  // typeahead sources
  const [driversAll, setDriversAll] = useState<DriverRow[]>([]);
  const [vehiclesAll, setVehiclesAll] = useState<VehicleRow[]>([]);

  // why: UX labels that read well to humans
  const driverLabel = (d: DriverRow) =>
    (d.full_name || d.name || "(unnamed)") + ` — ${d.id.slice(0, 8)}`;
  const vehicleLabel = (v: VehicleRow) =>
    (v.reg_no || v.plate || "(no reg)") + ` — ${v.id.slice(0, 8)}`;

  // filter suggestions client-side (MVP)
  const driverSug = useMemo(() => {
    const q = (driverRef || "").toLowerCase().trim();
    if (!q) return driversAll.slice(0, 20);
    return driversAll
      .filter(d =>
        d.full_name?.toLowerCase?.().includes(q) ||
        d.name?.toLowerCase?.().includes(q) ||
        d.id?.toLowerCase?.().startsWith(q)
      )
      .slice(0, 20);
  }, [driversAll, driverRef]);

  const vehicleSug = useMemo(() => {
    const q = (vehicleRef || "").toLowerCase().trim();
    if (!q) return vehiclesAll.slice(0, 20);
    return vehiclesAll
      .filter(v =>
        v.reg_no?.toLowerCase?.().includes(q) ||
        v.plate?.toLowerCase?.().includes(q) ||
        v.id?.toLowerCase?.().startsWith(q)
      )
      .slice(0, 20);
  }, [vehiclesAll, vehicleRef]);

  const grouped = useMemo(() => {
    const by: Record<JobStatus, Job[]> = { PENDING: [], IN_PROGRESS: [], DONE: [], FAILED: [] };
    for (const j of items) by[j.status]?.push(j);
    return by;
  }, [items]);

  // load board + sources
  const fetchBoard = useCallback(async () => {
    if (!cfg.adminKey) { setErr("Set Admin Key in Config"); return; }
    setLoading(true); setErr("");
    try {
      const url = joinUrl(cfg.base, "/admin/jobs");
      const res = await fetch(url, { headers: { "X-API-Key": cfg.adminKey } });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const data = await res.json() as Job[];
      setItems(Array.isArray(data) ? data : []);
    } catch (e:any) {
      setErr(e?.message || "Failed to load jobs");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [cfg.base, cfg.adminKey]);

  useEffect(() => {
    let alive = true;
    (async () => {
      if (!cfg.adminKey) return;
      try {
        const [ds, vs] = await Promise.allSettled([api.listDrivers(), api.listVehicles()]);
        if (!alive) return;
        if (ds.status === "fulfilled" && Array.isArray(ds.value)) setDriversAll(ds.value);
        if (vs.status === "fulfilled" && Array.isArray(vs.value)) setVehiclesAll(vs.value);
      } catch {}
    })();
    return () => { alive = false; };
  }, [cfg.adminKey]);

  const resolveDriverId = useCallback(async (ref: string): Promise<string | null> => {
    const s = (ref || "").trim();
    if (!s) return null;
    if (looksLikeId(s)) return s;

    // exact match in loaded list first (fast, no extra calls)
    const lower = s.toLowerCase();
    const exact = driversAll.find(d =>
      d.full_name?.toLowerCase?.() === lower || d.name?.toLowerCase?.() === lower
    );
    if (exact?.id) return String(exact.id);
    const contains = driversAll.find(d =>
      d.full_name?.toLowerCase?.().includes(lower) || d.name?.toLowerCase?.().includes(lower)
    );
    if (contains?.id) return String(contains.id);

    // fallback: fresh fetch (in case lists are stale)
    try {
      const all = await api.listDrivers();
      const exactF = all.find((d:any) =>
        d?.full_name?.toLowerCase?.() === lower || d?.name?.toLowerCase?.() === lower
      );
      if (exactF?.id) return String(exactF.id);
      const containsF = all.find((d:any) =>
        d?.full_name?.toLowerCase?.().includes(lower) || d?.name?.toLowerCase?.().includes(lower)
      );
      if (containsF?.id) return String(containsF.id);
    } catch {}
    return null;
  }, [driversAll]);

  const resolveVehicleId = useCallback(async (ref: string): Promise<string | null> => {
    const s = (ref || "").trim();
    if (!s) return null;
    if (looksLikeId(s)) return s;

    const lower = s.toLowerCase();
    const exact = vehiclesAll.find(v =>
      v.reg_no?.toLowerCase?.() === lower || v.plate?.toLowerCase?.() === lower
    );
    if (exact?.id) return String(exact.id);
    const contains = vehiclesAll.find(v =>
      v.reg_no?.toLowerCase?.().includes(lower) || v.plate?.toLowerCase?.().includes(lower)
    );
    if (contains?.id) return String(contains.id);

    try {
      const all = await api.listVehicles();
      const exactF = all.find((v:any) =>
        v?.reg_no?.toLowerCase?.() === lower || v?.plate?.toLowerCase?.() === lower
      );
      if (exactF?.id) return String(exactF.id);
      const containsF = all.find((v:any) =>
        v?.reg_no?.toLowerCase?.().includes(lower) || v?.plate?.toLowerCase?.().includes(lower)
      );
      if (containsF?.id) return String(containsF.id);
    } catch {}
    return null;
  }, [vehiclesAll]);

  const createJob = useCallback(async () => {
    if (!cfg.adminKey) { alert("Set Admin Key in Config"); return; }

    const errs: string[] = [];
    if (!driverRef.trim()) errs.push("Driver (name or id) required");
    if (type === "DELIVER_EMPTY" && !toZone.trim()) errs.push("to_zone_id required for delivery");
    if (type === "RELOCATE_EMPTY" && (!fromZone.trim() || !toZone.trim())) errs.push("from/to zones required");
    if (type === "COLLECT_FULL" && (!skipQr.trim())) errs.push("skip_qr required for collect-full");
    if (errs.length) { alert(errs.join("\n")); return; }

    try {
      const [driverId, vehicleId] = await Promise.all([
        resolveDriverId(driverRef),
        vehicleRef.trim() ? resolveVehicleId(vehicleRef) : Promise.resolve(null),
      ]);
      if (!driverId) { alert("Driver not found. Use exact name or pick from suggestions."); return; }

      const payload: any = {
        type,
        skip_qr: skipQr || undefined,
        from_zone_id: fromZone || undefined,
        to_zone_id: toZone || undefined,
        site_id: siteId || undefined,
        destination_type: destName || destType ? destType : undefined,
        destination_name: destName || undefined,
        window_start: winStart || undefined,
        window_end: winEnd || undefined,
        assigned_driver_id: driverId,
        assigned_vehicle_id: vehicleId || undefined,
        notes: notes || undefined,
        status: "PENDING",
      };

      const url = joinUrl(cfg.base, "/admin/jobs");
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": cfg.adminKey },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      await fetchBoard();
      if (type === "DELIVER_EMPTY") { setSkipQr(""); setToZone(""); }
      if (type === "RELOCATE_EMPTY") { setFromZone(""); setToZone(""); setSkipQr(""); }
    } catch (e:any) {
      alert(e?.message || "Create job failed");
    }
  }, [
    cfg.base, cfg.adminKey,
    type, skipQr, fromZone, toZone, siteId, destType, destName, winStart, winEnd, notes,
    driverRef, vehicleRef, resolveDriverId, resolveVehicleId, fetchBoard
  ]);

  useEffect(() => { fetchBoard(); }, [fetchBoard]);

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Admin · Jobs</h3>
        <button className="border rounded px-3 py-1" onClick={fetchBoard} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {err && <div className="text-sm opacity-70">{err}</div>}

      {/* Form */}
      <div className="grid md:grid-cols-2 grid-cols-1 gap-2">
        <div className="border rounded p-3 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <label className="text-sm">Type
              <select className="border rounded w-full p-1" value={type} onChange={e=>setType(e.target.value as JobType)}>
                <option>DELIVER_EMPTY</option>
                <option>RELOCATE_EMPTY</option>
                <option>COLLECT_FULL</option>
                <option>RETURN_EMPTY</option>
              </select>
            </label>
            <label className="text-sm">Skip QR
              <input className="border rounded w-full p-1" value={skipQr} onChange={e=>setSkipQr(e.target.value)} placeholder="QR123"/>
            </label>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <label className="text-sm">From Zone
              <input className="border rounded w-full p-1" value={fromZone} onChange={e=>setFromZone(e.target.value)} placeholder="ZONE_A"/>
            </label>
            <label className="text-sm">To Zone
              <input className="border rounded w-full p-1" value={toZone} onChange={e=>setToZone(e.target.value)} placeholder="ZONE_B"/>
            </label>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <label className="text-sm">Site Id
              <input className="border rounded w-full p-1" value={siteId} onChange={e=>setSiteId(e.target.value)} placeholder="SITE1"/>
            </label>
            <label className="text-sm">Window Start (ISO)
              <input className="border rounded w-full p-1" value={winStart} onChange={e=>setWinStart(e.target.value)} placeholder="2025-09-21T08:00:00Z"/>
            </label>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <label className="text-sm">Window End (ISO)
              <input className="border rounded w-full p-1" value={winEnd} onChange={e=>setWinEnd(e.target.value)} placeholder="2025-09-21T12:00:00Z"/>
            </label>
            <label className="text-sm">Notes
              <input className="border rounded w-full p-1" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="optional"/>
            </label>
          </div>
        </div>

        <div className="border rounded p-3 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <label className="text-sm">Destination Type
              <select className="border rounded w-full p-1" value={destType} onChange={e=>setDestType(e.target.value)}>
                <option>RECYCLING</option>
                <option>LANDFILL</option>
                <option>TRANSFER</option>
              </select>
            </label>
            <label className="text-sm">Destination Name
              <input className="border rounded w-full p-1" value={destName} onChange={e=>setDestName(e.target.value)} placeholder="ECO MRF"/>
            </label>
          </div>

          {/* NEW: typeahead with datalist (why: allow typing names/regs) */}
          <label className="text-sm">Driver (name or id)
            <input className="border rounded w-full p-1" value={driverRef}
                   onChange={e=>setDriverRef(e.target.value)} placeholder="e.g. Alex" list="drivers-dl"/>
            <datalist id="drivers-dl">
              {driverSug.map(d => (
                <option key={d.id} value={d.full_name || d.name || ""} label={driverLabel(d)} />
              ))}
            </datalist>
          </label>

          <label className="text-sm">Vehicle (reg or id)
            <input className="border rounded w-full p-1" value={vehicleRef}
                   onChange={e=>setVehicleRef(e.target.value)} placeholder="e.g. TEST-001" list="vehicles-dl"/>
            <datalist id="vehicles-dl">
              {vehicleSug.map(v => (
                <option key={v.id} value={v.reg_no || v.plate || ""} label={vehicleLabel(v)} />
              ))}
            </datalist>
          </label>

          <div className="pt-2">
            <button className="border rounded px-3 py-2" onClick={createJob}>Create Job</button>
          </div>
        </div>
      </div>

      {/* Board */}
      <div className="grid md:grid-cols-4 grid-cols-1 gap-3 pt-3">
        {(["PENDING","IN_PROGRESS","DONE","FAILED"] as JobStatus[]).map(st => (
          <div key={st} className="border rounded p-2">
            <div className="font-semibold text-sm mb-2">{st}</div>
            {grouped[st].length === 0 ? (
              <div className="text-sm opacity-60">No jobs</div>
            ) : grouped[st].map(j => (
              <div key={j.id} className="border rounded p-2 mb-2">
                <div className="text-xs opacity-60">{j.id}</div>
                <div className="font-medium">{j.type}</div>
                <div className="text-xs">
                  {j.skip_qr ? `QR ${j.skip_qr} · ` : ""}
                  {j.from_zone_id ? `from ${j.from_zone_id} ` : ""}
                  {j.to_zone_id ? `→ ${j.to_zone_id}` : ""}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
