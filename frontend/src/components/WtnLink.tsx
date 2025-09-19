// path: frontend/src/components/WtnLink.tsx
import React from "react";

type Props = {
  baseUrl: string;          // e.g. http://127.0.0.1:8000
  wtnPdfUrl: string;        // e.g. /wtn/<id>.pdf
  className?: string;
};

function joinUrl(base: string, path: string): string {
  const b = base.endsWith("/") ? base.slice(0, -1) : base;
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}

export const WtnLink: React.FC<Props> = ({ baseUrl, wtnPdfUrl, className }) => {
  const htmlUrl = `${joinUrl(baseUrl, wtnPdfUrl)}?format=html`;
  const pdfUrl  = `${joinUrl(baseUrl, wtnPdfUrl)}?format=pdf`;

  return (
    <div className={className ?? "flex items-center gap-2 mt-2"}>
      {/* why: let users preview quickly or grab a real PDF */}
      <a
        href={htmlUrl}
        target="_blank"
        rel="noreferrer"
        className="px-3 py-2 rounded-xl shadow hover:opacity-90 border border-slate-600"
      >
        Open WTN (HTML)
      </a>
      <a
        href={pdfUrl}
        target="_blank"
        rel="noreferrer"
        className="px-3 py-2 rounded-xl shadow hover:opacity-90 border border-slate-600"
      >
        Open PDF
      </a>
      <button
        onClick={() => navigator.clipboard.writeText(htmlUrl)}
        className="px-3 py-2 rounded-xl shadow hover:opacity-90 border border-slate-600"
      >
        Copy link
      </button>
    </div>
  );
};

// Helper to safely find wtn_pdf_url in any response object
export function findWtnUrl(resp: unknown): string | null {
  if (!resp || typeof resp !== "object") return null;
  const obj = resp as Record<string, unknown>;
  if (typeof obj.wtn_pdf_url === "string" && obj.wtn_pdf_url) return obj.wtn_pdf_url;

  // scan shallow arrays/objects (defensive)
  for (const v of Object.values(obj)) {
    if (typeof v === "string" && v.includes("/wtn/") && v.endsWith(".pdf")) return v;
    if (v && typeof v === "object") {
      const nested = findWtnUrl(v);
      if (nested) return nested;
    }
  }
  return null;
}
