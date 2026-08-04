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
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      if (requestRate > 0) {
        setPulseKey((k) => k + 1);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [requestRate]);

  return (
    <div
      className="relative flex flex-col items-center justify-center"
      onMouseEnter={() => setShowInfo(true)}
      onMouseLeave={() => setShowInfo(false)}
    >
      {requestRate > 0 && (
        <div
          key={pulseKey}
          className="absolute inset-0 -m-6 animate-ping rounded-full bg-primary/20"
        />
      )}

      <div className="relative flex h-40 w-40 flex-col items-center justify-center rounded-full border-2 border-primary bg-card shadow-2xl shadow-primary/20 cursor-help">
        <Server className="h-10 w-10 text-primary" />
        <div className="mt-1 text-xs font-semibold uppercase tracking-wider text-primary">
          Load Balancer
        </div>
      </div>

      {showInfo && (
        <div className="absolute left-1/2 top-full mt-4 -translate-x-1/2 whitespace-nowrap rounded-lg border border-border bg-popover px-4 py-3 shadow-xl z-20 animate-in fade-in slide-in-from-top-1 duration-200">
          <div className="space-y-1.5 text-sm">
            <div className="flex items-center justify-between gap-6">
              <span className="text-muted-foreground">Total Requests</span>
              <span className="font-bold">{totalRequests.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between gap-6">
              <span className="text-muted-foreground">Rate</span>
              <span className="font-bold text-primary">
                {requestRate.toFixed(1)} req/s
              </span>
            </div>
            <div className="flex items-center justify-between gap-6">
              <span className="text-muted-foreground">Active Nodes</span>
              <span className="font-bold">
                {activeNodes}/{totalNodes}
              </span>
            </div>
          </div>
          <div className="absolute -top-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 border-l border-t border-border bg-popover" />
        </div>
      )}
    </div>
  );
}