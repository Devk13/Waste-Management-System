// path: frontend/src/lib/devConfig.ts

export type DevCfg = {
  baseUrl: string
  adminKey?: string
  driverKey?: string
  driverId?: string
}
const STORAGE_KEY = "wm_dev_console_cfg"

export function loadCfg(): DevCfg {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : { baseUrl: "" }
  } catch {
    return { baseUrl: "" }
  }
}

export function saveCfg(cfg: DevCfg) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg))
}
