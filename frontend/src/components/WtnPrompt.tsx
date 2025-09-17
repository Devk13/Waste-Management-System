import React from 'react';

type WtnEvt = { url: string; id?: string };

export default function WtnPrompt() {
  const [url, setUrl] = React.useState<string | null>(null);
  const [id, setId] = React.useState<string | undefined>(undefined);
  const [autoOpen, setAutoOpen] = React.useState<boolean>(() => {
    const v = localStorage.getItem('wtn:autoOpen');
    return v === null || v === '1';
  });

  React.useEffect(() => {
    const onReady = (e: Event) => {
      const detail = (e as CustomEvent<WtnEvt>).detail;
      if (detail?.url) {
        setUrl(detail.url);
        setId(detail.id);
      }
    };
    window.addEventListener('wtn:ready', onReady as EventListener);
    return () => window.removeEventListener('wtn:ready', onReady as EventListener);
  }, []);

  React.useEffect(() => {
    localStorage.setItem('wtn:autoOpen', autoOpen ? '1' : '0');
  }, [autoOpen]);

  if (!url) return null;

  return (
    <div
      style={{
        position: 'fixed',
        right: 16,
        bottom: 16,
        maxWidth: 420,
        zIndex: 50,
        boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
        borderRadius: 12,
        padding: 14,
        background: '#111827',
        color: 'white',
      }}
      role="status"
      aria-live="polite"
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>
        Waste Transfer Note {id ? `· ${id}` : ''}
      </div>
      <div style={{ opacity: 0.85, fontSize: 14, marginBottom: 10 }}>
        A WTN PDF is ready from the last <em>collect-full</em>.
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: '8px 12px',
            borderRadius: 8,
            background: 'white',
            color: '#111827',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          Open PDF
        </a>
        <button
          onClick={() => {
            navigator.clipboard?.writeText(url).catch(() => {});
          }}
          style={{
            padding: '8px 12px',
            borderRadius: 8,
            background: '#e5e7eb',
            color: '#111827',
            fontWeight: 600,
            border: 'none',
            cursor: 'pointer',
          }}
        >
          Copy Link
        </button>
        <label style={{ display: 'inline-flex', gap: 8, alignItems: 'center', fontSize: 13 }}>
          <input
            type="checkbox"
            checked={autoOpen}
            onChange={(e) => setAutoOpen(e.target.checked)}
          />
          Auto-open next time
        </label>
        <button
          onClick={() => setUrl(null)}
          style={{
            marginLeft: 'auto',
            padding: 6,
            borderRadius: 8,
            background: 'transparent',
            color: '#9ca3af',
            border: '1px solid #374151',
            cursor: 'pointer',
          }}
          aria-label="Dismiss WTN prompt"
          title="Dismiss"
        >
          ×
        </button>
      </div>
    </div>
  );
}
