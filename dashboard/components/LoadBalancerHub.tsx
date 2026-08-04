"use client";

import { useEffect, useState } from "react";
import { Server } from "lucide-react";

interface LoadBalancerHubProps {
  totalRequests: number;
  requestRate: number;
  activeNodes: number;
  totalNodes: number;
}

export function LoadBalancerHub({
  totalRequests,
  requestRate,
  activeNodes,
  totalNodes,
}: LoadBalancerHubProps) {
  const [pulseKey, setPulseKey] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      if (requestRate > 0) {
        setPulseKey((k) => k + 1);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [requestRate]);

  return (
    <div className="relative flex flex-col items-center justify-center">
      {requestRate > 0 && (
        <div
          key={pulseKey}
          className="absolute inset-0 -m-6 animate-ping rounded-full bg-primary/20"
        />
      )}

      <div className="relative flex h-40 w-40 flex-col items-center justify-center rounded-full border-2 border-primary bg-card shadow-2xl shadow-primary/20">
        <Server className="h-10 w-10 text-primary" />
        <div className="mt-1 text-xs font-semibold uppercase tracking-wider text-primary">
          Load Balancer
        </div>
      </div>

      <div className="mt-4 space-y-1 text-center">
        <div className="text-2xl font-bold">{totalRequests.toLocaleString()}</div>
        <div className="text-xs uppercase text-muted-foreground">
          Total Requests
        </div>
        <div className="mt-2 flex items-center justify-center gap-3 text-sm">
          <div>
            <span className="font-semibold text-primary">
              {requestRate.toFixed(1)}
            </span>
            <span className="ml-1 text-muted-foreground">req/s</span>
          </div>
          <div className="text-muted-foreground">·</div>
          <div>
            <span className="font-semibold">
              {activeNodes}/{totalNodes}
            </span>
            <span className="ml-1 text-muted-foreground">active</span>
          </div>
        </div>
      </div>
    </div>
  );
}