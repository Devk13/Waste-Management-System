const ORIG_FETCH = window.fetch.bind(window);

function toAbsolute(url: string, base?: string): string {
  try {
    return new URL(url, base ?? window.location.origin).toString();
  } catch {
    return url;
  }
}

function shouldAutoOpen(): boolean {
  const v = localStorage.getItem('wtn:autoOpen');
  return v === null || v === '1';
}

window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const res = await ORIG_FETCH(input as any, init);
  try {
    const urlStr = typeof input === 'string' ? input : (input as URL).toString();
    if (urlStr.includes('/driver/collect-full')) {
      // Clone so we don't consume caller's body
      const clone = res.clone();
      const contentType = clone.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const data = await clone.json().catch(() => null);
        const wtnPath = data?.wtn_pdf_url as string | undefined;
        const wtnId = data?.wtn_id as string | undefined;
        if (wtnPath) {
          const base = (() => {
            try { return new URL(urlStr).origin; } catch { return undefined; }
          })();
          const abs = toAbsolute(wtnPath, base);
          // Notify UI listeners
          window.dispatchEvent(new CustomEvent('wtn:ready', { detail: { url: abs, id: wtnId } }));
          if (shouldAutoOpen()) {
            // Open in new tab; 'noopener' for safety
            window.open(abs, '_blank', 'noopener,noreferrer');
          }
        }
      }
    }
  } catch { /* non-fatal */ }
  return res;
};

export {}; // module-scope
