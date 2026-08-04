"use client";

import { NodeCard } from "./NodeCard";
import type { NodeTrustDetails } from "@/lib/types";

interface TrustPoint {
  timestamp: number;
  score: number;
}

interface NodeGridProps {
  nodes: NodeTrustDetails[];
  history: Record<string, TrustPoint[]>;
  onNodeClick?: (node: NodeTrustDetails) => void;
}

export function NodeGrid({ nodes, history, onNodeClick }: NodeGridProps) {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
      {nodes.map((node) => (
        <NodeCard
          key={node.node_id}
          node={node}
          history={history[node.node_id] ?? []}
          onClick={onNodeClick ? () => onNodeClick(node) : undefined}
        />
      ))}
    </div>
  );
}