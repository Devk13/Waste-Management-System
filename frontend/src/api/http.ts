// path: frontend/src/api/http.ts

export async function http<T>(
  url: string,
  opts: RequestInit & { apiKey?: string } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string> || {}),
  }
  if (opts.apiKey) headers["X-API-Key"] = opts.apiKey
  const res = await fetch(url, { ...opts, headers })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`)
  }
  return res.json()
}
