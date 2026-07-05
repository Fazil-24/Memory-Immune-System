import { useState } from "react";
import { api } from "../api";

const STATUS_BADGE = {
  CLEAN: "bg-slate-800 text-slate-400",
  SUSPECT: "bg-amber-900/60 text-amber-300",
  QUARANTINED: "bg-red-950/60 text-red-300",
  VERIFIED: "bg-emerald-900/60 text-emerald-300",
  DEPRECATED: "bg-slate-800 text-slate-500 line-through",
};

export default function RepairPanel({ sources, onChanged }) {
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState(null);

  const flagged = sources.filter((s) => s.status === "SUSPECT" || s.status === "QUARANTINED" || s.status === "VERIFIED");

  const act = async (source_id, action) => {
    setBusyId(source_id);
    setError(null);
    try {
      await api.repair([source_id], action);
      onChanged?.();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="rounded-xl border border-[var(--color-panel-border)] bg-[var(--color-panel)] p-4">
      <h2 className="text-sm font-semibold tracking-wide text-slate-300 mb-3">
        3 · Repair &amp; Quarantine
      </h2>
      {error && <p className="text-xs text-red-400 mb-2">{error}</p>}
      {flagged.length === 0 ? (
        <p className="text-xs text-slate-500">No flagged sources yet. Run a scan first.</p>
      ) : (
        <ul className="space-y-2">
          {flagged.map((s) => (
            <li key={s.source_id} className="flex items-center justify-between gap-2 text-xs">
              <div className="min-w-0">
                <div className="font-mono truncate">{s.source_id}</div>
                <span className={`inline-block mt-0.5 px-2 py-0.5 rounded-full ${STATUS_BADGE[s.status]}`}>
                  {s.status} · {(s.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex gap-1 shrink-0">
                <button
                  onClick={() => act(s.source_id, "quarantine")}
                  disabled={busyId === s.source_id || s.status === "QUARANTINED"}
                  className="px-2 py-1 rounded-md bg-red-700/80 hover:bg-red-600 disabled:opacity-40 transition"
                >
                  Quarantine
                </button>
                <button
                  onClick={() => act(s.source_id, "verify")}
                  disabled={busyId === s.source_id || s.status === "VERIFIED"}
                  className="px-2 py-1 rounded-md bg-emerald-700/80 hover:bg-emerald-600 disabled:opacity-40 transition"
                >
                  Verify
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
