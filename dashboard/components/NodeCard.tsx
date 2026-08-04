"use client";

import type { NodeTrustDetails } from "@/lib/types";

interface NodeCardProps {
  node: NodeTrustDetails;
  onClick?: () => void;
}

export function NodeCard({ node, onClick }: NodeCardProps) {
  const trust = node.trust_score ?? 0;
  const isQuarantined = node.quarantine.is_quarantined;

  const trustColor =
    trust >= 0.85
      ? "text-emerald-500"
      : trust >= 0.5
        ? "text-blue-500"
        : trust >= 0.3
          ? "text-amber-500"
          : "text-red-500";

  const borderClass = isQuarantined
    ? "border-red-500/50"
    : trust < 0.5
      ? "border-amber-500/50"
      : "border-border";

  return (
    <button
      onClick={onClick}
      className={`group rounded-lg border ${borderClass} bg-card p-6 text-left transition-all hover:border-primary/50 hover:bg-card/80 ${
        isQuarantined ? "opacity-50" : ""
      }`}
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-foreground">{node.node_id}</h3>
        {isQuarantined && (
          <span className="rounded bg-red-500/20 px-2 py-0.5 text-xs font-medium text-red-400">
            QUARANTINED
          </span>
        )}
      </div>

      <div className={`text-4xl font-bold ${trustColor}`}>{trust.toFixed(2)}</div>

      <div className="mt-2 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Trust Score</span>
        {node.cross_validation && node.cross_validation.observed_count > 0 && (
          <span className="text-muted-foreground">
            {node.cross_validation.observed_count} req
          </span>
        )}
      </div>

      {node.quarantine.quarantine_count > 0 && (
        <div className="mt-3 border-t border-border pt-2 text-xs text-muted-foreground">
          Quarantined {node.quarantine.quarantine_count}x
        </div>
      )}
    </button>
  );
}