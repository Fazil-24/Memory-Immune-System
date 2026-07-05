// In local dev, Vite's server.proxy (vite.config.js) forwards "/api/*" to the
// backend, so the relative path works with no env var needed. That proxy only
// exists in `vite dev` -- a production build (Vercel) is a static bundle with
// no proxy, so it needs the backend's real URL via VITE_API_URL instead.
const BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${path} failed: ${res.status} ${body}`);
  }
  return res.json();
}

export const api = {
  ingest: () => request("/ingest", { method: "POST" }),
  ask: (query, mode) =>
    request("/ask", { method: "POST", body: JSON.stringify({ query, mode }) }),
  scan: () => request("/scan", { method: "POST" }),
  repair: (source_ids, action) =>
    request("/repair", { method: "POST", body: JSON.stringify({ source_ids, action }) }),
  forget: (source_ids) =>
    request("/forget", { method: "POST", body: JSON.stringify({ source_ids }) }),
  graphState: () => request("/graph-state"),
};
