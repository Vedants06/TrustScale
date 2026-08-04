"use client";

import { useState } from "react";
import { NodeGrid } from "@/components/NodeGrid";
import { ActionPanel } from "@/components/ActionPanel";
import { ActivityLog } from "@/components/ActivityLog";
import { SystemStatusBanner } from "@/components/SystemStatusBanner";
import { NodeDetailModal } from "@/components/NodeDetailModal";
import { TrafficFlow } from "@/components/TrafficFlow";
import { useNodes } from "@/lib/hooks/useNodes";
import { useTrustHistory } from "@/lib/hooks/useTrustHistory";
import type { NodeTrustDetails } from "@/lib/types";

export default function DashboardPage() {
  const { nodes, loading, error } = useNodes();
  const history = useTrustHistory(nodes);
  const [selectedNode, setSelectedNode] = useState<NodeTrustDetails | null>(
    null,
  );
  const [trafficTrigger, setTrafficTrigger] = useState(0);

  const handleTrafficSent = () => {
    setTrafficTrigger((prev) => prev + 1);
  };

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-[1600px] space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">TrustScale</h1>
            <p className="text-sm text-muted-foreground">
              Byzantine-aware distributed load balancer
            </p>
          </div>
        </header>

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <p className="text-sm text-destructive">Error: {error}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Make sure the backend is running at http://localhost:8000
            </p>
          </div>
        )}

        {loading && (
          <div className="rounded-lg border border-border bg-card p-8 text-center">
            <p className="text-muted-foreground">Loading nodes...</p>
          </div>
        )}

        {!loading && !error && (
          <>
            <SystemStatusBanner nodes={nodes} />

            <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
              <div className="relative space-y-6">
                <div className="relative">
                  <NodeGrid
                    nodes={nodes}
                    history={history}
                    onNodeClick={setSelectedNode}
                  />
                  <TrafficFlow nodes={nodes} triggerCount={trafficTrigger} />
                </div>
              </div>

              <div className="space-y-6">
                <ActionPanel nodes={nodes} onTrafficSent={handleTrafficSent} />
                <div className="h-[400px]">
                  <ActivityLog />
                </div>
              </div>
            </div>
          </>
        )}

        <NodeDetailModal
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      </div>
    </main>
  );
}