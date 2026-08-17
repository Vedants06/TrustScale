"use client";

import { useState } from "react";
import { Network, Ticket } from "lucide-react";
import { TopologyView } from "@/components/TopologyView";
import { ActionsBar } from "@/components/ActionsBar";
import { SystemStatusBanner } from "@/components/SystemStatusBanner";
import { NodeDetailModal } from "@/components/NodeDetailModal";
import { BookingDemo } from "@/components/BookingDemo";
import {
  ActivityDrawer,
  ActivityDrawerToggle,
} from "@/components/ActivityDrawer";
import { useNodes } from "@/lib/hooks/useNodes";
import { useRequestRate } from "@/lib/hooks/useRequestRate";
import type { NodeTrustDetails } from "@/lib/types";

type Tab = "topology" | "booking";

export default function DashboardPage() {
  const { nodes, loading, error } = useNodes();
  const { rate, total } = useRequestRate(nodes);
  const [selectedNode, setSelectedNode] = useState<NodeTrustDetails | null>(
    null,
  );
  const [logOpen, setLogOpen] = useState(false);
  const [trafficTrigger, setTrafficTrigger] = useState(0);
  const [activeTab, setActiveTab] = useState<Tab>("topology");

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

          <div className="flex items-center gap-4">
            <div className="flex rounded-lg border border-border bg-card p-1">
              <button
                onClick={() => setActiveTab("topology")}
                className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === "topology"
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Network className="h-4 w-4" />
                Topology
              </button>
              <button
                onClick={() => setActiveTab("booking")}
                className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === "booking"
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Ticket className="h-4 w-4" />
                Booking Demo
              </button>
            </div>

            <ActivityDrawerToggle onClick={() => setLogOpen(true)} />
          </div>
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

            {activeTab === "topology" && (
              <>
                <div className="rounded-lg border border-border bg-card p-8">
                  <TopologyView
                    nodes={nodes}
                    requestRate={rate}
                    totalRequests={total}
                    trafficTrigger={trafficTrigger}
                    onNodeClick={setSelectedNode}
                  />
                </div>

                <ActionsBar
                  nodes={nodes}
                  onTrafficSent={handleTrafficSent}
                />
              </>
            )}

            {activeTab === "booking" && <BookingDemo />}
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