// frontend/src/lib/devConfig.ts

export type DevCfg = {
  baseUrl: string;
  driverKey?: string;
  adminKey?: string;

  // NEW
  driverName?: string;

  // Legacy (still read, but we won't write it anymore)
  driverId?: string;
};

const KEY = "wm_dev_console_cfg";

/** Read config from localStorage with legacy fallbacks. */
export function loadCfg(): DevCfg {
  try {
    const raw = localStorage.getItem(KEY);
    const cur = raw ? JSON.parse(raw) as Partial<DevCfg> : {};

    // legacy store used by older panels
    const legacyRaw = localStorage.getItem("wm_console_cfg");
    const legacy = legacyRaw ? JSON.parse(legacyRaw) as any : {};

    const baseUrl   = String(cur.baseUrl   ?? legacy.base   ?? "");
    const driverKey = String(cur.driverKey ?? legacy.apiKey ?? "");
    const adminKey  = String(cur.adminKey  ?? legacy.adminKey ?? "");

    // prefer name; fall back to any old id if present
    const driverName = String(
      (cur.driverName ?? legacy.driverName ?? cur.driverId ?? legacy.driverId ?? "")
    );

    return { baseUrl, driverKey, adminKey, driverName };
  } catch {
    return { baseUrl: "" };
  }
}

/** Save (merge) config. We write `driverName`, not `driverId`. */
export function saveCfg(next: Partial<DevCfg>) {
  const cur = loadCfg();
  const merged: DevCfg = {
    baseUrl: (next.baseUrl ?? cur.baseUrl ?? "").replace(/\/+$/, ""),
    driverKey: next.driverKey ?? cur.driverKey,
    adminKey:  next.adminKey  ?? cur.adminKey,
    driverName: next.driverName ?? cur.driverName,
  };
  localStorage.setItem(KEY, JSON.stringify(merged));
}

export function resetCfg() {
  localStorage.removeItem(KEY);
}
