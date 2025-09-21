// frontend/src/api.ts
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

// ---- SINGLE createClient (keep only this one) ----
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

export function setConfig(next: ApiConfig) { cfg = next; saveConfig(cfg); client = createClient(cfg); }
export function getConfig(): ApiConfig { return cfg; }

async function get<T=any>(url: string, config?: AxiosRequestConfig){ return (await client.get<T>(url, config)).data; }
async function post<T=any>(url: string, body?: any, config?: AxiosRequestConfig){ return (await client.post<T>(url, body??{}, config)).data; }
async function patch<T=any>(url: string, body?: any){ return (await client.patch<T>(url, body??{})).data; }
async function del<T=any>(url: string){ return (await client.delete<T>(url)).data; }

// ---- Error normalization ----
export type FieldErrors = Record<string, string>;
export class ApiError extends Error {
  code: number; fields?: FieldErrors;
  constructor(message: string, code: number, fields?: FieldErrors) { super(message); this.code = code; this.fields = fields; }
}
function parseApiError(e: any): ApiError {
  const code = e?.response?.status ?? 0;
  const data = e?.response?.data ?? {};
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

  let message = data?.detail?.message || data?.detail || data?.error || e?.message || "Request failed";
  let fields: FieldErrors | undefined;
  if (code === 422) fields = as422(data);
  if (code === 409) {
    const txt = String(message).toLowerCase();
    if (txt.includes("reg"))   fields = { reg_no: "Registration already exists" };
    if (txt.includes("name"))  fields = { name: "Driver with this name already exists" };
    message = "Duplicate value";
  }
  return new ApiError(message, code, fields);
}

// ---- API surface ----
export const api = {
  health: () => get("/_meta/ping"),
  routes: () => get("/__debug/routes"),
  mounts: () => get("/__debug/mounts"),
  skipsSmoke: () => get("/skips/__smoke"),
  bootstrap: () => post("/__admin/bootstrap", {}, { headers: { "X-API-Key": getConfig().adminKey || "" } }),
  versions: () => get("/meta/versions"),
  latestWtns: (limit = 5) => get(`/__debug/wtns?limit=${limit}`),
  meta: async () => {
  const fallback = { skip: { colors: { green: { label: "Recycling" } }, sizes: { sizes_m3: [6, 8, 12] } } };

  const fetchSafe = async (path: string) => {
    try { return await get(path); } catch { return null; }
  };

  let raw = await fetchSafe("/meta/config");
  if (!raw) raw = await fetchSafe("/_meta/config");
  if (!raw) return fallback;

  // normalize into: { skip: { colors: Record<string,any>, sizes: { sizes_m3?: (number|string)[], wheelie_l?: (number|string)[], rolloff_yd?: (number|string)[] } } }
  const colors =
    raw?.skip?.colors ??
    raw?.colors ??
    raw?.SKIP_COLOR_SPEC ??
    {};

  const sizesSrc =
    raw?.skip?.sizes ??
    raw?.sizes ??
    {
      sizes_m3: raw?.SKIP_SIZES_M3 ?? raw?.SKIP_SIZES ?? undefined,
      wheelie_l: raw?.WHEELIE_LITRES ?? undefined,
      rolloff_yd: raw?.ROLLOFF_YARDS ?? undefined,
    };

  const toStrArr = (v: unknown) =>
    Array.isArray(v) ? v.map(x => (x == null ? "" : String(x))) : [];

  const sizes = Object.fromEntries(
    Object.entries(sizesSrc).map(([k, v]) => [k, toStrArr(v)])
  );

  return { skip: { colors, sizes } };
},

  ensureSkipDev: async (qr: string) => {
    try { return await post("/driver/dev/ensure-skip", { qr_code: qr, qr }); }
    catch (e:any){ if (e?.response?.status===422) return await get(`/driver/dev/ensure-skip?qr=${encodeURIComponent(qr)}`); throw parseApiError(e); }
  },

  scan: async (qr: string) => {
    try { return await get(`/driver/scan?qr=${encodeURIComponent(qr)}`); }
    catch (e:any){ if ([400,422].includes(e?.response?.status)) return await get(`/driver/scan?q=${encodeURIComponent(qr)}`); throw parseApiError(e); }
  },
  deliverEmpty:  (p:{skip_qr:string;to_zone_id:string;driver_name:string;vehicle_reg?:string;}) => post("/driver/deliver-empty", p).catch((e)=>{throw parseApiError(e)}),
  relocateEmpty: (p:{skip_qr:string;from_zone_id?:string;to_zone_id:string;driver_name:string;})      => post("/driver/relocate-empty", p).catch((e)=>{throw parseApiError(e)}),
  collectFull:   (p:{skip_qr:string;destination_type:string;destination_name:string;weight_source:string;gross_kg?:number;tare_kg?:number;net_kg?:number;driver_name:string;site_id?:string;vehicle_reg?:string;}) => post("/driver/collect-full", p).catch((e)=>{throw parseApiError(e)}),
  returnEmpty:   (p:{skip_qr:string;to_zone_id:string;driver_name:string;})                             => post("/driver/return-empty", p).catch((e)=>{throw parseApiError(e)}),

  // drivers
  listDrivers:   () => get("/admin/drivers"),
  createDriver:  (p:{ name:string; phone?:string; email?:string; license_no?:string; active?:boolean }) => post("/admin/drivers", p).catch((e)=>{throw parseApiError(e)}),
  updateDriver:  (id:string, p:Partial<{ name:string; phone:string; email:string; license_no:string; active:boolean }>) => patch(`/admin/drivers/${id}`, p).catch((e)=>{throw parseApiError(e)}),
  deleteDriver:  (id:string) => del(`/admin/drivers/${id}`).catch((e)=>{throw parseApiError(e)}),

  // vehicles
  listVehicles:  () => get("/admin/vehicles"),
  createVehicle: (p:{ reg_no:string; make?:string; model?:string; active?:boolean }) => post("/admin/vehicles", p).catch((e)=>{throw parseApiError(e)}),
  updateVehicle: (id:string, p:Partial<{ reg_no:string; make:string; model:string; active:boolean }>) => patch(`/admin/vehicles/${id}`, p).catch((e)=>{throw parseApiError(e)}),
  deleteVehicle: (id:string) => del(`/admin/vehicles/${id}`).catch((e)=>{throw parseApiError(e)}),

  // --- contractors ---
listContractors: () => get("/admin/contractors"),
// create (note the required org_name)
createContractor: async (p:{ org_name:string; contact_name?:string; email?:string; phone?:string; billing_address?:string; active?:boolean }) => {
  try { return await post("/admin/contractors", p); } catch (e:any) { throw parseApiError(e); }
},
// update/delete if you want them now
updateContractor: (id:string, p:Partial<{ org_name:string; contact_name:string; email:string; phone:string; billing_address:string; active:boolean }>) => patch(`/admin/contractors/${id}`, p),
deleteContractor: (id:string) => del(`/admin/contractors/${id}`),

// --- bin assignments (match backend) ---
listCurrentOwner: (qr: string) =>
  get(`/admin/bin-assignments/current?qr=${encodeURIComponent(qr)}`),

assignBin: (p: { qr: string; contractor_id: string }) =>
  post("/admin/bin-assignments/assign", p),

unassignBin: (p: { qr: string; contractor_id?: string }) =>
  post("/admin/bin-assignments/unassign", p),
};

// optional helper you added is fine to keep:
export type SkipCreateIn = { qr:string; color:string; size:string; notes?:string };
export async function adminCreateSkip(p: SkipCreateIn) {
  try {
    // map `qr` -> `qr_code` for the backend seed schema
    return await post("/skips/skips/_seed", {
      qr_code: p.qr,
      color: p.color,
      size: p.size,
      notes: p.notes ?? undefined,
    }, {
      headers: { "X-API-Key": getConfig().adminKey || "" },
    });
  } catch (e: any) {
    // fallback to dev helper if the admin seed is locked down
    if ([401, 403, 404, 405].includes(e?.response?.status)) {
      return await post(
        "/driver/dev/ensure-skip",
        { qr_code: p.qr, qr: p.qr },
        { headers: { "X-API-Key": getConfig().adminKey || getConfig().apiKey || "" } }
      );
    }
    throw parseApiError(e);
  }
}

export type Contractor = {
  id: string;
  org_name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  billing_address?: string;
  active?: boolean;
};

export type Json = any;
export function pretty(x:Json){ try{return JSON.stringify(x,null,2)}catch{return String(x)} }
