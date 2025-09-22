// path: frontend/src/api.ts
import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

/** Shared config shape used by the app. */
export type ApiConfig = { base: string; apiKey?: string; adminKey?: string };

// ---- helpers ---------------------------------------------------------------
function readJSON<T>(k: string): T | null {
  try {
    const raw = localStorage.getItem(k);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

/** Canonical, null-safe config loader (old store -> new store fallback). */
export function getConfig(): ApiConfig {
  // 1) Legacy store used by older panels
  const oldCfg = readJSON<any>("wm_console_cfg");
  if (oldCfg && typeof oldCfg === "object") {
    return {
      base: typeof oldCfg.base === "string" ? oldCfg.base : String(oldCfg.base ?? ""),
      apiKey: typeof oldCfg.apiKey === "string" ? oldCfg.apiKey : "",
      adminKey: typeof oldCfg.adminKey === "string" ? oldCfg.adminKey : "",
    };
  }
  // 2) New store used by Jobs/MyTasks
  const dev = readJSON<any>("wm_dev_console_cfg") || {};
  const baseUrl = typeof dev.baseUrl === "string" ? dev.baseUrl : String(dev.baseUrl ?? "");
  return {
    base: String(baseUrl || "").replace(/\/+$/, ""), // strip trailing slashes; safe on empty
    apiKey: typeof dev.driverKey === "string" ? dev.driverKey : "",
    adminKey: typeof dev.adminKey === "string" ? dev.adminKey : "",
  };
}

/** Save to BOTH stores (keeps driverId if present). */
export function setConfig(next: ApiConfig) {
  const base = String(next.base || "").replace(/\/+$/, "");
  const legacy = { base, apiKey: next.apiKey || "", adminKey: next.adminKey || "" };
  localStorage.setItem("wm_console_cfg", JSON.stringify(legacy));

  const devPrev = readJSON<any>("wm_dev_console_cfg") || {};
  const devNext = {
    baseUrl: base,
    driverKey: next.apiKey || "",
    adminKey: next.adminKey || "",
    driverId: typeof devPrev.driverId === "string" ? devPrev.driverId : "",
  };
  localStorage.setItem("wm_dev_console_cfg", JSON.stringify(devNext));

  // Rebuild axios instance with the new base/keys
  client = createClient(getConfig());
}

// ---- axios client (safe base handling) -------------------------------------
function createClient(c: ApiConfig): AxiosInstance {
  const safeBase = String(c.base || "").replace(/\/+$/, ""); // never throws
  const inst = axios.create({ baseURL: safeBase, timeout: 20000 });

  inst.interceptors.request.use((req) => {
    const url = (req.url || "").toLowerCase();
    const h: Record<string, string> = (req.headers as any) || {};
    const needsDriverKey = url.startsWith("/driver") || url.includes("/ensure-skip");
    const needsAdminKey =
      url.startsWith("/admin") || url.startsWith("/skips/_seed") || url.startsWith("/__debug") || url.startsWith("/_debug");
    if (needsDriverKey && c.apiKey) h["X-API-Key"] = c.apiKey!;
    if (needsAdminKey && c.adminKey) h["X-API-Key"] = c.adminKey!;
    req.headers = h as any;
    return req;
  });

  return inst;
}

// Initialize safely using the robust loader (no top-level .replace)
let client: AxiosInstance = createClient(getConfig());

// ---- tiny http helpers -----------------------------------------------------
async function get<T = any>(url: string, config?: AxiosRequestConfig) {
  return (await client.get<T>(url, config)).data;
}
async function post<T = any>(url: string, body?: any, config?: AxiosRequestConfig) {
  return (await client.post<T>(url, body ?? {}, config)).data;
}
async function patch<T = any>(url: string, body?: any) {
  return (await client.patch<T>(url, body ?? {})).data;
}
async function del<T = any>(url: string) {
  return (await client.delete<T>(url)).data;
}

// ---- API surface -----------------------------------------------------------
export type FieldErrors = Record<string, string>;
export class ApiError extends Error {
  code: number;
  fields?: FieldErrors;
  constructor(message: string, code: number, fields?: FieldErrors) {
    super(message);
    this.code = code;
    this.fields = fields;
  }
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
    if (txt.includes("reg")) fields = { reg_no: "Registration already exists" };
    if (txt.includes("name")) fields = { name: "Driver with this name already exists" };
    message = "Duplicate value";
  }
  return new ApiError(message, code, fields);
}

export const api = {
  // meta/debug
  health: () => get("/_meta/ping"),
  routes: () => get("/__debug/routes"),
  mounts: () => get("/__debug/mounts"),
  skipsSmoke: () => get("/skips/__smoke"),
  bootstrap: () =>
    post("/__admin/bootstrap", {}, { headers: { "X-API-Key": getConfig().adminKey || "" } }),
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

    const colors = raw?.skip?.colors ?? raw?.colors ?? raw?.SKIP_COLOR_SPEC ?? {};
    const sizesSrc =
      raw?.skip?.sizes ??
      raw?.sizes ?? {
        sizes_m3: raw?.SKIP_SIZES_M3 ?? raw?.SKIP_SIZES ?? undefined,
        wheelie_l: raw?.WHEELIE_LITRES ?? undefined,
        rolloff_yd: raw?.ROLLOFF_YARDS ?? undefined,
      };
    const toStrArr = (v: unknown) => (Array.isArray(v) ? v.map((x) => (x == null ? "" : String(x))) : []);
    const sizes = Object.fromEntries(Object.entries(sizesSrc).map(([k, v]) => [k, toStrArr(v)]));
    return { skip: { colors, sizes } };
  },

  // driver flow
  ensureSkipDev: async (qr: string) => {
    try { return await post("/driver/dev/ensure-skip", { qr_code: qr, qr }); }
    catch (e: any) {
      if (e?.response?.status === 422) return await get(`/driver/dev/ensure-skip?qr=${encodeURIComponent(qr)}`);
      throw parseApiError(e);
    }
  },
  scan: async (qr: string) => {
    try { return await get(`/driver/scan?qr=${encodeURIComponent(qr)}`); }
    catch (e: any) {
      if ([400, 422].includes(e?.response?.status)) return await get(`/driver/scan?q=${encodeURIComponent(qr)}`);
      throw parseApiError(e);
    }
  },
  deliverEmpty: (p: { skip_qr: string; to_zone_id: string; driver_name: string; vehicle_reg?: string }) =>
    post("/driver/deliver-empty", p).catch((e) => {
      throw parseApiError(e);
    }),
  relocateEmpty: (p: { skip_qr: string; from_zone_id?: string; to_zone_id: string; driver_name: string }) =>
    post("/driver/relocate-empty", p).catch((e) => {
      throw parseApiError(e);
    }),
  collectFull: (p: {
    skip_qr: string;
    destination_type: string;
    destination_name: string;
    weight_source: string;
    gross_kg?: number;
    tare_kg?: number;
    net_kg?: number;
    driver_name: string;
    site_id?: string;
    vehicle_reg?: string;
  }) =>
    post("/driver/collect-full", p).catch((e) => {
      throw parseApiError(e);
    }),
  returnEmpty: (p: { skip_qr: string; to_zone_id: string; driver_name: string }) =>
    post("/driver/return-empty", p).catch((e) => {
      throw parseApiError(e);
    }),

  // admin masters
  listDrivers: () => get("/admin/drivers"),
  createDriver: (p: { name: string; phone?: string; email?: string; license_no?: string; active?: boolean }) =>
    post("/admin/drivers", p).catch((e) => {
      throw parseApiError(e);
    }),
  updateDriver: (id: string, p: Partial<{ name: string; phone: string; email: string; license_no: string; active: boolean }>) =>
    patch(`/admin/drivers/${id}`, p).catch((e) => {
      throw parseApiError(e);
    }),
  deleteDriver: (id: string) => del(`/admin/drivers/${id}`).catch((e) => {
    throw parseApiError(e);
  }),

  listVehicles: () => get("/admin/vehicles"),
  createVehicle: (p: { reg_no: string; make?: string; model?: string; active?: boolean }) =>
    post("/admin/vehicles", p).catch((e) => {
      throw parseApiError(e);
    }),
  updateVehicle: (id: string, p: Partial<{ reg_no: string; make: string; model: string; active: boolean }>) =>
    patch(`/admin/vehicles/${id}`, p).catch((e) => {
      throw parseApiError(e);
    }),
  deleteVehicle: (id: string) => del(`/admin/vehicles/${id}`).catch((e) => {
    throw parseApiError(e);
  }),

  // contractors
  listContractors: () => get("/admin/contractors"),
  createContractor: (p: {
    org_name: string;
    contact_name?: string;
    email?: string;
    phone?: string;
    billing_address?: string;
    active?: boolean;
  }) => post("/admin/contractors", p).catch((e) => {
    throw parseApiError(e);
  }),
  updateContractor: (id: string, p: Partial<{ org_name: string; contact_name: string; email: string; phone: string; billing_address: string; active: boolean }>) =>
    patch(`/admin/contractors/${id}`, p),
  deleteContractor: (id: string) => del(`/admin/contractors/${id}`),

  // bin assignments
  listCurrentOwner: (qr: string) => get(`/admin/bin-assignments/current?qr=${encodeURIComponent(qr)}`),
  assignBin: (p: { qr: string; contractor_id: string }) => post("/admin/bin-assignments/assign", p),
  unassignBin: (p: { qr: string; contractor_id?: string }) => post("/admin/bin-assignments/unassign", p),

  // jobs & driver schedule
  listJobs: (status?: string) => get(status ? `/admin/jobs?status=${encodeURIComponent(status)}` : "/admin/jobs"),
  createJob: (p: any) => post("/admin/jobs", p),
  patchJob: (id: string, p: any) => patch(`/admin/jobs/${id}`, p),

  driverSchedule: (driverId: string) =>
    get(`/driver/schedule?driver_id=${encodeURIComponent(driverId)}&driver=${encodeURIComponent(driverId)}`),
  markTaskDone: (taskId: string) => patch(`/driver/schedule/${taskId}/done`, {}),
};

// also export the seed helper expected by SkipCreationForm.tsx
export type SkipCreateIn = {
  qr: string;
  color: string;
  size: number;                 // number of m³ from the UI
  notes?: string;
  owner_org_id?: string;        // resolved UUID (optional)
};

/** Admin seed helper used by the UI form. Falls back to the dev ensure endpoint if the admin seed is gated. */
export async function adminCreateSkip(p: SkipCreateIn) {
  try {
    // primary: admin seed endpoint
    return await post(
      "/skips/skips/_seed",
      {
        qr_code: p.qr,          // backend expects qr_code
        color: p.color,
        size_m3: Number(p.size),
        notes: p.notes ?? undefined,
        owner_org_id: p.owner_org_id ?? undefined,
      },
      { headers: { "X-API-Key": getConfig().adminKey || "" } }
    );
  } catch (e: any) {
    // fallback: dev helper (still requires some key)
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

// utilities
export type Json = any;
export function pretty(x: Json) {
  try {
    return JSON.stringify(x, null, 2);
  } catch {
    return String(x);
  }
}
