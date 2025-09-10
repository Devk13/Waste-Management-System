// path: frontend/src/components/ActionCard.tsx
import React, { useEffect, useState } from 'react'
import { Truck, Package2, Factory, ArrowLeftRight } from 'lucide-react'
import { collectFull, deliverEmpty, dropAtFacility, returnEmpty, searchFacilities, searchZones } from '../api'
import SearchSelect from './SearchSelect'
import { useToast } from './Toast'
import type { Option } from './types';

const [msg, setMsg] = useState<string | null>(null);
const [busy, setBusy] = useState<string | null>(null);

const [toZone, setToZone] = useState<Option | undefined>(undefined);
const [fromZone, setFromZone] = useState<Option | undefined>(undefined);
const [facility, setFacility] = useState<Option | undefined>(undefined);

/** Props the page passes into ActionCard */
type Props = {
  qr: string
  zoneId?: string | null
}

export default function ActionCard({ qr, zoneId }: Props) {
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const toast = useToast()

  // Pickers
  const [toZone, setToZone] = useState<Option | null>(null)
  const [fromZone, setFromZone] = useState<Option | null>(zoneId ? { id: zoneId, label: zoneId } : null)
  const [facility, setFacility] = useState<Option | null>(null)

  // Numeric inputs
  const [gross, setGross] = useState<number | ''>('')
  const [tare, setTare] = useState<number | ''>('')
  const [ticket, setTicket] = useState<string>('')

  // Remember last used selections
  useEffect(() => {
    try {
      const z = JSON.parse(localStorage.getItem('last:zone') || 'null') as Option | null
      if (z) setToZone(z)
    } catch {}
    try {
      const f = JSON.parse(localStorage.getItem('last:facility') || 'null') as Option | null
      if (f) setFacility(f)
    } catch {}
  }, [])

  // remember last selection
  function saveLast(key: 'zone' | 'facility', opt?: Option) {
    if (!opt) return;
    try { localStorage.setItem(`last:${key}`, JSON.stringify(opt)); } catch {}
  }

  // Data loaders for SearchSelect
  const loadZones = async (q: string): Promise<Option[]> =>
    (await searchZones(q)).map(z => ({ id: z.id, label: z.name, sublabel: z.site_name }))
  const loadFacilities = async (q: string): Promise<Option[]> =>
    (await searchFacilities(q)).map(f => ({ id: f.id, label: f.name, sublabel: f.org_name }))

  async function run(name: string, fn: () => Promise<unknown>) {
    try {
      setBusy(name)
      setMsg(null)
      await fn()
      toast.success('OK')
    } catch (e) {
      const m = (e as any)?.response?.data?.detail ?? (e as Error)?.message ?? 'Error'
      setMsg(String(m))
      toast.error(String(m))
      throw e
    } finally {
      setBusy(null)
    }
  }

  const numberOrEmpty = (v: string) => {
    if (v.trim() === '') return ''
    const n = Number(v)
    return Number.isNaN(n) ? '' : n
  }

  return (
    <div className="grid gap-4">
      {msg && (
        <div className="text-sm text-center text-slate-700 bg-slate-100 rounded p-2">{msg}</div>
      )}

      {/* Deliver Empty */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><Package2 /> <b>Deliver Empty</b></div>
        <div className="grid gap-2 sm:grid-cols-2">
          <SearchSelect
            placeholder="Destination zone"
            value={toZone}
            onChange={setToZone}
            loadOptions={loadZones}
            allowClear
          />
          <button className="btn" disabled={!toZone || !!busy} onClick={() =>
            run('Delivered', async () => deliverEmpty(qr, toZone!.id))
          }>
            Deliver
          </button>
        </div>
      </div>

      {/* Collect Full */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><Truck /> <b>Collect Full</b></div>
        <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
          <SearchSelect
            placeholder="From zone (optional)"
            value={fromZone}
            onChange={setFromZone}
            loadOptions={loadZones}
            allowClear
          />
          <button className="btn" disabled={!!busy} onClick={() =>
            run('Collected', async () => {
              await collectFull({
                qr_code: qr,
                from_zone_id: fromZone?.id ?? undefined,          // <- was ?? null
                destination_facility_id: facility?.id ?? undefined // <- was ?? null
              })
            })
          }>
            Collect
          </button>
        </div>
      </div>

      {/* Drop at Facility */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><Factory /> <b>Drop at Facility</b></div>
        <div className="grid gap-2 sm:grid-cols-4 items-start">
          <SearchSelect
            placeholder="Facility"
            value={facility}
            onChange={(v) => { setFacility(v); if (v) saveLast('facility', v) }}
            loadOptions={loadFacilities}
          />
          <input
            className="input"
            placeholder="Gross kg"
            inputMode="numeric"
            value={gross}
            onChange={(e) => setGross(numberOrEmpty(e.target.value))}
          />
          <input
            className="input"
            placeholder="Tare kg"
            inputMode="numeric"
            value={tare}
            onChange={(e) => setTare(numberOrEmpty(e.target.value))}
          />
          <div className="flex justify-end">
            <button
              className="btn"
              disabled={!facility || !!busy}
              onClick={() =>
                run('Dropped', async () =>
                  dropAtFacility({
                    qr_code: qr,
                    facility_id: facility!.id,
                    gross_kg: gross === '' ? undefined : Number(gross),
                    tare_kg: tare === '' ? undefined : Number(tare),
                    ticket_no: ticket || undefined,
                  })
                )
              }
            >
              Submit
            </button>
          </div>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 mt-2">
          <input
            className="input"
            placeholder="Weigh Ticket # (optional)"
            value={ticket}
            onChange={(e) => setTicket(e.target.value)}
          />
        </div>
      </div>

      {/* Return Empty */}
      <div className="p-4 rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center gap-2 mb-2"><ArrowLeftRight /> <b>Return Empty</b></div>
        <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
          <SearchSelect
            placeholder="Select destination zone"
            value={toZone}
            onChange={(v) => { setToZone(v); if (v) saveLast('zone', v) }}
            loadOptions={loadZones}
          />
          <button className="btn" disabled={!toZone || !!busy} onClick={() =>
            run('Returned', async () => returnEmpty(qr, toZone!.id))
          }>
            Return
          </button>
        </div>
      </div>
    </div>
  )
}
