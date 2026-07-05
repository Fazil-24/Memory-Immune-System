import { useState } from "react";
import { api } from "../api";

export default function ForgetPanel({ sources, onChanged }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [fading, setFading] = useState(new Set());

  const quarantined = sources.filter((s) => s.status === "QUARANTINED");
  const deprecated = sources.filter((s) => s.status === "DEPRECATED");

  const forgetAll = async () => {
    if (quarantined.length === 0) return;
    setBusy(true);
    setError(null);
    const ids = quarantined.map((s) => s.source_id);
    setFading(new Set(ids));
    try {
      await new Promise((r) => setTimeout(r, 500));
      await api.forget(ids);
      onChanged?.();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
      setFading(new Set());
    }
  };

  return (
    <div className="rounded-xl border border-[var(--color-panel-border)] bg-[var(--color-panel)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold tracking-wide text-slate-300">4 · Forget</h2>
        <button
          onClick={forgetAll}
          disabled={busy || quarantined.length === 0}
          className="px-3 py-1.5 text-sm rounded-lg bg-slate-600/90 hover:bg-slate-500 disabled:opacity-40 transition"
        >
          {busy ? "Forgetting…" : "Forget these memories"}
        </button>
      </div>

      {quarantined.length === 0 && deprecated.length === 0 && (
        <p className="text-xs text-slate-500">Nothing quarantined yet.</p>
      )}

      {quarantined.length > 0 && (
        <ul className="space-y-1.5 mb-2">
          {quarantined.map((s) => (
            <li
              key={s.source_id}
              className={
                "text-xs font-mono px-2 py-1 rounded-md bg-red-950/40 border border-red-900/40 pulse-quarantined " +
                (fading.has(s.source_id) ? "fade-deprecated" : "")
              }
            >
              {s.source_id}
            </li>
          ))}
        </ul>
      )}

      {deprecated.length > 0 && (
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">Deprecated (forgotten)</p>
          <ul className="space-y-1">
            {deprecated.map((s) => (
              <li key={s.source_id} className="text-xs font-mono text-slate-600 line-through">
                {s.source_id}
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  );
}
