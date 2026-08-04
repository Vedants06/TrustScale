"use client";

import type { NodeTrustDetails } from "@/lib/types";

interface NodeOrbitProps {
  node: NodeTrustDetails;
  x: number;
  y: number;
  onClick?: () => void;
}

export function NodeOrbit({ node, x, y, onClick }: NodeOrbitProps) {
  const trust = node.trust_score ?? 0;
  const isQuarantined = node.quarantine.is_quarantined;
  const nodeNumber = node.node_id.replace("node_", "");

  const trustColor =
    trust >= 0.85
      ? "text-emerald-500"
      : trust >= 0.5
        ? "text-blue-500"
        : trust >= 0.3
          ? "text-amber-500"
          : "text-red-500";

  const borderColor =
    trust >= 0.85
      ? "border-emerald-500"
      : trust >= 0.5
        ? "border-blue-500"
        : trust >= 0.3
          ? "border-amber-500 animate-pulse"
          : "border-red-500";

  const bgColor =
    trust >= 0.85
      ? "bg-emerald-500/10"
      : trust >= 0.5
        ? "bg-blue-500/10"
        : trust >= 0.3
          ? "bg-amber-500/10"
          : "bg-red-500/10";

  return (
    <button
      onClick={onClick}
      className="absolute flex flex-col items-center transition-transform hover:scale-110"
      style={{
        left: `${x}px`,
        top: `${y}px`,
        transform: "translate(-50%, -50%)",
      }}
    >
      <div
        data-node-id={node.node_id}
        className={`relative flex h-20 w-20 items-center justify-center rounded-full border-2 ${borderColor} ${bgColor} shadow-lg transition-all ${
          isQuarantined ? "opacity-40" : ""
        }`}
      >
        <span className={`text-3xl font-bold ${trustColor}`}>{nodeNumber}</span>

        {isQuarantined && (
          <div className="absolute -top-2 -right-2 h-6 w-6 rounded-full border-2 border-background bg-red-500 text-xs font-bold text-white flex items-center justify-center">
            ×
          </div>
        )}
      </div>

      <div className="mt-2 text-center">
        <div className={`text-sm font-semibold ${trustColor}`}>
          {trust.toFixed(2)}
        </div>
        <div className="text-xs text-muted-foreground">node {nodeNumber}</div>
      </div>
    </button>
  );
}