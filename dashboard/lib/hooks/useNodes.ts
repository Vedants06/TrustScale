"use client";

import { useEffect, useState } from "react";
import { api } from "../api";
import type { NodeTrustDetails } from "../types";

export function useNodes(pollingInterval = 2000) {
  const [nodes, setNodes] = useState<NodeTrustDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        const nodeIds = await api.listNodes();
        const trustPromises = nodeIds.map((id) => api.getNodeTrust(id));
        const trustData = await Promise.all(trustPromises);

        if (!cancelled) {
          setNodes(trustData);
          setLoading(false);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
          setLoading(false);
        }
      }
    }

    fetchData();
    const interval = setInterval(fetchData, pollingInterval);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [pollingInterval]);

  return { nodes, loading, error };
}