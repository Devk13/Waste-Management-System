// path: frontend/src/components/SearchSelect.tsx
import React, { useEffect, useMemo, useState } from 'react'
import type { Option } from './types'

type Props = {
  placeholder?: string
  value: Option | null
  onChange: (v: Option | null) => void
  loadOptions: (q: string) => Promise<Option[]>
  allowClear?: boolean
}

export default function SearchSelect({ placeholder, value, onChange, loadOptions, allowClear }: Props) {
  const [q, setQ] = useState('')
  const [opts, setOpts] = useState<Option[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let alive = true
    ;(async () => {
      setLoading(true)
      try {
        const rows = await loadOptions(q)
        if (alive) setOpts(rows)
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => { alive = false }
  }, [q, loadOptions])

  const display = useMemo(() => (value ? value.label : ''), [value])

  return (
    <div className="relative">
      <div className="flex gap-2">
        <input
          className="input w-full"
          placeholder={placeholder}
          value={open ? q : display}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => { setOpen(true); setQ('') }}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
        {allowClear && value && (
          <button className="btn btn-ghost" onMouseDown={(e) => e.preventDefault()} onClick={() => onChange(null)}>
            ✕
          </button>
        )}
      </div>

      {open && (
        <div className="absolute z-10 mt-1 w-full max-h-56 overflow-auto rounded border bg-white shadow">
          {loading && <div className="px-3 py-2 text-sm text-slate-500">Loading…</div>}
          {!loading && opts.length === 0 && <div className="px-3 py-2 text-sm text-slate-500">No results</div>}
          {!loading && opts.map(o => (
            <button
              key={o.id}
              className="block w-full text-left px-3 py-2 hover:bg-slate-50"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => { onChange(o); setOpen(false) }}
            >
              <div className="text-sm">{o.label}</div>
              {o.sublabel && <div className="text-xs text-slate-500">{o.sublabel}</div>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
