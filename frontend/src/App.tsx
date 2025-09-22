// path: frontend/src/App.tsx
import React, { useEffect, useMemo, useState } from "react";
import { api, getConfig, setConfig, pretty, ApiError } from "./api";
import "./styles.css";
import Toaster from "./ui/Toaster";
import { toast } from "./ui/toast";
import SkipCreateForm from "./components/SkipCreationForm";
// import { QRCodeSVG } from "qrcode.react"; // unused
import ContractorsAdmin from "./components/ContractorsAdmin";
import BinAssignmentsAdmin from "./components/BinAssignmentsAdmin";
// import ConfigCard from "./components/ConfigCard" // not used here
import JobsCard from "./components/admin/JobsCard";
import MyTasksPanel from "./components/driver/MyTasksPanel";
import { loadCfg as loadDevCfg, saveCfg as saveDevCfg } from "./lib/devConfig";

type PanelResult = { title: string; payload: any; at: string };
type Versions = { backend?: { env?: string; sha?: string; built_at?: string } };

function safeNum(v: string): number { const n = Number(v); return Number.isFinite(n) ? n : 0; }

function driverLabel(d:any){ return d?.full_name ?? d?.name ?? d?.email ?? d?.phone ?? "(unnamed)"; }

function vehicleLabel(v:any){ return v?.reg_no ?? v?.plate ?? v?.id ?? "(no reg)"; }

function openWithParams(base: string, path: string, params: Record<string,string>) {
  const url = new URL(path, base);
  Object.entries(params).forEach(([k,v]) => { if (v) url.searchParams.set(k, v); });
  window.open(url.toString(), "_blank");
}

function findWtnUrl(resp: unknown): string | null {
  if (!resp || typeof resp !== "object") return null;
  const obj = resp as Record<string, unknown>;
  if (typeof obj.wtn_pdf_url === "string" && obj.wtn_pdf_url) return obj.wtn_pdf_url;
  for (const v of Object.values(obj)) if (typeof v === "string" && v.includes("/wtn/") && v.endsWith(".pdf")) return v;
  return null;
}

// null-safe join
function joinUrl(base: string | undefined, path: string): string {
  const b = String(base ?? "").replace(/\/+$/, "");
  const p = path?.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}

// Minimal error boundary with reset
function Safe({ children }: { children: React.ReactNode }) {
  const [err, setErr] = React.useState<Error | null>(null);
  React.useEffect(() => {
    const onError = (e: ErrorEvent) => setErr(e.error || new Error(String(e.message || "unknown error")));
    const onRej = (e: PromiseRejectionEvent) => setErr(e.reason instanceof Error ? e.reason : new Error(String(e.reason)));
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRej);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRej);
    };
  }, []);
  if (!err) return <>{children}</>;
  return (
    <div style={{padding:16}}>
      <div className="card" style={{borderColor:"#f39"}}>
        <h2 style={{color:"#f39"}}>App crashed</h2>
        <p className="muted">{String(err.message)}</p>
        <div className="row" style={{gap:8}}>
          <button onClick={() => {
            try { localStorage.removeItem("wm_console_cfg"); localStorage.removeItem("wm_dev_console_cfg"); } catch {}
            location.href = location.origin + "/?v=" + Date.now();
          }}>Reset Config & Reload</button>
          <button className="ghost" onClick={() => console.error(err)}>Details (console)</button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [cfg, setCfg] = useState(getConfig());
  const [driverNameCfg, setDriverNameCfg] = useState<string>(() => {
  try { return loadDevCfg().driverName || "" } catch { return "" }
});
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<PanelResult[]>([]);
  const [ver, setVer] = useState<Versions | null>(null);

  // masters
  const [drivers, setDrivers] = useState<any[]>([]);
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [driverId, setDriverId] = useState<string>("");
  const [vehId, setVehId] = useState<string>("");

  // driver flow inputs
  const [qr, setQr] = useState("QR123");
  const [driverName, setDriverName] = useState("Alex");
  const [vehReg, setVehReg] = useState("TEST-001");
  const [zoneA, setZoneA] = useState("ZONE_A");
  const [zoneB, setZoneB] = useState("ZONE_B");
  const [zoneC, setZoneC] = useState("ZONE_C");
  const [gross, setGross] = useState(2500);
  const [tare, setTare] = useState(1500);
  const [destType, setDestType] = useState("RECYCLING");
  const [destName, setDestName] = useState("ECO MRF");
  const [siteId, setSiteId] = useState("SITE1");

  const pushOut = (title:string, payload:any) =>
    setOut((xs)=>[{title, payload, at:new Date().toLocaleTimeString()}, ...xs].slice(0,30));

  const save = () => {
  const trimmed = { ...cfg, base: (cfg.base || "").trim().replace(/\/+$/, "") };

  // writes both stores & rebuilds axios client
  setConfig(trimmed);

  // mirror driverName in dev store explicitly
  saveDevCfg({
    baseUrl: trimmed.base || "",
    adminKey: trimmed.adminKey || "",
    driverKey: trimmed.apiKey || "",
    driverName: driverNameCfg || "",
  });

  setCfg(getConfig());
  pushOut("Saved config", { ...trimmed, driverName: driverNameCfg });
  toast.success("Configuration saved");
};

  const [contractors, setContractors] = useState<any[]>([]);
  const [contractorId, setContractorId] = useState<string>("");

  // load masters (only when configured)
  useEffect(() => {
    if (!cfg.base || !cfg.adminKey) return;
    let cancelled = false;
    (async () => {
      try {
        const [ds, vs] = await Promise.all([api.listDrivers(), api.listVehicles()]);
        if (!cancelled) { setDrivers(ds); setVehicles(vs); }
      } catch (e: any) {
        toast.error("Failed to load drivers/vehicles", e?.message);
      }
    })();
    return () => { cancelled = true; };
  }, [cfg.base, cfg.adminKey]);

  // reflect selections
  useEffect(()=>{ const d = drivers.find(x=>x.id===driverId); if (d) setDriverName(driverLabel(d)); }, [driverId, drivers]);
  useEffect(()=>{ const v = vehicles.find(x=>x.id===vehId); if (v) setVehReg(vehicleLabel(v)); }, [vehId, vehicles]);

  const run = async <T,>(label:string, fn:()=>Promise<T>)=>{
    setBusy(true);
    try { const data = await fn(); pushOut(label, data); toast.success(`${label} ✓`); return data; }
    catch(e:any){
      const ae: ApiError | null = e instanceof ApiError ? e : null;
      pushOut(`${label} (ERR)`, { error:ae?.message || e?.message || String(e), code: ae?.code, fields: ae?.fields });
      toast.error(ae?.message || e?.message || "Request failed", label);
      throw e;
    }
    finally{ setBusy(false); }
  };

  useEffect(() => { (async () => {
    try { setContractors(await api.listContractors()); } catch {}
  })(); }, [cfg.base, cfg.adminKey]);

  // + Contractor
  const seedContractor = async () => {
    const name = prompt("Contractor org name", "ACME LTD");
    if (!name) return;
    const r = await run("Create contractor", () => api.createContractor({ org_name: name }));
    setContractors(await api.listContractors());
    setContractorId(r.id);
  };

  // mini creates
  const seedDriver = async () => {
    const name = prompt("Driver full name", "Alex");
    if (!name) return;
    try {
      const r = await run("Create driver", () => api.createDriver({ name }));
      setDrivers(await api.listDrivers());
      setDriverId(r.id);
    } catch (e: any) {
      // Gracefully handle duplicate
      if (e instanceof ApiError && e.code === 409) {
        toast.error("Driver already exists", name);
        const ds = await api.listDrivers();
        setDrivers(ds);
        const existing =
          ds.find((d:any) => (d.full_name ?? d.name ?? "").toLowerCase() === name.toLowerCase()) ||
          ds.find((d:any) => (d.name ?? "").toLowerCase() === name.toLowerCase());
        if (existing) setDriverId(existing.id);
        return;
      }
      throw e; // let our Safe boundary catch anything unexpected
    }
  };

  const seedVehicle = async () => {
    const reg = prompt("Vehicle reg", "TEST-001");
    if (!reg) return;

    try {
      const r = await run("Create vehicle", () =>
        api.createVehicle({ reg_no: reg })
      );
      // Created OK – refresh and select new one
      setVehicles(await api.listVehicles());
      setVehId(r.id);
    } catch (e: any) {
      // Gracefully handle duplicate registration
      if (e instanceof ApiError && e.code === 409) {
        toast.error("Vehicle already exists", reg);
        const vs = await api.listVehicles();
        setVehicles(vs);
        const existing =
          vs.find((v: any) =>
            (v.reg_no ?? v.plate ?? "").toLowerCase() === reg.toLowerCase()
          ) || null;
        if (existing) setVehId(existing.id);
        return;
      }
      // Anything else -> let the error bubble to the Safe boundary
      throw e;
    }
  };

  // Admin inline edit state
  const selDriver = useMemo(()=>drivers.find(d=>d.id===driverId)??null,[drivers,driverId]);
  const selVehicle = useMemo(()=>vehicles.find(v=>v.id===vehId)??null,[vehicles,vehId]);

  const [drvEdit, setDrvEdit] = useState<{name:string; phone?:string; license_no?:string; active:boolean} | null>(null);
  const [vehEdit, setVehEdit] = useState<{reg_no:string; make?:string; model?:string; active:boolean} | null>(null);
  const [drvErrs, setDrvErrs] = useState<Record<string,string>>({});
  const [vehErrs, setVehErrs] = useState<Record<string,string>>({});

  useEffect(()=>{ if (selDriver) setDrvEdit({
      name: selDriver.full_name ?? selDriver.name ?? "",
      phone: selDriver.phone ?? "",
      license_no: selDriver.license_no ?? "",
      active: Boolean(selDriver.active ?? true),
    }); else setDrvEdit(null);
    setDrvErrs({});
  }, [selDriver]);

  useEffect(()=>{ if (selVehicle) setVehEdit({
      reg_no: selVehicle.reg_no ?? "",
      make: selVehicle.make ?? "",
      model: selVehicle.model ?? "",
      active: Boolean(selVehicle.active ?? true),
    }); else setVehEdit(null);
    setVehErrs({});
  }, [selVehicle]);

  // validators
  function validateDriver(p:{name:string}): Record<string,string> {
    const e: Record<string,string> = {};
    if (!p.name?.trim()) e.name = "Name is required";
    if (p.name && p.name.length > 80) e.name = "Name too long";
    return e;
  }
  function validateVehicle(p:{reg_no:string}): Record<string,string> {
    const e: Record<string,string> = {};
    if (!p.reg_no?.trim()) e.reg_no = "Registration required";
    if (p.reg_no && p.reg_no.length > 32) e.reg_no = "Too long";
    return e;
  }

  const saveDriver = async ()=>{
    if (!driverId || !drvEdit) return;
    const errs = validateDriver(drvEdit); setDrvErrs(errs); if (Object.keys(errs).length) { toast.error("Fix validation errors", "Driver"); return; }
    try {
      await run("Update driver", ()=>api.updateDriver(driverId, {
        name: drvEdit.name, phone: drvEdit.phone, license_no: drvEdit.license_no, active: drvEdit.active,
      }));
      setDrivers(await api.listDrivers());
    } catch (e:any) {
      if (e instanceof ApiError && e.fields) setDrvErrs(prev=>({ ...prev, ...e.fields }));
    }
  };
  const deleteDriver = async ()=>{
    if (!driverId) return;
    if (!confirm("Delete this driver?")) return;
    await run("Delete driver", ()=>api.deleteDriver(driverId));
    setDriverId(""); setDrivers(await api.listDrivers());
  };

  const saveVehicle = async ()=>{
    if (!vehId || !vehEdit) return;
    const errs = validateVehicle(vehEdit); setVehErrs(errs); if (Object.keys(errs).length) { toast.error("Fix validation errors", "Vehicle"); return; }
    try {
      await run("Update vehicle", ()=>api.updateVehicle(vehId, vehEdit));
      setVehicles(await api.listVehicles());
    } catch (e:any) {
      if (e instanceof ApiError && e.fields) setVehErrs(prev=>({ ...prev, ...e.fields }));
    }
  };
  const deleteVehicle = async ()=>{
    if (!vehId) return;
    if (!confirm("Delete this vehicle?")) return;
    await run("Delete vehicle", ()=>api.deleteVehicle(vehId));
    setVehId(""); setVehicles(await api.listVehicles());
  };

  const runAll = async ()=>{
    await run("DEV ensure-skip", ()=>api.ensureSkipDev(qr));
    await run("driver/scan", ()=>api.scan(qr));
    await run("driver/deliver-empty", ()=>api.deliverEmpty({ skip_qr:qr, to_zone_id:zoneC, driver_name:driverName, vehicle_reg:vehReg }));
    await run("driver/relocate-empty", ()=>api.relocateEmpty({ skip_qr:qr, from_zone_id:zoneA, to_zone_id:zoneB, driver_name:driverName }));
    await run("driver/collect-full", ()=>api.collectFull({
      skip_qr:qr, destination_type:destType, destination_name:destName,
      weight_source:"WEIGHBRIDGE", gross_kg:gross, tare_kg:tare, driver_name:driverName, site_id:siteId, vehicle_reg:vehReg
    }));
    await run("driver/return-empty", ()=>api.returnEmpty({ skip_qr:qr, to_zone_id:zoneC, driver_name:driverName }));
  };

  const fetchVersions = async () => { const data = await run("meta/versions", api.versions) as Versions; setVer(data); };
  const envText = ver?.backend?.env ?? ""; const shaText = ver?.backend?.sha ?? ""; const builtAt = ver?.backend?.built_at ?? "";

  return (
    <Safe>
      <div className="wrap">
        <Toaster />
        <div className="header">
          <div>
            <h1>WMIS Dev Console</h1>
            <p className="muted">Driver flow + admin masters + WTN</p>
          </div>
          <div className="row">
            <div className="tag">{busy? "running…" : "idle"}</div>
            {envText || shaText ? (
              <div className="tag" title={builtAt ? `built ${builtAt}` : undefined}>
                {envText ? envText : "env"} • {shaText || "sha"}
              </div>
            ) : null}
          </div>
        </div>

        <section className="card">
          <h2>Config</h2>
          <div className="grid3">
            <label>Base URL<input value={cfg.base} onChange={(e)=>setCfg({...cfg, base:e.target.value})}/></label>
            <label>Driver API Key<input value={cfg.apiKey??""} onChange={(e)=>setCfg({...cfg, apiKey:e.target.value})}/></label>
            <label>Admin Key<input value={cfg.adminKey??""} onChange={(e)=>setCfg({...cfg, adminKey:e.target.value})}/></label>
            <label className="full"> Driver Name <input placeholder="e.g. Alex" value={driverNameCfg} onChange={(e) => setDriverNameCfg(e.target.value)} /> </label>
          </div>
          <div className="row"><button onClick={save}>Save</button></div>
        </section>

        <section className="card">
          <h2>Debug</h2>
          <div className="row">
            <button disabled={busy} onClick={()=>run("_meta/ping", api.health)}>Ping DB</button>
            <button disabled={busy} onClick={()=>run("__debug/routes", api.routes)}>Routes</button>
            <button disabled={busy} onClick={()=>run("__debug/mounts", api.mounts)}>Mounts</button>
            <button disabled={busy} onClick={() => run("__admin/bootstrap", api.bootstrap)}>Bootstrap DB </button>
            <button disabled={busy} onClick={()=>run("skips/__smoke", api.skipsSmoke)}>Skips Smoke</button>
            <button disabled={busy} onClick={fetchVersions}>Versions</button>
            
              <button disabled={busy} onClick={async ()=>{
                const r:any = await run("__debug/wtns", ()=>api.latestWtns(1));
                const u = r?.items?.[0]?.pdf_url; if (!u) { toast.error("No recent WTN"); return; }
                openWithParams(cfg.base, u, { format: "html", key: cfg.adminKey || "" });
              }}>Open Latest WTN (HTML)</button>

              <button disabled={busy} onClick={async ()=>{
                const r:any = await run("__debug/wtns", ()=>api.latestWtns(1));
                const u = r?.items?.[0]?.pdf_url; if (!u) { toast.error("No recent WTN"); return; }
                openWithParams(cfg.base, u, { format: "pdf", key: cfg.adminKey || "" });
              }}>Open Latest WTN (PDF)</button>
          </div>
        </section>

        <section className="card">
          <h2>Dispatch (Jobs & My Tasks)</h2>
          <div className="row wrap" style={{ gap: 16 }}>
            <div style={{ flex: 1, minWidth: 320 }}>
              <JobsCard />
            </div>
            <div style={{ flex: 1, minWidth: 320 }}>
              <MyTasksPanel />
            </div>
          </div>
        </section>

        {/* Admin CRUD */}
        <section className="card">
          <h2>Admin: Drivers & Vehicles</h2>
          <div className="grid3">
            <label>Driver
              <select value={driverId} onChange={(e)=>setDriverId(e.target.value)}>
                <option value="">-- select driver --</option>
                {drivers.map((d:any)=><option key={d.id} value={d.id}>{driverLabel(d)}</option>)}
              </select>
            </label>
            <label>Vehicle
              <select value={vehId} onChange={(e)=>setVehId(e.target.value)}>
                <option value="">-- select vehicle --</option>
                {vehicles.map((v:any)=><option key={v.id} value={v.id}>{vehicleLabel(v)}</option>)}
              </select>
            </label>
            <div className="row">
              <button onClick={seedDriver}>+ Driver</button>
              <button onClick={seedVehicle}>+ Vehicle</button>
            </div>
          </div>

          {drvEdit && (
            <div style={{marginTop:12}}>
              <h3 style={{margin:"8px 0"}}>Edit Driver</h3>
              <div className="grid3">
                <label>Name
                  <input value={drvEdit.name} onChange={(e)=>{ setDrvEdit({...drvEdit!, name:e.target.value}); setDrvErrs({...drvErrs, name:""}); }}/>
                  {drvErrs.name ? <small style={{color:"#f39"}}>{drvErrs.name}</small> : null}
                </label>
                <label>Phone<input value={drvEdit.phone??""} onChange={(e)=>setDrvEdit({...drvEdit!, phone:e.target.value})}/></label>
                <label>License #<input value={drvEdit.license_no??""} onChange={(e)=>setDrvEdit({...drvEdit!, license_no:e.target.value})}/></label>
              </div>
              <div className="row" style={{marginTop:8}}>
                <label className="row"><input type="checkbox" checked={drvEdit.active} onChange={(e)=>setDrvEdit({...drvEdit!, active:e.target.checked})}/> Active</label>
                <button disabled={!!validateDriver(drvEdit).name} onClick={saveDriver}>Save</button>
                <button className="ghost" onClick={deleteDriver}>Delete</button>
              </div>
            </div>
          )}

          {vehEdit && (
            <div style={{marginTop:12}}>
              <h3 style={{margin:"8px 0"}}>Edit Vehicle</h3>
              <div className="grid3">
                <label>Reg No
                  <input value={vehEdit.reg_no} onChange={(e)=>{ setVehEdit({...vehEdit!, reg_no:e.target.value}); setVehErrs({...vehErrs, reg_no:""}); }}/>
                  {vehErrs.reg_no ? <small style={{color:"#f39"}}>{vehErrs.reg_no}</small> : null}
                </label>
                <label>Make<input value={vehEdit.make??""} onChange={(e)=>setVehEdit({...vehEdit!, make:e.target.value})}/></label>
                <label>Model<input value={vehEdit.model??""} onChange={(e)=>setVehEdit({...vehEdit!, model:e.target.value})}/></label>
              </div>
              <div className="row" style={{marginTop:8}}>
                <label className="row"><input type="checkbox" checked={vehEdit.active} onChange={(e)=>setVehEdit({...vehEdit!, active:e.target.checked})}/> Active</label>
                <button disabled={!!validateVehicle(vehEdit).reg_no} onClick={saveVehicle}>Save</button>
                <button className="ghost" onClick={deleteVehicle}>Delete</button>
              </div>
            </div>
          )}
        </section>

        <ContractorsAdmin onResult={(title, payload) => pushOut(title, payload)} />
        <BinAssignmentsAdmin onResult={(title, payload) => pushOut(title, payload)} />

        {/* Skip create */}
        <SkipCreateForm onSeed={(seededQr) => setQr(seededQr)} />
        <section className="card">
          <h2>Seed & Driver Flow</h2>
          <div className="grid3">
            <label>QR<input value={qr} onChange={(e)=>setQr(e.target.value)}/></label>
            <label>Zones A/B/C<div className="row">
              <input value={zoneA} onChange={(e)=>setZoneA(e.target.value)} style={{width: "33%"}}/>
              <input value={zoneB} onChange={(e)=>setZoneB(e.target.value)} style={{width: "33%"}}/>
              <input value={zoneC} onChange={(e)=>setZoneC(e.target.value)} style={{width: "33%"}}/>
            </div></label>
            <label>Destination<input value={destName} onChange={(e)=>setDestName(e.target.value)}/></label>
          </div>
          <div className="grid3">
            <label>Driver name<input value={driverName} onChange={(e)=>setDriverName(e.target.value)}/></label>
            <label>Vehicle reg<input value={vehReg} onChange={(e)=>setVehReg(e.target.value)}/></label>
            <label>Dest. Type<select value={destType} onChange={(e)=>setDestType(e.target.value)}>
              <option>RECYCLING</option><option>LANDFILL</option><option>TRANSFER</option>
            </select></label>
          </div>
          <div className="grid3">
            <label>Gross (kg)<input type="number" value={gross} onChange={(e)=>setGross(safeNum(e.target.value))}/></label>
            <label>Tare (kg)<input type="number" value={tare} onChange={(e)=>setTare(safeNum(e.target.value))}/></label>
            <label>Site ID<input value={siteId} onChange={(e)=>setSiteId(e.target.value)}/></label>
          </div>
          <div className="row wrap" style={{marginTop:8}}>
            <button disabled={busy} onClick={()=>run("DEV ensure-skip", ()=>api.ensureSkipDev(qr))}>Seed skip</button>
            <button disabled={busy} onClick={()=>run("driver/scan", ()=>api.scan(qr))}>Scan</button>
            <button disabled={busy} onClick={()=>run("driver/deliver-empty", ()=>api.deliverEmpty({ skip_qr:qr, to_zone_id:zoneC, driver_name:driverName, vehicle_reg:vehReg }))}>Deliver Empty</button>
            <button disabled={busy} onClick={()=>run("driver/relocate-empty", ()=>api.relocateEmpty({ skip_qr:qr, from_zone_id:zoneA, to_zone_id:zoneB, driver_name:driverName }))}>Relocate Empty</button>
            <button disabled={busy} onClick={()=>run("driver/collect-full", ()=>api.collectFull({ skip_qr:qr, destination_type:destType, destination_name:destName, weight_source:"WEIGHBRIDGE", gross_kg:gross, tare_kg:tare, driver_name:driverName, site_id:siteId, vehicle_reg:vehReg }))}>Collect Full</button>
            <button disabled={busy} onClick={()=>run("driver/return-empty", ()=>api.returnEmpty({ skip_qr:qr, to_zone_id:zoneC, driver_name:driverName }))}>Return Empty</button>
            <button className="primary" disabled={busy} onClick={runAll}>Run Full Flow</button>
          </div>
        </section>

        <section className="card">
          <h2>Results</h2>
          {out.length===0 ? <p className="muted">No calls yet.</p> : null}
          {out.map((o,i)=>{
            const wtnUrl = findWtnUrl(o.payload);
            const htmlUrl = wtnUrl ? `${joinUrl(cfg.base, wtnUrl)}?format=html` : null;
            const pdfUrl = wtnUrl ? `${joinUrl(cfg.base, wtnUrl)}?format=pdf` : null;
            return (
              <details key={i} open={i===0} className="result">
                <summary><strong>{o.title}</strong> <span className="muted">at {o.at}</span></summary>
                <pre>{pretty(o.payload)}</pre>
                {wtnUrl && (
                  <div className="row" style={{ gap: 8, marginTop: 8 }}>
                    <a className="btn" href={htmlUrl!} target="_blank" rel="noreferrer">Open WTN (HTML)</a>
                    <a className="btn" href={pdfUrl!} target="_blank" rel="noreferrer">Open PDF</a>
                  </div>
                )}
              </details>
            );
          })}
        </section>
      </div>
    </Safe>
  );
}
