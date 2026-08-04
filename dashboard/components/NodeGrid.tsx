"use client";

import { NodeCard } from "./NodeCard";
import type { NodeTrustDetails } from "@/lib/types";

interface NodeGridProps {
  nodes: NodeTrustDetails[];
  onNodeClick?: (node: NodeTrustDetails) => void;
}

export function NodeGrid({ nodes, onNodeClick }: NodeGridProps) {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-4">
      {nodes.map((node) => (
        <NodeCard
          key={node.node_id}
          node={node}
          onClick={onNodeClick ? () => onNodeClick(node) : undefined}
        />
      ))}
    </div>
  );
}