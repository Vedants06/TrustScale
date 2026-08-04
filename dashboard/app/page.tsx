"use client";

import { useState } from "react";
import { TopologyView } from "@/components/TopologyView";
import { ActionsBar } from "@/components/ActionsBar";
import { SystemStatusBanner } from "@/components/SystemStatusBanner";
import { NodeDetailModal } from "@/components/NodeDetailModal";
import {
  ActivityDrawer,
  ActivityDrawerToggle,
} from "@/components/ActivityDrawer";
import { useNodes } from "@/lib/hooks/useNodes";
import { useRequestRate } from "@/lib/hooks/useRequestRate";
import type { NodeTrustDetails } from "@/lib/types";

export default function DashboardPage() {
  const { nodes, loading, error } = useNodes();
  const { rate, total } = useRequestRate(nodes);
  const [selectedNode, setSelectedNode] = useState<NodeTrustDetails | null>(
    null,
  );
  const [logOpen, setLogOpen] = useState(false);

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
          <ActivityDrawerToggle onClick={() => setLogOpen(true)} />
        </header>

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <p className="text-sm text-destructive">Error: {error}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Make sure backend is running at http://localhost:8000
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

            <div className="rounded-lg border border-border bg-card p-8">
              <TopologyView
                nodes={nodes}
                requestRate={rate}
                totalRequests={total}
                onNodeClick={setSelectedNode}
              />
            </div>

            <ActionsBar nodes={nodes} />
          </>
        )}

        <NodeDetailModal
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />

        <ActivityDrawer open={logOpen} onClose={() => setLogOpen(false)} />
      </div>
    </main>
  );
}