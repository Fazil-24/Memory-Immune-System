import { useRef, useState } from "react";
import { api } from "../api";

const DEMO_FILES = [
  { source_id: "policy_data_retention_old", label: "policy_data_retention_old.txt" },
  { source_id: "policy_data_retention_current", label: "policy_data_retention_current.txt" },
  { source_id: "policy_data_retention_rogue", label: "policy_data_retention_rogue.txt" },
  { source_id: "slack_chat_1", label: "slack_chat_1.txt" },
  { source_id: "slack_chat_2", label: "slack_chat_2.txt" },
  { source_id: "meeting_retention_discussion", label: "meeting_retention_discussion.txt" },
];

const STAGES = ["Idle", "Ingesting", "Remembered", "Mapped to Graph"];
const POLL_MS = 1500;

export default function IngestionPanel({ onIngested }) {
  const [stageIdx, setStageIdx] = useState(DEMO_FILES.map(() => 0));
  const [doneCount, setDoneCount] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  const setAll = (idx) => setStageIdx(DEMO_FILES.map(() => idx));

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const runIngest = async () => {
    setBusy(true);
    setError(null);
    setAll(1);
    setDoneCount(0);

    pollRef.current = setInterval(async () => {
      try {
        const state = await api.graphState();
        const remembered = new Set(state.sources.map((s) => s.source_id));
        setStageIdx((prev) => DEMO_FILES.map((f, i) => (remembered.has(f.source_id) ? 2 : prev[i])));
        // never let the bar jump backward, even across the mid-ingest reset
        setDoneCount((prev) => Math.max(prev, remembered.size));
      } catch {
        // transient poll failure -- next tick will retry, nothing to show the user yet
      }
    }, POLL_MS);

    try {
      const result = await api.ingest();
      setAll(3);
      setDoneCount(DEMO_FILES.length);
      onIngested?.(result);
    } catch (e) {
      setError(String(e.message || e));
      setAll(0);
      setDoneCount(0);
    } finally {
      stopPolling();
      setBusy(false);
    }
  };

  const percent = Math.round((doneCount / DEMO_FILES.length) * 100);

  return (
    <div className="rounded-xl border border-[var(--color-panel-border)] bg-[var(--color-panel)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold tracking-wide text-slate-300">
          1 · Document Ingestion
        </h2>
        <button
          onClick={runIngest}
          disabled={busy}
          className="px-3 py-1.5 text-sm rounded-lg bg-emerald-600/90 hover:bg-emerald-500 disabled:opacity-50 transition"
        >
          {busy ? "Loading…" : "Load Demo Corpus"}
        </button>
      </div>

      {busy && (
        <div className="mb-3">
          <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-emerald-500 transition-all duration-500 ease-out"
              style={{ width: `${percent}%` }}
            />
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            {doneCount} / {DEMO_FILES.length} documents remembered
          </p>
        </div>
      )}

      <ul className="space-y-1.5">
        {DEMO_FILES.map((f, i) => (
          <li key={f.source_id} className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono">{f.label}</span>
            <span
              className={
                "px-2 py-0.5 rounded-full " +
                (stageIdx[i] === 3
                  ? "bg-emerald-900/60 text-emerald-300"
                  : stageIdx[i] === 2
                  ? "bg-sky-900/60 text-sky-300"
                  : stageIdx[i] === 1
                  ? "bg-amber-900/60 text-amber-300"
                  : "bg-slate-800 text-slate-500")
              }
            >
              {STAGES[stageIdx[i]]}
            </span>
          </li>
        ))}
      </ul>
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  );
}
