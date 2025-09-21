// path: frontend/src/components/driver/MyTasksPanel.tsx

import { useEffect, useState } from "react"
import { driverSchedule, markTaskDone, Job } from "../../api/jobs"
import { loadCfg } from "../../lib/devConfig"

export default function MyTasksPanel() {
  const cfg = loadCfg()
  const [tasks, setTasks] = useState<Job[]>([])
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const refresh = async () => {
    if (!cfg.driverId) { setErr("Missing Driver Id in Config"); return }
    setLoading(true); setErr(null)
    try { setTasks(await driverSchedule(cfg.driverId)) } catch (e:any) { setErr(e.message) } finally { setLoading(false) }
  }
  useEffect(() => { refresh() }, [])

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Driver · My Tasks</h3>
        <button className="border rounded p-2" onClick={refresh} disabled={loading}>Refresh</button>
      </div>
      {err && <div className="text-red-600 text-sm">{err}</div>}
      <div className="space-y-2">
        {tasks.map(t => (
          <div key={t.id} className="border rounded p-3">
            <div className="text-sm font-medium">{t.type} · {t.skip_qr || "—"}</div>
            <div className="text-xs opacity-70">
              Window: {t.window_start?.slice(0,16) || "—"} → {t.window_end?.slice(0,16) || "—"}
            </div>
            <div className="text-xs">From {t.from_zone_id||"—"} → {t.to_zone_id||"—"} · Site {t.site_id||"—"}</div>
            <div className="text-xs">Status: {t.status}</div>
            <div className="mt-2 flex gap-2">
              <button className="text-xs border rounded px-2 py-1" onClick={() => markTaskDone(t.id).then(refresh)}>Mark Done</button>
            </div>
          </div>
        ))}
        {tasks.length === 0 && <div className="text-xs opacity-60">No assigned tasks.</div>}
      </div>
    </div>
  )
}
