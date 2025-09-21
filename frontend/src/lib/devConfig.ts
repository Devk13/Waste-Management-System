// path: frontend/src/lib/devConfig.ts

export type DevCfg = {
  baseUrl: string;
  adminKey?: string;
  driverKey?: string;
  driverId?: string;
};
const STORAGE_KEY = "wm_dev_console_cfg";

export function loadCfg(): DevCfg {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const obj = raw ? JSON.parse(raw) : {};
    // Coerce to strings to avoid .replace/.endsWith crashes
    const baseUrl = typeof obj.baseUrl === "string" ? obj.baseUrl : String(obj.baseUrl ?? "");
    const adminKey = typeof obj.adminKey === "string" ? obj.adminKey : "";
    const driverKey = typeof obj.driverKey === "string" ? obj.driverKey : "";
    const driverId  = typeof obj.driverId  === "string" ? obj.driverId  : "";
    return { baseUrl, adminKey, driverKey, driverId };
  } catch {
    return { baseUrl: "" };
  }
}

export function saveCfg(cfg: DevCfg) {
  const baseUrl = (cfg.baseUrl || "").toString().trim().replace(/\/+$/, ""); // strip trailing slashes
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...cfg, baseUrl }));
}
