"use client";

import { useEffect, useRef, useState } from "react";
import type { NodeTrustDetails } from "../types";

interface TrustPoint {
  timestamp: number;
  score: number;
}

const MAX_POINTS = 60;

export function useTrustHistory(nodes: NodeTrustDetails[]) {
  const [history, setHistory] = useState<Record<string, TrustPoint[]>>({});
  const lastUpdate = useRef<Record<string, number>>({});

  useEffect(() => {
    const now = Date.now();

    setHistory((prev) => {
      const next = { ...prev };

      for (const node of nodes) {
        if (node.trust_score === null) continue;

        const lastTs = lastUpdate.current[node.node_id] ?? 0;
        if (now - lastTs < 1500) continue;

        lastUpdate.current[node.node_id] = now;

        const existing = next[node.node_id] ?? [];
        const updated = [
          ...existing,
          { timestamp: now, score: node.trust_score },
        ].slice(-MAX_POINTS);

        next[node.node_id] = updated;
      }

      return next;
    });
  }, [nodes]);

  return history;
}