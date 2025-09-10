// path: frontend/src/components/Scanner.tsx
import React, { useCallback, useRef, useState, useEffect } from 'react';
import { Scanner as LibScanner } from '@yudiel/react-qr-scanner';
import { Camera, ClipboardPaste, Pause, Play, RefreshCcw } from 'lucide-react';

export default function Scanner({
  onScan,
}: {
  onScan: (text: string) => void;
}) {
  const [enabled, setEnabled] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [manual, setManual] = useState('');

  // debounced duplicate frame filter
  const lastTextRef = useRef<string>('');
  const lastTsRef = useRef<number>(0);

  const handleResult = useCallback((raw: string | undefined) => {
    if (!raw) return;
    const now = Date.now();
    if (raw === lastTextRef.current && now - lastTsRef.current < 1500) return;
    lastTextRef.current = raw;
    lastTsRef.current = now;
    onScan(raw);
  }, [onScan]);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setManual(text);
        handleResult(text);
      }
    } catch {
      setErr('Clipboard is unavailable');
    }
  };

  const handleSubmitManual = (e: React.FormEvent) => {
    e.preventDefault();
    if (manual.trim()) handleResult(manual.trim());
  };

  // Optional: remember camera toggle
  useEffect(() => { try { localStorage.setItem('scan:cam', String(enabled)); } catch {} }, [enabled]);
  useEffect(() => {
    try { const v = localStorage.getItem('scan:cam'); if (v !== null) setEnabled(v === 'true'); } catch {}
  }, []);

  // If your editor still complains about props because the old type is cached,
  // this cast silences it while the uninstall settles:
  const AnyScanner = LibScanner as unknown as React.FC<any>;

  return (
    <div className="rounded-2xl border bg-white shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-slate-50">
        <div className="flex items-center gap-2"><Camera className="w-4 h-4"/> Scanner</div>
        <div className="flex items-center gap-2">
          <button className="btn btn-ghost" title={enabled ? 'Pause' : 'Start'} onClick={() => setEnabled(v => !v)}>
            {enabled ? <Pause className="w-4 h-4"/> : <Play className="w-4 h-4"/>}
          </button>
          <button className="btn btn-ghost" title="Reset last" onClick={() => (lastTextRef.current = '', lastTsRef.current = 0)}>
            <RefreshCcw className="w-4 h-4"/>
          </button>
        </div>
      </div>

      <div className="p-3">
        <div className="aspect-video rounded-xl overflow-hidden bg-black/5">
          {enabled && (
            <AnyScanner
              onResult={(text: string | { rawValue?: string }) =>
                handleResult(typeof text === 'string' ? text : text?.rawValue)}
              onError={(e: any) => setErr(e?.message || 'Camera error')}
              styles={{ container: { width: '100%', height: '100%' } }}
            />
          )}
        </div>

        {err && <div className="mt-2 rounded-md bg-rose-50 text-rose-700 px-3 py-2 text-sm">{err}</div>}

        {/* Manual fallback */}
        <form onSubmit={handleSubmitManual} className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto_auto]">
          <input
            className="input"
            placeholder="Paste or type code / full URL"
            value={manual}
            onChange={(e) => setManual(e.target.value)}
          />
          <button type="button" className="btn" onClick={handlePaste} title="Paste from clipboard">
            <ClipboardPaste className="w-4 h-4 mr-1" /> Paste
          </button>
          <button className="btn" type="submit">Use</button>
        </form>
        <p className="text-xs text-slate-500 mt-1">
          Tip: you can scan a QR or paste a full deep link like <code>/driver/qr/SK-1234</code>.
        </p>
      </div>
    </div>
  );
}
