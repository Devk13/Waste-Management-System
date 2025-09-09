// path: frontend/src/components/Toast.tsx
import React, { createContext, useCallback, useContext, useMemo, useState } from 'react'

type ToastType = 'success' | 'error' | 'info'
interface ToastItem { id: number; type: ToastType; message: string }

interface ToastApi {
  success: (m: string) => void
  error: (m: string) => void
  info: (m: string) => void
}

const Ctx = createContext<{ push: (t: ToastItem) => void } | null>(null)
let seq = 1

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])

  const push = useCallback((t: ToastItem) => {
    setItems((prev) => [...prev, t])
    const ttl = 3500
    setTimeout(() => setItems((prev) => prev.filter((x) => x.id !== t.id)), ttl)
  }, [])

  const ctxVal = useMemo(() => ({ push }), [push])

  return (
    <Ctx.Provider value={ctxVal}>
      {children}
      <div className="pointer-events-none fixed left-1/2 top-3 z-[1000] w-full max-w-sm -translate-x-1/2 space-y-2 px-2">
        {items.map((t) => (
          <div key={t.id} className={`pointer-events-auto rounded-xl border bg-white px-3 py-2 text-sm shadow ${t.type==='success'?'border-emerald-300':'border-rose-300'}`}>
            <div className="flex items-start gap-2">
              <span className={`mt-0.5 h-2.5 w-2.5 rounded-full ${t.type==='success'?'bg-emerald-500':t.type==='error'?'bg-rose-500':'bg-slate-400'}`}></span>
              <div className="flex-1 text-slate-800">{t.message}</div>
              <button className="text-slate-400 hover:text-slate-600" onClick={() => setItems((prev) => prev.filter((x) => x.id !== t.id))}>×</button>
            </div>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  )
}

export function useToast(): ToastApi {
  const ctx = useContext(Ctx)
  if (!ctx) return { success: () => {}, error: () => {}, info: () => {} }
  return {
    success: (m: string) => ctx.push({ id: seq++, type: 'success', message: m }),
    error:   (m: string) => ctx.push({ id: seq++, type: 'error', message: m }),
    info:    (m: string) => ctx.push({ id: seq++, type: 'info', message: m }),
  }
}
