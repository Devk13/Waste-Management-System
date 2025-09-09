// path: frontend/src/types.ts
export type SkipStatus = 'in_stock' | 'deployed' | 'in_transit' | 'processing'

export interface ScanOut {
  skip_id: string
  qr_code: string
  status: SkipStatus
  assigned_commodity_id?: string | null
  assigned_commodity_name?: string | null
  zone_id?: string | null
  zone_name?: string | null
  owner_org_id: string
  owner_org_name: string
}

export interface Zone { id: string; name: string; site_id?: string; site_name?: string }
export interface Facility { id: string; name: string; org_id?: string; org_name?: string }

// Add roles for admin-gated UI
export type UserRole = 'admin' | 'driver' | 'dispatcher' | 'user'
export interface Me { id: string; role: UserRole; org_id?: string }
