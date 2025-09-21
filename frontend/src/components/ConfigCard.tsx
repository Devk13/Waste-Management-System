// path: frontend/src/components/ConfigCard.tsx
import { useEffect, useState } from "react";
import { loadCfg, saveCfg, DevCfg } from "../lib/devConfig";

function normalizeBaseUrl(s: string): string {
  let v = (s || "").trim();
  v = v.replace(/\s+/g, "");
  if (!v) return "";
  return v.replace(/\/+$/, ""); // strip trailing slashes
}

export default function ConfigCard() {
  const [cfg, setCfg] = useState<DevCfg>({ baseUrl: "", adminKey: "", driverKey: "", driverRef: "" });
  const [saved, setSaved] = useState(false);

  useEffect(() => { setCfg(loadCfg()); }, []);

  const onSave = () => {
    const next: DevCfg = {
      ...cfg,
      baseUrl: normalizeBaseUrl(cfg.baseUrl || ""),
      adminKey: cfg.adminKey || "",
      driverKey: cfg.driverKey || "",
      driverRef: (cfg.driverRef || "").trim(),
    };
    saveCfg(next);               // saveCfg keeps driverId in sync for backward-compat
    setCfg(loadCfg());           // re-read to reflect normalization
    setSaved(true);
    setTimeout(() => setSaved(false), 1200);
  };

  const canSave = !!(cfg.baseUrl && cfg.baseUrl.trim());

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <h3 className="text-lg font-semibold">Config</h3>
      <div className="grid md:grid-cols-3 grid-cols-1 gap-2">
        <input
          className="border rounded p-2"
          placeholder="Base URL https://waste-management-system-cvss.onrender.com"
          value={cfg.baseUrl}
          onChange={e => setCfg({ ...cfg, baseUrl: e.target.value })}
        />
        <input
          className="border rounded p-2"
          type="password"
          placeholder="Driver API Key"
          value={cfg.driverKey || ""}
          onChange={e => setCfg({ ...cfg, driverKey: e.target.value })}
        />
        <input
          className="border rounded p-2"
          type="password"
          placeholder="Admin Key"
          value={cfg.adminKey || ""}
          onChange={e => setCfg({ ...cfg, adminKey: e.target.value })}
        />
        {/* New: name-or-id field */}
        <input
          className="border rounded p-2 md:col-span-3"
          placeholder="Driver (name or id), e.g., Alex"
          value={cfg.driverRef || ""}
          onChange={e => setCfg({ ...cfg, driverRef: e.target.value })}
        />
      </div>
      <button
        className="bg-black text-white rounded px-3 py-2 disabled:opacity-50"
        disabled={!canSave}
        onClick={onSave}
      >
        Save
      </button>
      {saved && <span className="text-xs ml-2 opacity-70">Saved.</span>}
    </div>
  );
}
