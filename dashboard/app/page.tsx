"use client";

import { useNodes } from "@/lib/hooks/useNodes";

export default function DashboardPage() {
  const { nodes, loading, error } = useNodes();

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">TrustScale</h1>
            <p className="text-sm text-muted-foreground">
              Byzantine-aware distributed load balancer
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
            Live
          </div>
        </header>

        {loading && (
          <div className="rounded-lg border border-border bg-card p-8 text-center">
            <p className="text-muted-foreground">Loading nodes...</p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <p className="text-sm text-destructive">Error: {error}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Make sure the backend is running at http://localhost:8000
            </p>
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
            {nodes.map((node) => {
              const trust = node.trust_score ?? 0;
              const trustColor =
                trust >= 0.85
                  ? "text-emerald-500"
                  : trust >= 0.5
                    ? "text-blue-500"
                    : trust >= 0.3
                      ? "text-amber-500"
                      : "text-red-500";

              return (
                <div
                  key={node.node_id}
                  className={`rounded-lg border border-border bg-card p-6 transition-all ${
                    node.quarantine.is_quarantined
                      ? "border-red-500/50 opacity-50"
                      : ""
                  }`}
                >
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="font-semibold">{node.node_id}</h3>
                    {node.quarantine.is_quarantined && (
                      <span className="rounded bg-red-500/20 px-2 py-0.5 text-xs text-red-400">
                        QUARANTINED
                      </span>
                    )}
                  </div>
                  <div className={`text-4xl font-bold ${trustColor}`}>
                    {trust.toFixed(2)}
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    Trust Score
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <footer className="pt-8 text-center text-xs text-muted-foreground">
          {nodes.length} nodes tracked • Polling every 2 seconds
        </footer>
      </div>
    </main>
  );
}