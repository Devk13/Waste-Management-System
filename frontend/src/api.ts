// path: frontend/src/api.ts
import axios from 'axios'
import type { ScanOut, Zone, Facility, Me } from './types'

export type Config = { baseUrl: string; token: string }

export function getConfig(): Config {
  const baseUrl = localStorage.getItem('baseUrl') || 'http://localhost:8000'
  const token = localStorage.getItem('token') || ''
  return { baseUrl, token }
}

export function setConfig(cfg: Partial<Config>) {
  const cur = getConfig()
  const next = { ...cur, ...cfg }
  localStorage.setItem('baseUrl', next.baseUrl)
  localStorage.setItem('token', next.token)
}

function client() {
  const { baseUrl, token } = getConfig()
  const inst = axios.create({ baseURL: baseUrl })
  if (token) inst.defaults.headers.common['Authorization'] = `Bearer ${token}`
  return inst
}

// Why: many list endpoints might return either an array or an {items: []} wrapper.
function unwrap<T>(data: any): T[] {
  return Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : [])
}

export async function searchZones(q?: string, site_id?: string): Promise<Zone[]> {
  try {
    const { data } = await client().get('/zones', { params: { q, site_id, limit: 50 } })
    return unwrap<Zone>(data)
  } catch {
    return []
  }
}

export async function searchFacilities(q?: string): Promise<Facility[]> {
  try {
    const { data } = await client().get('/facilities', { params: { q, limit: 50 } })
    return unwrap<Facility>(data)
  } catch {
    return []
  }
}

export async function apiScan(qr: string): Promise<ScanOut> {
  // Accept full deep link or raw code
  const match = qr.match(/\/driver\/qr\/([^?\s#]+)/)
  const code = match ? match[1] : qr
  const { data } = await client().get(`/driver/qr/${encodeURIComponent(code)}`)
  return data
}

export async function deliverEmpty(qr_code: string, to_zone_id: string, notes?: string) {
  const { data } = await client().post('/driver/deliver-empty', { qr_code, to_zone_id, notes })
  return data
}

export async function collectFull(params: { qr_code: string; from_zone_id?: string; destination_facility_id?: string; notes?: string }) {
  const { data } = await client().post('/driver/collect-full', params)
  return data
}

export async function dropAtFacility(params: { qr_code: string; facility_id: string; gross_kg?: number; tare_kg?: number; ticket_no?: string; notes?: string }) {
  const { data } = await client().post('/driver/drop-at-facility', params)
  return data
}

export async function returnEmpty(qr_code: string, to_zone_id: string, notes?: string) {
  const { data } = await client().post('/driver/return-empty', { qr_code, to_zone_id, notes })
  return data
}

// Admin helpers
export async function whoAmI(): Promise<Me | null> {
  try {
    const { data } = await client().get('/auth/me')
    return data as Me
  } catch {
    return null
  }
}

export async function downloadLabelsPdf(skip_id: string): Promise<Blob> {
  const { data } = await client().get(`/skips/${encodeURIComponent(skip_id)}/labels.pdf`, { responseType: 'blob' })
  return data as Blob
}
