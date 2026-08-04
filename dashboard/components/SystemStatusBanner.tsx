"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { NodeTrustDetails, RoutingStrategy } from "@/lib/types";

interface SystemStatusBannerProps {
  nodes: NodeTrustDetails[];
}

export function SystemStatusBanner({ nodes }: SystemStatusBannerProps) {
  const [strategy, setStrategy] = useState<RoutingStrategy>("trust_aware");

  useEffect(() => {
    async function fetchStrategy() {
      try {
        const s = await api.getRoutingStrategy();
        setStrategy(s);
      } catch {
        // ignore
      }
    }
    fetchStrategy();
    const interval = setInterval(fetchStrategy, 5000);
    return () => clearInterval(interval);
  }, []);

  const activeNodes = nodes.filter((n) => !n.quarantine.is_quarantined).length;
  const quarantinedNodes = nodes.filter((n) => n.quarantine.is_quarantined).length;
  const totalNodes = nodes.length;

  const systemHealthy = quarantinedNodes === 0;
  const statusColor = systemHealthy ? "bg-emerald-500" : "bg-amber-500";
  const statusText = systemHealthy ? "SYSTEM HEALTHY" : "ATTACK DETECTED";

  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-card px-6 py-4">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-3 w-3 animate-pulse rounded-full ${statusColor}`}
          />
          <span className="font-semibold">{statusText}</span>
        </div>

        <div className="h-6 w-px bg-border" />

        <div className="text-sm">
          <span className="text-muted-foreground">Strategy: </span>
          <span className="font-mono font-medium">
            {strategy === "trust_aware" ? "Trust-Aware" : "Round-Robin"}
          </span>
        </div>

        <div className="h-6 w-px bg-border" />

        <div className="text-sm">
          <span className="text-muted-foreground">Nodes: </span>
          <span className="font-medium text-emerald-500">{activeNodes}</span>
          <span className="text-muted-foreground"> active</span>
          {quarantinedNodes > 0 && (
            <>
              <span className="text-muted-foreground"> · </span>
              <span className="font-medium text-red-500">{quarantinedNodes}</span>
              <span className="text-muted-foreground"> quarantined</span>
            </>
          )}
          <span className="text-muted-foreground"> / {totalNodes}</span>
        </div>
      </div>

      <div className="text-xs text-muted-foreground">Live · updates every 2s</div>
    </div>
  );
}