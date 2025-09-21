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
    const raw = localStorage.getItem("wm_dev_console_cfg");
    const obj = raw ? JSON.parse(raw) : {};
    return {
      baseUrl: typeof obj.baseUrl === "string" ? obj.baseUrl : String(obj.baseUrl ?? ""),
      adminKey: typeof obj.adminKey === "string" ? obj.adminKey : "",
      driverKey: typeof obj.driverKey === "string" ? obj.driverKey : "",
      driverId:  typeof obj.driverId  === "string" ? obj.driverId  : "",
    };
  } catch { return { baseUrl: "" }; }
}

export function saveCfg(cfg: DevCfg) {
  const baseUrl = (cfg.baseUrl || "").toString().trim().replace(/\/+$/, ""); // strip trailing slashes
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...cfg, baseUrl }));
}
