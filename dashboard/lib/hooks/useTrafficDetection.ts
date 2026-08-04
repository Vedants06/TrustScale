"use client";

import { useEffect, useRef, useState } from "react";
import type { NodeTrustDetails } from "../types";

interface TrafficEvent {
  id: string;
  nodeId: string;
  timestamp: number;
}

export function useTrafficDetection(nodes: NodeTrustDetails[]) {
  const [events, setEvents] = useState<TrafficEvent[]>([]);
  const lastCounts = useRef<Record<string, number>>({});

  useEffect(() => {
    if (nodes.length === 0) return;

    const newEvents: TrafficEvent[] = [];

    for (const node of nodes) {
      const currentCount = node.cross_validation?.observed_count ?? 0;
      const previousCount = lastCounts.current[node.node_id];

      if (previousCount !== undefined && currentCount > previousCount) {
        const diff = currentCount - previousCount;
        const particleCount = Math.min(diff, 5);

        for (let i = 0; i < particleCount; i++) {
          newEvents.push({
            id: `${Date.now()}-${node.node_id}-${i}-${Math.random()}`,
            nodeId: node.node_id,
            timestamp: Date.now() + i * 100,
          });
        }
      }

      lastCounts.current[node.node_id] = currentCount;
    }

    if (newEvents.length > 0) {
      setEvents((prev) => [...prev, ...newEvents]);

      const timer = setTimeout(() => {
        setEvents((prev) =>
          prev.filter((e) => !newEvents.some((ne) => ne.id === e.id)),
        );
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [nodes]);

  return events;
}