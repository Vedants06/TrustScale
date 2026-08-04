"use client";

import { useEffect, useRef, useState } from "react";
import type { NodeTrustDetails } from "../types";

export function useRequestRate(nodes: NodeTrustDetails[]) {
  const [rate, setRate] = useState(0);
  const [total, setTotal] = useState(0);
  const lastSnapshot = useRef<{ time: number; total: number } | null>(null);

  useEffect(() => {
    if (nodes.length === 0) return;

    const currentTotal = nodes.reduce(
      (sum, n) => sum + (n.cross_validation?.observed_count ?? 0),
      0,
    );

    setTotal(currentTotal);

    const now = Date.now();
    if (lastSnapshot.current) {
      const timeDiff = (now - lastSnapshot.current.time) / 1000;
      const totalDiff = currentTotal - lastSnapshot.current.total;

      if (timeDiff > 0) {
        const newRate = Math.max(0, totalDiff / timeDiff);
        setRate(newRate);
      }
    }

    lastSnapshot.current = { time: now, total: currentTotal };
  }, [nodes]);

  return { rate, total };
}