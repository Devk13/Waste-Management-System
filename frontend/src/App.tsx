// path: frontend/src/App.tsx
import React, { useEffect, useState } from 'react'
import Scanner from './components/Scanner'
import { apiScan, getConfig, setConfig, whoAmI, downloadLabelsPdf } from './api'
import type { ScanOut, Me } from './types'
import { Camera, Settings, Shield } from 'lucide-react'
import ActionCard from './components/ActionCard'

export default function App() {
  const [cfg, setCfg] = useState(getConfig())
  const [scanned, setScanned] = useState<string>('')
  const [info, setInfo] = useState<ScanOut | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'scan' | 'settings'>('scan')
  const [me, setMe] = useState<Me | null>(null)

  useEffect(() => { setConfig(cfg) }, [cfg])

  // Role-aware gating: fetch /auth/me when Base URL or token changes
  useEffect(() => {
    let alive = true
    ;(async () => {
      if (!cfg.token) { if (alive) setMe(null); return }
      const m = await whoAmI()
      if (alive) setMe(m)
    })()
    return () => { alive = false }
  }, [cfg.baseUrl, cfg.token])

  async function handleScan(text: string) {
    setScanned(text)
    setError(null)
    try {
      const data = await apiScan(text)
      setInfo(data)
    } catch (e: any) {
      setInfo(null)
      setError(e?.response?.data?.detail || e.message || 'Scan failed')
    }
  }

  function extractCode(): string {
    if (!scanned) return ''
    const m = scanned.match(/\/driver\/qr\/([^?\s#]+)/)
    return m ? m[1] : scanned
  }

  async function handleDownloadLabels(skipId: string, qrCode: string) {
    try {
      const blob = await downloadLabelsPdf(skipId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'skip-' + qrCode + '-labels.pdf'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || 'Download failed')
    }
  }

  return (
    <div className="max-w-xl mx-auto p-4 md:p-6">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">WMIS Driver</h1>
        <nav className="flex gap-2">
          <button className={`tab ${tab==='scan'?'tab-active':''}`} onClick={()=>setTab('scan')}>
            <Camera className="w-4 h-4"/> Scan
          </button>
          <button className={`tab ${tab==='settings'?'tab-active':''}`} onClick={()=>setTab('settings')}>
            <Settings className="w-4 h-4"/> Settings
          </button>
        </nav>
      </header>

      {tab === 'settings' && (
        <section className="rounded-2xl border bg-white p-4 shadow-sm space-y-3">
          <div className="text-sm text-slate-600 flex items-center gap-2">
            <Shield className="w-4 h-4"/> Configure your API
          </div>
          <label className="label">Base URL</label>
          <input className="input" value={cfg.baseUrl}
                 onChange={(e)=>setCfg({...cfg, baseUrl:e.target.value})}
                 placeholder="http://localhost:8000" />
          <label className="label">Bearer Token</label>
          <input className="input" value={cfg.token}
                 onChange={(e)=>setCfg({...cfg, token:e.target.value})}
                 placeholder="paste JWT token" />
          <p className="text-xs text-slate-500">
            Sign in to the admin UI, copy your JWT, and paste it here. Stored locally.
          </p>
        </section>
      )}

      {tab === 'scan' && (
        <section className="space-y-4">
          <Scanner onScan={handleScan} />
          {scanned && (
            <div className="rounded-2xl border bg-white p-3 shadow-sm text-sm">
              Scanned: <code className="text-slate-700">{extractCode()}</code>
            </div>
          )}
          {error && <div className="rounded-2xl bg-rose-50 text-rose-700 p-3 text-sm">{error}</div>}

          {info && (
            <div className="rounded-2xl border bg-white p-4 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-slate-500">Owner</div>
                  <div className="font-semibold">{info.owner_org_name}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-500">Skip</div>
                  <div className="font-mono">{info.qr_code}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <div className="text-xs text-slate-500">Commodity</div>
                  <div>{info.assigned_commodity_name || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">Zone</div>
                  <div>{info.zone_name || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">Status</div>
                  <div className="capitalize">{info.status.replace('_',' ')}</div>
                </div>
              </div>

              <ActionCard qr={info.qr_code} zoneId={info.zone_id} />

              {/* Admin-only labels download */}
              {me?.role === 'admin' && info.skip_id && (
                <div className="flex justify-end mt-2">
                  <button className="btn" onClick={() => handleDownloadLabels(info.skip_id, info.qr_code)}>
                    Download labels.pdf
                  </button>
                </div>
              )}
              {me && me.role !== 'admin' && (
                <p className="text-xs text-slate-500 text-right">Login as admin to access labels.</p>
              )}
            </div>
          )}
        </section>
      )}

      <footer className="text-center text-xs text-slate-400 mt-6">v0.1 • works offline (shell)</footer>
    </div>
  )
}
