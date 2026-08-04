"use client";

import { NodeGrid } from "@/components/NodeGrid";
import { ActionPanel } from "@/components/ActionPanel";
import { ActivityLog } from "@/components/ActivityLog";
import { SystemStatusBanner } from "@/components/SystemStatusBanner";
import { useNodes } from "@/lib/hooks/useNodes";

export default function DashboardPage() {
  const { nodes, loading, error } = useNodes();

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
              <div className="space-y-6">
                <NodeGrid nodes={nodes} />
              </div>

              <div className="space-y-6">
                <ActionPanel nodes={nodes} />
                <div className="h-[400px]">
                  <ActivityLog />
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}