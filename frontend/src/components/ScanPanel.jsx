import { useState } from "react";
import { api } from "../api";

export default function ScanPanel({ sources, onScanned }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const sourceTitle = (id) => sources.find((s) => s.source_id === id)?.title || id;

  const runScan = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.scan();
      setResult(res);
      onScanned?.(res);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-xl border border-[var(--color-panel-border)] bg-[var(--color-panel)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold tracking-wide text-slate-300">
          2 · Immune Scan Results
        </h2>
        <button
          onClick={runScan}
          disabled={busy}
          className="px-3 py-1.5 text-sm rounded-lg bg-amber-600/90 hover:bg-amber-500 disabled:opacity-50 transition"
        >
          {busy ? "Scanning…" : "Run Scan"}
        </button>
      </div>

      {error && <p className="text-xs text-red-400 mb-2">{error}</p>}

      {!result && !error && (
        <p className="text-xs text-slate-500">No scan run yet. Ingest the corpus, then run a scan to detect conflicting memory.</p>
      )}

      {result && (
        <div className="space-y-3">
          {result.authoritative_source && (
            <div className="text-xs text-emerald-300">
              Authoritative source: <span className="font-mono">{result.authoritative_source}</span>
            </div>
          )}
          <div>
            <p className="text-xs uppercase tracking-wide text-red-400 mb-1">Conflicts</p>
            <ul className="space-y-1.5">
              {result.conflicts.map((c, i) => (
                <li key={i} className="text-xs bg-red-950/30 border border-red-900/40 rounded-lg p-2">
                  <div className="font-mono text-red-300">
                    {c.source_a} <span className="text-slate-500">×</span> {c.source_b}
                  </div>
                  <div className="text-slate-400 mt-0.5">{c.reasoning}</div>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-emerald-400 mb-1">Supports</p>
            <ul className="space-y-1.5">
              {result.supports.map((s, i) => (
                <li key={i} className="text-xs bg-emerald-950/30 border border-emerald-900/40 rounded-lg p-2">
                  <div className="font-mono text-emerald-300">
                    {s.source_a} <span className="text-slate-500">↔</span> {s.source_b}
                  </div>
                  <div className="text-slate-400 mt-0.5">{s.reasoning}</div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
