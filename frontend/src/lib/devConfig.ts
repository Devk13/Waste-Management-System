// frontend/src/lib/devConfig.ts

export type DevCfg = {
  baseUrl: string;
  driverKey?: string;
  adminKey?: string;
  driverName?: string;   // optional, for “Driver · My Tasks”
  driverId?: string;     // optional, legacy
};

const STORAGE_KEY = "wm.devcfg.v1";
let cache: DevCfg | null = null;

/** Read config from localStorage with legacy fallbacks. */
function normalizeBaseUrl(s: string): string {
  const v = (s || "").trim().replace(/\s+/g, "");
  return v.replace(/\/+$/, ""); // strip trailing slashes
}

export function loadCfg(): DevCfg {
  if (cache) return cache;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) cache = JSON.parse(raw) as DevCfg;
  } catch {}
  cache = cache ?? { baseUrl: "" };
  return cache;
}

export function saveCfg(next: DevCfg): void {
  cache = { ...loadCfg(), ...next, baseUrl: normalizeBaseUrl(next.baseUrl) };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cache));
}

export function getConfig(): DevCfg {
  // simple alias used by components that just need the latest values
  return loadCfg();
}
