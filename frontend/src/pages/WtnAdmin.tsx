import React from "react";

type WtnItem = {
  id: string;
  number?: string | null;
  created_at?: string;
  quantity?: string;
  waste_type?: string;
  destination?: string;
  driver_name?: string;
  vehicle_reg?: string;
};

type ListResp = { items: WtnItem[]; page: number; page_size: number; total: number };

function apiBase(): string {
  // Why: allow VITE_API_BASE override, else same-origin
  const env = (import.meta as any).env;
  const base = env?.VITE_API_BASE as string | undefined;
  return base && base.length ? base.replace(/\/$/, "") : "";
}

export default function WtnAdmin() {
  const [q, setQ] = React.useState("");
  const [items, setItems] = React.useState<WtnItem[]>([]);
  const [page, setPage] = React.useState(1);
  const [pageSize] = React.useState(20);
  const [total, setTotal] = React.useState(0);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async (p = page, query = q) => {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${apiBase()}/wtn`, window.location.origin);
      if (query) url.searchParams.set("q", query);
      url.searchParams.set("page", String(p));
      url.searchParams.set("page_size", String(pageSize));
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ListResp = await res.json();
      setItems(data.items);
      setPage(data.page);
      setTotal(data.total);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [page, q, pageSize]);

  React.useEffect(() => { load(1); /* first load */ }, []);

  const pages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div style={{ maxWidth: 1100, margin: "24px auto", padding: "0 12px" }}>
      <h1 style={{ fontSize: 22, marginBottom: 12 }}>Waste Transfer Notes</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
        <input
          placeholder="Search by ID or number…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load(1, q)}
          style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #d1d5db", minWidth: 280 }}
        />
        <button
          onClick={() => load(1, q)}
          disabled={loading}
          style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #111827", background: "#111827", color: "white" }}
        >
          Search
        </button>
        <button
          onClick={() => { setQ(""); load(1, ""); }}
          disabled={loading}
          style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #e5e7eb", background: "white" }}
        >
          Clear
        </button>
        <div style={{ marginLeft: "auto", color: "#6b7280" }}>
          {loading ? "Loading…" : `Total: ${total}`}
        </div>
      </div>

      {error && (
        <div style={{ background: "#fee2e2", border: "1px solid #fecaca", color: "#991b1b", padding: 10, borderRadius: 8, marginBottom: 12 }}>
          {error}
        </div>
      )}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", background: "#f9fafb" }}>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>WTN # / ID</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Created</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Quantity</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Waste</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Destination</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Driver / Vehicle</th>
              <th style={{ padding: 10, borderBottom: "1px solid #e5e7eb" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && !loading && (
              <tr><td colSpan={7} style={{ padding: 16, color: "#6b7280" }}>No WTNs</td></tr>
            )}
            {items.map((it) => {
              const label = it.number || it.id;
              const base = apiBase() || "";
              const pdf = `${base}/wtn/${it.id}.pdf`;
              const html = `${base}/wtn/${it.id}/html`;
              return (
                <tr key={it.id}>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>
                    <div style={{ fontWeight: 600 }}>{label}</div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>{it.id}</div>
                  </td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>{it.created_at || "-"}</td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>{it.quantity || "-"}</td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>{it.waste_type || "-"}</td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>{it.destination || "-"}</td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>
                    {it.driver_name || "-"}
                    <div style={{ fontSize: 12, color: "#6b7280" }}>{it.vehicle_reg || ""}</div>
                  </td>
                  <td style={{ padding: 10, borderBottom: "1px solid #f3f4f6" }}>
                    <a href={pdf} target="_blank" rel="noreferrer" style={{ marginRight: 8 }}>PDF</a>
                    <a href={html} target="_blank" rel="noreferrer">HTML</a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 12, alignItems: "center" }}>
        <button
          onClick={() => load(Math.max(1, page - 1))}
          disabled={loading || page <= 1}
          style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid #d1d5db", background: "white" }}
        >
          Prev
        </button>
        <span style={{ color: "#6b7280" }}>Page {page} / {pages}</span>
        <button
          onClick={() => load(Math.min(pages, page + 1))}
          disabled={loading || page >= pages}
          style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid #d1d5db", background: "white" }}
        >
          Next
        </button>
        <button
          onClick={() => load(page)}
          disabled={loading}
          style={{ marginLeft: "auto", padding: "6px 10px", borderRadius: 8, border: "1px solid #111827", background: "#111827", color: "white" }}
        >
          Refresh
        </button>
      </div>
    </div>
  );
}
