// path: frontend/src/components/admin/JobsCard.tsx
// ======================================================================
import { useEffect, useMemo, useState } from "react"
import { createJob, listJobs, patchJob, Job, JobType, JobStatus } from "../../api/jobs"
import { loadCfg } from "../../lib/devConfig"

const TYPES: JobType[] = ["DELIVER_EMPTY", "RELOCATE_EMPTY", "COLLECT_FULL", "RETURN_EMPTY"]
const STATUS_COLS: JobStatus[] = ["PENDING", "IN_PROGRESS", "DONE"]

function useJobsBoard() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const refresh = async () => {
    setLoading(true); setErr(null)
    try { setJobs(await listJobs(undefined)) } catch (e:any) { setErr(e.message) } finally { setLoading(false) }
  }
  useEffect(() => { refresh() }, [])
  return { jobs, refresh, loading, err }
}

export default function JobsCard() {
  const cfg = loadCfg()
  const { jobs, refresh, loading, err } = useJobsBoard()
  const [form, setForm] = useState<Partial<Job>>({ type: "DELIVER_EMPTY" as JobType })

  const columns = useMemo(() => {
    const by: Record<JobStatus, Job[]> = { PENDING:[], IN_PROGRESS:[], DONE:[], FAILED:[] }
    for (const j of jobs) by[j.status].push(j)
    return by
  }, [jobs])

  const set = (k: keyof Job, v: any) => setForm(prev => ({ ...prev, [k]: v }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    await createJob({
      type: form.type as JobType,
      skip_qr: form.skip_qr ?? undefined,
      from_zone_id: form.from_zone_id ?? undefined,
      to_zone_id: form.to_zone_id ?? undefined,
      site_id: form.site_id ?? undefined,
      destination_type: form.destination_type ?? undefined,
      destination_name: form.destination_name ?? undefined,
      window_start: form.window_start ?? undefined,
      window_end: form.window_end ?? undefined,
      assigned_driver_id: form.assigned_driver_id ?? undefined,
      assigned_vehicle_id: form.assigned_vehicle_id ?? undefined,
      notes: form.notes ?? undefined,
      status: "PENDING",
    })
    setForm({ type: "DELIVER_EMPTY" })
    await refresh()
  }

  return (
    <div className="rounded-xl border p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Admin · Jobs</h3>
        <div className="text-xs opacity-70">Base: {cfg.baseUrl || "—"}</div>
      </div>

      <form onSubmit={submit} className="grid md:grid-cols-4 grid-cols-1 gap-2">
        <select className="border rounded p-2" value={form.type as string} onChange={e=>set("type", e.target.value)}>
          {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <input className="border rounded p-2" placeholder="skip_qr" value={form.skip_qr||""} onChange={e=>set("skip_qr", e.target.value)} />
        <input className="border rounded p-2" placeholder="from_zone_id" value={form.from_zone_id||""} onChange={e=>set("from_zone_id", e.target.value)} />
        <input className="border rounded p-2" placeholder="to_zone_id" value={form.to_zone_id||""} onChange={e=>set("to_zone_id", e.target.value)} />
        <input className="border rounded p-2" placeholder="site_id" value={form.site_id||""} onChange={e=>set("site_id", e.target.value)} />
        <input className="border rounded p-2" placeholder="destination_type" value={form.destination_type||""} onChange={e=>set("destination_type", e.target.value)} />
        <input className="border rounded p-2" placeholder="destination_name" value={form.destination_name||""} onChange={e=>set("destination_name", e.target.value)} />
        <input className="border rounded p-2" placeholder="window_start ISO" value={form.window_start as any||""} onChange={e=>set("window_start", e.target.value)} />
        <input className="border rounded p-2" placeholder="window_end ISO" value={form.window_end as any||""} onChange={e=>set("window_end", e.target.value)} />
        <input className="border rounded p-2" placeholder="assigned_driver_id" value={form.assigned_driver_id||""} onChange={e=>set("assigned_driver_id", e.target.value)} />
        <input className="border rounded p-2" placeholder="assigned_vehicle_id" value={form.assigned_vehicle_id||""} onChange={e=>set("assigned_vehicle_id", e.target.value)} />
        <input className="border rounded p-2 md:col-span-3" placeholder="notes" value={form.notes||""} onChange={e=>set("notes", e.target.value)} />
        <button className="bg-black text-white rounded p-2">Create Job</button>
      </form>

      <div className="flex items-center gap-2">
        <button className="border rounded p-2" onClick={refresh} disabled={loading}>Refresh</button>
        {err && <span className="text-red-600 text-sm">{err}</span>}
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {STATUS_COLS.map(col => (
          <div key={col} className="rounded-lg border p-3">
            <div className="font-semibold mb-2">{col}</div>
            <div className="space-y-2">
              {columns[col].map(j => (
                <div key={j.id} className="border rounded p-2">
                  <div className="text-sm font-medium">{j.type} · {j.skip_qr || "—"}</div>
                  <div className="text-xs opacity-70">{j.window_start?.slice(0,16)} → {j.window_end?.slice(0,16) || "—"}</div>
                  <div className="text-xs">Driver:{j.assigned_driver_id || "—"} · Veh:{j.assigned_vehicle_id || "—"}</div>
                  <div className="flex gap-2 mt-2">
                    <button className="text-xs border rounded px-2 py-1" onClick={() => patchJob(j.id, { status: col === "PENDING" ? "IN_PROGRESS" : col === "IN_PROGRESS" ? "DONE" : "PENDING" }).then(refresh)}>Advance</button>
                    <button className="text-xs border rounded px-2 py-1" onClick={() => patchJob(j.id, { assigned_driver_id: prompt("driver_id?", j.assigned_driver_id||"") || undefined }).then(refresh)}>Assign Driver</button>
                    <button className="text-xs border rounded px-2 py-1" onClick={() => patchJob(j.id, { assigned_vehicle_id: prompt("vehicle_id?", j.assigned_vehicle_id||"") || undefined }).then(refresh)}>Assign Vehicle</button>
                  </div>
                </div>
              ))}
              {columns[col].length === 0 && <div className="text-xs opacity-60">No jobs</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
