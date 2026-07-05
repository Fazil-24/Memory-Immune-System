import { useMemo, useRef, useEffect } from "react";
import ForceGraph2D from "react-force-graph-2d";

const STATUS_COLOR = {
  CLEAN: "#22c55e",
  VERIFIED: "#22c55e",
  SUSPECT: "#eab308",
  QUARANTINED: "#ef4444",
  DEPRECATED: "#6b7280",
};

export default function MemoryGraph({ sources, edges, onNodeClick, selectedId, width, height }) {
  const fgRef = useRef();

  const graphData = useMemo(() => {
    const ids = new Set(sources.map((s) => s.source_id));
    return {
      nodes: sources.map((s) => ({
        id: s.source_id,
        status: s.status,
        confidence: s.confidence,
        title: s.title,
      })),
      links: edges
        .filter((e) => ids.has(e.source_a) && ids.has(e.source_b))
        .map((e) => ({
          source: e.source_a,
          target: e.source_b,
          relation: e.relation,
          reasoning: e.reasoning,
        })),
    };
  }, [sources, edges]);

  useEffect(() => {
    fgRef.current?.d3Force("charge")?.strength(-200);
  }, [graphData]);

  return (
    <ForceGraph2D
      ref={fgRef}
      width={width}
      height={height}
      graphData={graphData}
      backgroundColor="rgba(0,0,0,0)"
      nodeRelSize={6}
      linkColor={(l) => (l.relation === "CONTRADICTS" ? "rgba(239,68,68,0.7)" : "rgba(34,197,94,0.55)")}
      linkWidth={(l) => (l.relation === "CONTRADICTS" ? 2 : 1)}
      linkDirectionalParticles={(l) => (l.relation === "CONTRADICTS" ? 2 : 0)}
      linkDirectionalParticleWidth={3}
      linkDirectionalParticleColor={() => "#ef4444"}
      linkLabel={(l) => `${l.relation}${l.reasoning ? ": " + l.reasoning : ""}`}
      onNodeClick={(node) => onNodeClick?.(node.id)}
      nodeCanvasObject={(node, ctx, globalScale) => {
        const color = STATUS_COLOR[node.status] || "#38bdf8";
        const radius = 6 + (node.confidence ?? 0.5) * 5;

        ctx.save();
        if (node.status === "QUARANTINED") {
          const pulse = 0.6 + 0.4 * Math.sin(Date.now() / 220);
          ctx.shadowColor = color;
          ctx.shadowBlur = 20 * pulse;
        } else if (node.status === "DEPRECATED") {
          ctx.globalAlpha = 0.25;
        } else {
          ctx.shadowColor = color;
          ctx.shadowBlur = 10;
        }
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();
        if (node.id === selectedId) {
          ctx.lineWidth = 2;
          ctx.strokeStyle = "#ffffff";
          ctx.stroke();
        }
        ctx.restore();

        const fontSize = 10 / globalScale;
        ctx.font = `${fontSize}px sans-serif`;
        ctx.fillStyle = "#cbd5e1";
        ctx.textAlign = "center";
        ctx.fillText(node.id, node.x, node.y + radius + fontSize);
      }}
    />
  );
}
