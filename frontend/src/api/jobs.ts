/// path: frontend/src/api/jobs.ts

import { http } from "./http"
import { loadCfg } from "../lib/devConfig"

export type JobType = "DELIVER_EMPTY" | "RELOCATE_EMPTY" | "COLLECT_FULL" | "RETURN_EMPTY"
export type JobStatus = "PENDING" | "IN_PROGRESS" | "DONE" | "FAILED"

export type Job = {
  id: string
  type: JobType
  skip_qr?: string | null
  from_zone_id?: string | null
  to_zone_id?: string | null
  site_id?: string | null
  destination_type?: string | null
  destination_name?: string | null
  window_start?: string | null
  window_end?: string | null
  assigned_driver_id?: string | null
  assigned_vehicle_id?: string | null
  notes?: string | null
  status: JobStatus
  created_at: string
  updated_at: string
}

export async function listJobs(status?: JobStatus): Promise<Job[]> {
  const cfg = loadCfg()
  const q = status ? `?status=${status}` : ""
  return http<Job[]>(`${cfg.baseUrl}/admin/jobs${q}`, { apiKey: cfg.adminKey })
}
export async function createJob(payload: Partial<Job> & { type: JobType; status?: JobStatus }): Promise<Job> {
  const cfg = loadCfg()
  return http<Job>(`${cfg.baseUrl}/admin/jobs`, { method: "POST", body: JSON.stringify(payload), apiKey: cfg.adminKey })
}
export async function patchJob(id: string, payload: Partial<Job>): Promise<Job> {
  const cfg = loadCfg()
  return http<Job>(`${cfg.baseUrl}/admin/jobs/${id}`, { method: "PATCH", body: JSON.stringify(payload), apiKey: cfg.adminKey })
}
export async function driverSchedule(driverId: string): Promise<Job[]> {
  const cfg = loadCfg()
  return http<Job[]>(`${cfg.baseUrl}/driver/schedule?driver_id=${encodeURIComponent(driverId)}`, { apiKey: cfg.driverKey })
}
export async function markTaskDone(taskId: string): Promise<Job> {
  const cfg = loadCfg()
  return http<Job>(`${cfg.baseUrl}/driver/schedule/${taskId}/done`, { method: "PATCH", apiKey: cfg.driverKey })
}
