// path: frontend/src/components/ActionCard.tsx
import React, { useEffect, useState } from 'react'
import { Truck, Package2, Factory, ArrowLeftRight } from 'lucide-react'
import { collectFull, deliverEmpty, dropAtFacility, returnEmpty, searchFacilities, searchZones } from '../api'
import SearchSelect, { Option } from './SearchSelect'
import { useToast } from './Toast'

export default function ActionCard({ qr, zoneId }: { qr: string; zoneId?: string | null }) {
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const toast = useToast()

  async function run<T>(name: string, fn: () => Promise<T>) {
    setBusy(name)
    setMsg(null)
    try {
      const res = await fn()
      const ok = `${name} ✓`
      setMsg(ok)
      toast.success(ok)
      return res
    } catch (e: any) {
      const m = e?.response?.data?.detail || e.message || 'Error'
      setMsg(m)
      toast.error(m)
      throw e
    } finally {
      setBusy(null)
    }
  }

  // Pickers
  const [toZone, setToZone] = useState<Option | null>(null)
  const [fromZone, setFromZone] = useState<Option | null>(zoneId ? { id: zoneId, label: zoneId } : null)
  const [facility, setFacility] = useState<Option | null>(null)

  // Numeric inputs
  const [gross, setGross] = useState<number | ''>('')
  const [tare, setTare] = useState<number | ''>('')
  const [ticket, setTicket] = useState('')

  // Remember last used selections
  useEffect(() => {
    const lastZone = localStorage.getItem('last:zone')
    if (lastZone && !toZone) {
      try { const z = JSON.parse(lastZone) as Option; setToZone(z) } catch {}
    }
    const lastFac = localStorage.getItem('last:facility')
    if (lastFac && !facility) {
      try { const f = JSON.parse(lastFac) as Option; setFacility(f) } catch {}
    }
  }, [])

  function saveLast(key: 'zone' | 'facility', opt: Option | null) {
    if (!opt) return
    try { localStorage.setItem(`last:${key}`, JSON.stringify(opt)) } catch {}
  }

  // Loaders
  const loadZones = async (q: string) => (await searchZones(q)).map(z => ({ id: z.id, label: z.name, sublabel: z.site_name }))
  const loadFacilities = async (q: string) => (await searchFacilities(q)).map(f => ({ id: f.id, label: f.name, sublabel: f.org_name }))

  return (
    <div className="grid gap-4">
      {msg && <div className="text-sm text-center text-slate-700 bg-slate-100 rounded p-2">{msg}</div>}

      {/* Deliver Empty */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><Package2 /> <b>Deliver Empty</b></div>
        <div className="grid gap-2 sm:grid-cols-[1fr_auto] items-start">
          <SearchSelect placeholder="Select destination zone" value={toZone} onChange={setToZone} loadOptions={loadZones} />
          <button className="btn" disabled={!toZone || !!busy} onClick={() => run('Delivered', async () => {
            await deliverEmpty(qr, toZone!.id)
            saveLast('zone', toZone)
          })}>Deliver</button>
        </div>
      </div>

      {/* Collect Full */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><Truck /> <b>Collect Full</b></div>
        <div className="grid gap-2 sm:grid-cols-3 items-start">
          <SearchSelect placeholder="From zone (optional)" value={fromZone} onChange={setFromZone} loadOptions={loadZones} allowClear />
          <SearchSelect placeholder="Destination facility (optional)" value={facility} onChange={setFacility} loadOptions={loadFacilities} allowClear />
          <button className="btn" disabled={!!busy} onClick={() => run('Collected', async () => {
            await collectFull({ qr_code: qr, from_zone_id: fromZone?.id, destination_facility_id: facility?.id })
            if (fromZone) saveLast('zone', fromZone)
            if (facility) saveLast('facility', facility)
          })}>Collect</button>
        </div>
      </div>

      {/* Drop at Facility */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><Factory /> <b>Drop at Facility</b></div>
        <div className="grid gap-2 sm:grid-cols-4 items-start">
          <div className="sm:col-span-2">
            <SearchSelect placeholder="Facility" value={facility} onChange={(v)=>{ setFacility(v); if (v) saveLast('facility', v) }} loadOptions={loadFacilities} />
          </div>
          <input className="input" placeholder="Gross kg" inputMode="numeric" value={gross} onChange={(e) => setGross(e.target.value ? Number(e.target.value) : '')} />
          <input className="input" placeholder="Tare kg" inputMode="numeric" value={tare} onChange={(e) => setTare(e.target.value ? Number(e.target.value) : '')} />
        </div>
        <div className="grid gap-2 sm:grid-cols-2 mt-2">
          <input className="input" placeholder="Weigh Ticket # (optional)" value={ticket} onChange={(e) => setTicket(e.target.value)} />
          <div className="flex justify-end"><button className="btn" disabled={!facility || !!busy} onClick={() => run('Dropped', () => dropAtFacility({ qr_code: qr, facility_id: facility!.id, gross_kg: gross || undefined, tare_kg: tare || undefined, ticket_no: ticket || undefined }))}>Submit</button></div>
        </div>
      </div>

      {/* Return Empty */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><ArrowLeftRight /> <b>Return Empty</b></div>
        <div className="grid gap-2 sm:grid-cols-[1fr_auto] items-start">
          <SearchSelect placeholder="Select destination zone" value={toZone} onChange={(v)=>{ setToZone(v); if (v) saveLast('zone', v) }} loadOptions={loadZones} />
          <button className="btn" disabled={!toZone || !!busy} onClick={() => run('Returned', () => returnEmpty(qr, toZone!.id))}>Return</button>
        </div>
      </div>
    </div>
  )
}
