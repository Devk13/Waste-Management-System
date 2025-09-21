// path: frontend/src/lib/devConfig.ts

export type DevCfg = {
  baseUrl: string;
  adminKey?: string;
  driverKey?: string;
  /** New: free-form reference (name or id) */
  driverRef?: string;
  /** Legacy for backward-compat */
  driverId?: string;
};

const LS = "wm_dev_console_cfg";

export function loadCfg(): DevCfg {
  try {
    const raw = JSON.parse(localStorage.getItem(LS) || "{}");
    const baseUrl = typeof raw.baseUrl === "string" ? raw.baseUrl.trim() : "";
    const adminKey = typeof raw.adminKey === "string" ? raw.adminKey : "";
    const driverKey = typeof raw.driverKey === "string" ? raw.driverKey : "";
    const driverRef =
      (typeof raw.driverRef === "string" ? raw.driverRef : "") ||
      (typeof raw.driverId === "string" ? raw.driverId : ""); // fallback to old key
    const driverId = typeof raw.driverId === "string" ? raw.driverId : "";
    return { baseUrl, adminKey, driverKey, driverRef, driverId };
  } catch {
    return { baseUrl: "", adminKey: "", driverKey: "", driverRef: "", driverId: "" };
  }
}

export function saveCfg(next: Partial<DevCfg>) {
  const cur = loadCfg();
  const merged = { ...cur, ...next };
  // keep both keys synchronized for now
  if (typeof next.driverRef === "string") merged.driverId = next.driverRef;
  localStorage.setItem(LS, JSON.stringify(merged));
}
