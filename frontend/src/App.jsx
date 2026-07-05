import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import IngestionPanel from "./components/IngestionPanel";
import ScanPanel from "./components/ScanPanel";
import RepairPanel from "./components/RepairPanel";
import ForgetPanel from "./components/ForgetPanel";
import QueryPanel from "./components/QueryPanel";
import MemoryGraph from "./components/MemoryGraph";

function useElementSize() {
  const ref = useRef(null);
  const [size, setSize] = useState({ width: 400, height: 420 });

  useEffect(() => {
    if (!ref.current) return;
    const el = ref.current;
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setSize({ width, height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return [ref, size];
}

const LEGEND = [
  { status: "CLEAN / VERIFIED", color: "bg-emerald-500" },
  { status: "SUSPECT", color: "bg-amber-500" },
  { status: "QUARANTINED", color: "bg-red-500" },
  { status: "DEPRECATED", color: "bg-slate-500" },
];

export default function App() {
  const [sources, setSources] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [graphRef, graphSize] = useElementSize();

  const refreshGraph = useCallback(async () => {
    try {
      const state = await api.graphState();
      setSources(state.sources);
      setEdges(state.edges);
    } catch (e) {
      console.error("graph-state refresh failed", e);
    }
  }, []);

  useEffect(() => {
    refreshGraph();
  }, [refreshGraph]);

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--color-panel-border)] px-6 py-4">
        <h1 className="text-lg font-semibold tracking-tight">
          Memory Immune System
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Detect, quarantine, repair, and forget conflicting memory — powered by Cognee.
        </p>
      </header>

      <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-4">
        <div className="space-y-4">
          <IngestionPanel onIngested={refreshGraph} />
          <ScanPanel sources={sources} onScanned={refreshGraph} />
          <RepairPanel sources={sources} onChanged={refreshGraph} />
          <ForgetPanel sources={sources} onChanged={refreshGraph} />
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-[var(--color-panel-border)] bg-[var(--color-panel)] p-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold tracking-wide text-slate-300">
                Live Memory Graph
              </h2>
              <div className="flex gap-3 text-[11px] text-slate-400">
                {LEGEND.map((l) => (
                  <span key={l.status} className="flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${l.color}`} />
                    {l.status}
                  </span>
                ))}
              </div>
            </div>
            <div ref={graphRef} className="h-[420px] rounded-lg bg-black/20">
              {sources.length > 0 && (
                <MemoryGraph
                  sources={sources}
                  edges={edges}
                  onNodeClick={setSelectedId}
                  selectedId={selectedId}
                  width={graphSize.width}
                  height={graphSize.height}
                />
              )}
              {sources.length === 0 && (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">
                  Load the demo corpus to populate the memory graph.
                </div>
              )}
            </div>
          </div>

          <QueryPanel />
        </div>
      </main>
    </div>
  );
}
