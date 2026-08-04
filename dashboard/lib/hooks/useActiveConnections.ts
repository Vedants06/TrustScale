"use client";

import { useEffect, useRef, useState } from "react";
import type { NodeTrustDetails } from "../types";

const HIGHLIGHT_DURATION_MS = 1500;

export function useActiveConnections(nodes: NodeTrustDetails[]) {
  const [activeUntil, setActiveUntil] = useState<Record<string, number>>({});
  const lastCounts = useRef<Record<string, number>>({});

  useEffect(() => {
    if (nodes.length === 0) return;

    const now = Date.now();
    const updates: Record<string, number> = {};
    let hasChanges = false;

    for (const node of nodes) {
      const currentCount = node.cross_validation?.observed_count ?? 0;
      const previousCount = lastCounts.current[node.node_id];

      if (previousCount !== undefined && currentCount > previousCount) {
        updates[node.node_id] = now + HIGHLIGHT_DURATION_MS;
        hasChanges = true;
      }

      lastCounts.current[node.node_id] = currentCount;
    }

    if (hasChanges) {
      setActiveUntil((prev) => ({ ...prev, ...updates }));
    }
  }, [nodes]);

  // Cleanup expired highlights
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setActiveUntil((prev) => {
        const next: Record<string, number> = {};
        let changed = false;

        for (const [nodeId, expiry] of Object.entries(prev)) {
          if (expiry > now) {
            next[nodeId] = expiry;
          } else {
            changed = true;
          }
        }

        return changed ? next : prev;
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  const activeNodeIds = new Set(Object.keys(activeUntil));
  return activeNodeIds;
}