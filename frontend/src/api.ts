// ======================================================================
// path: frontend/src/api.ts
// ======================================================================
import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

export type ApiConfig = { base: string; apiKey?: string | null; adminKey?: string | null };
const LS_KEY = "wm_dev_console_cfg";

function loadConfig(): ApiConfig {
  try { const raw = localStorage.getItem(LS_KEY); if (raw) return JSON.parse(raw); } catch {}
  return { base: (import.meta as any).env?.VITE_API_BASE || window.location.origin, apiKey: "", adminKey: "" };
}
function saveConfig(c: ApiConfig) { localStorage.setItem(LS_KEY, JSON.stringify(c)); }

let cfg = loadConfig();
let client: AxiosInstance = createClient(cfg);

function createClient(c: ApiConfig): AxiosInstance {
  const inst = axios.create({ baseURL: c.base.replace(/\/+$/, ""), timeout: 20000 });
  inst.interceptors.request.use((req) => {
    const url = (req.url || "").toLowerCase();
    const h: Record<string, string> = (req.headers as any) || {};
    const needsDriverKey = url.startsWith("/driver") || url.includes("/ensure-skip");
    const needsAdminKey  = url.startsWith("/admin") || url.startsWith("/skips/_seed");
    if (needsDriverKey && c.apiKey) h["X-API-Key"] = c.apiKey!;
    if (needsAdminKey  && c.adminKey) h["X-API-Key"] = c.adminKey!;
    req.headers = h as any;
    return req;
  });
  return inst;
}

export function setConfig(next: ApiConfig) { cfg = next; saveConfig(cfg); client = createClient(cfg); }
export function getConfig(): ApiConfig { return cfg; }

async function get<T=any>(url: string, config?: AxiosRequestConfig){ return (await client.get<T>(url, config)).data; }
async function post<T=any>(url: string, body?: any, config?: AxiosRequestConfig){ return (await client.post<T>(url, body??{}, config)).data; }
async function patch<T=any>(url: string, body?: any){ return (await client.patch<T>(url, body??{})).data; }
async function del<T=any>(url: string){ return (await client.delete<T>(url)).data; }

// ---------- Error normalization ----------
export type FieldErrors = Record<string, string>;
export class ApiError extends Error {
  code: number; fields?: FieldErrors;
  constructor(message: string, code: number, fields?: FieldErrors) { super(message); this.code = code; this.fields = fields; }
}

function parseApiError(e: any): ApiError {
  const code = e?.response?.status ?? 0;
  const data = e?.response?.data ?? {};
  // FastAPI validation array → field map
  const as422 = (d: any): FieldErrors => {
    const out: FieldErrors = {};
    if (Array.isArray(d?.detail)) {
      for (const it of d.detail) {
        const loc = (it?.loc || []).slice(1).join(".") || "non_field";
        const msg = it?.msg || it?.message || "Invalid value";
        out[loc] = msg;
      }
    }
    return out;
  };

function createClient(c: ApiConfig): AxiosInstance {
  const inst = axios.create({ baseURL: c.base.replace(/\/+$/, ""), timeout: 20000 });
  inst.interceptors.request.use((req) => {
    const url = (req.url || "").toLowerCase();
    const h: Record<string, string> = (req.headers as any) || {};
    const needsDriverKey = url.startsWith("/driver") || url.includes("/ensure-skip");
    const needsAdminKey  = url.startsWith("/admin") || url.startsWith("/skips/_seed") || url.startsWith("/__debug");
    if (needsDriverKey && c.apiKey)  h["X-API-Key"] = c.apiKey!;
    if (needsAdminKey  && c.adminKey) h["X-API-Key"] = c.adminKey!;
    req.headers = h as any;
    return req;
  });
  return inst;
}

  // Common server shapes
  let message =
    data?.detail?.message || data?.detail || data?.error || e?.message || "Request failed";
  let fields: FieldErrors | undefined;

  if (code === 422) fields = as422(data);
  if (code === 409) {
    // Try infer unique field
    const txt = String(message).toLowerCase();
    if (txt.includes("reg") || txt.includes("vehicle")) fields = { reg_no: "Registration already exists" };
    if (txt.includes("driver") || txt.includes("name")) fields = { name: "Driver with this name already exists" };
    message = "Duplicate value";
  }
  return new ApiError(message, code, fields);
}

// ---------- API surface ----------
export const api = {
  // debug/meta
  health: () => get("/_meta/ping"),
  routes: () => get("/__debug/routes"),
  mounts: () => get("/__debug/mounts"),
  skipsSmoke: () => get("/skips/__smoke"),
  versions: () => get("/meta/versions"),
  latestWtns: (limit = 5) => get(`/__debug/wtns?limit=${limit}`), // admin-gated in prod
  meta: async () => {
    try { return await get("/meta/config"); }
    catch { return { skip:{ colors:{ green:{label:"Recycling"} }, sizes:{ sizes_m3:[6,8,12] } } }; }
  },

  // dev seed
  ensureSkipDev: async (qr: string) => {
    try { return await post("/driver/dev/ensure-skip", { qr_code: qr, qr }); }
    catch (e:any){ if (e?.response?.status===422) return await get(`/driver/dev/ensure-skip?qr=${encodeURIComponent(qr)}`); throw parseApiError(e); }
  },

  // driver flow
  scan: async (qr: string) => {
    try { return await get(`/driver/scan?qr=${encodeURIComponent(qr)}`); }
    catch (e:any){ if ([400,422].includes(e?.response?.status)) return await get(`/driver/scan?q=${encodeURIComponent(qr)}`); throw parseApiError(e); }
  },
  deliverEmpty: async (p:{skip_qr:string;to_zone_id:string;driver_name:string;vehicle_reg?:string;}) => {
    try { return await post("/driver/deliver-empty", p); } catch(e:any){ throw parseApiError(e); }
  },
  relocateEmpty: async (p:{skip_qr:string;from_zone_id?:string;to_zone_id:string;driver_name:string;}) => {
    try { return await post("/driver/relocate-empty", p); } catch(e:any){ throw parseApiError(e); }
  },
  collectFull: async (p:{skip_qr:string;destination_type:string;destination_name:string;weight_source:string;gross_kg?:number;tare_kg?:number;net_kg?:number;driver_name:string;site_id?:string;vehicle_reg?:string;}) => {
    try { return await post("/driver/collect-full", p); } catch(e:any){ throw parseApiError(e); }
  },
  returnEmpty: async (p:{skip_qr:string;to_zone_id:string;driver_name:string;}) => {
    try { return await post("/driver/return-empty", p); } catch(e:any){ throw parseApiError(e); }
  },

  // admin: drivers
  listDrivers: () => get("/admin/drivers"),
  createDriver: async (p:{ name:string; phone?:string; email?:string; license_no?:string; active?:boolean }) => {
    try { return await post("/admin/drivers", p); } catch(e:any){ throw parseApiError(e); }
  },
  updateDriver: async (id:string, p:Partial<{ name:string; phone:string; email:string; license_no:string; active:boolean }>) => {
    try { return await patch(`/admin/drivers/${id}`, p); } catch(e:any){ throw parseApiError(e); }
  },
  deleteDriver: async (id:string) => {
    try { return await del(`/admin/drivers/${id}`); } catch(e:any){ throw parseApiError(e); }
  },

  // admin: vehicles
  listVehicles: () => get("/admin/vehicles"),
  createVehicle: async (p:{ reg_no:string; make?:string; model?:string; active?:boolean }) => {
    try { return await post("/admin/vehicles", p); } catch(e:any){ throw parseApiError(e); }
  },
  updateVehicle: async (id:string, p:Partial<{ reg_no:string; make:string; model:string; active:boolean }>) => {
    try { return await patch(`/admin/vehicles/${id}`, p); } catch(e:any){ throw parseApiError(e); }
  },
  deleteVehicle: async (id:string) => {
    try { return await del(`/admin/vehicles/${id}`); } catch(e:any){ throw parseApiError(e); }
  },
};

export type Json = any; export function pretty(x:Json){ try{return JSON.stringify(x,null,2)}catch{return String(x)} }
export type SkipCreateIn = { qr:string; color:string; size:string; notes?:string };
export async function adminCreateSkip(p: SkipCreateIn) {
  try { return await post("/skips/_seed", p, { headers: { "X-API-Key": getConfig().adminKey || "" } }); }
  catch (e:any) {
    if ([401,403,404,405].includes(e?.response?.status)) {
      return await post("/driver/dev/ensure-skip", { qr_code:p.qr, qr:p.qr }, { headers: { "X-API-Key": getConfig().adminKey || getConfig().apiKey || "" } });
    }
    throw parseApiError(e);
  }
}

export type DriverMe = {
  id: string;
  name: string;
  phone?: string;
  license_no?: string;
  active?: boolean;
};

export async function getDriverMe(): Promise<DriverMe> {
  return { id: "drv-demo", name: "Demo Driver" };
}

export async function searchFacilities(_q: string): Promise<Array<{ id: string; name: string }>> {
  return [{ id: "ECO_MRF", name: "ECO MRF" }];
}
export async function searchZones(_q: string): Promise<Array<{ id: string; name: string }>> {
  return [
    { id: "ZONE_A", name: "ZONE_A" },
    { id: "ZONE_B", name: "ZONE_B" },
    { id: "ZONE_C", name: "ZONE_C" },
  ];
}

export async function dropAtFacility(p: {
  skip_qr: string;
  facility_name: string;
  weight_source: string;
  gross_kg?: number;
  tare_kg?: number;
  net_kg?: number;
  driver_name: string;
  vehicle_reg?: string;
  site_id?: string;
}) {
  return await api.collectFull({
    skip_qr: p.skip_qr,
    destination_type: "TRANSFER",
    destination_name: p.facility_name,
    weight_source: p.weight_source,
    gross_kg: p.gross_kg,
    tare_kg: p.tare_kg,
    net_kg: p.net_kg,
    driver_name: p.driver_name,
    vehicle_reg: p.vehicle_reg,
    site_id: p.site_id,
  });
}
