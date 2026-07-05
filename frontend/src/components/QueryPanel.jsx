import { useState } from "react";
import { api } from "../api";

const DEMO_QUERY = "What is the current rule for EU customer data retention?";

const STATUS_DOT = {
  CLEAN: "bg-slate-400",
  VERIFIED: "bg-emerald-400",
  SUSPECT: "bg-amber-400",
  QUARANTINED: "bg-red-400",
  DEPRECATED: "bg-slate-600",
};

export default function QueryPanel() {
  const [query, setQuery] = useState(DEMO_QUERY);
  const [mode, setMode] = useState("after");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const ask = async (nextMode = mode) => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.ask(query, nextMode);
      setResult(res);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const toggleMode = (m) => {
    setMode(m);
    ask(m);
  };

  return (
    <div className="rounded-xl border border-[var(--color-panel-border)] bg-[var(--color-panel)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold tracking-wide text-slate-300">5 · Agent Query</h2>
        <div className="flex rounded-lg overflow-hidden border border-[var(--color-panel-border)] text-xs">
          <button
            onClick={() => toggleMode("before")}
            className={`px-3 py-1 transition ${mode === "before" ? "bg-red-700/70 text-white" : "bg-transparent text-slate-400 hover:text-slate-200"}`}
          >
            Before
          </button>
          <button
            onClick={() => toggleMode("after")}
            className={`px-3 py-1 transition ${mode === "after" ? "bg-emerald-700/70 text-white" : "bg-transparent text-slate-400 hover:text-slate-200"}`}
          >
            After
          </button>
        </div>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask();
        }}
        className="flex gap-2 mb-3"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 bg-black/30 border border-[var(--color-panel-border)] rounded-lg px-3 py-2 text-sm outline-none focus:border-sky-600"
          placeholder="Ask the agent…"
        />
        <button
          type="submit"
          disabled={busy}
          className="px-3 py-2 text-sm rounded-lg bg-sky-700/80 hover:bg-sky-600 disabled:opacity-50 transition"
        >
          {busy ? "…" : "Ask"}
        </button>
      </form>

      {error && <p className="text-xs text-red-400 mb-2">{error}</p>}

      {result && (
        <div className="space-y-3">
          <div
            className={
              "text-sm rounded-lg p-3 border " +
              (mode === "before"
                ? "border-red-900/50 bg-red-950/20"
                : "border-emerald-900/50 bg-emerald-950/20")
            }
          >
            {result.answer}
          </div>
          <div className="flex flex-wrap gap-2">
            {result.used_sources.map((s) => (
              <span
                key={s.source_id}
                title={`status: ${s.status} · confidence: ${((s.confidence ?? 0) * 100).toFixed(0)}%`}
                className="flex items-center gap-1.5 text-xs font-mono px-2 py-1 rounded-full bg-black/30 border border-[var(--color-panel-border)] cursor-help"
              >
                <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[s.status] || "bg-slate-400"}`} />
                {s.source_id}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
