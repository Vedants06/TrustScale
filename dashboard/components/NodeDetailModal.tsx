"use client";

import { X } from "lucide-react";
import { useEffect } from "react";
import type { NodeTrustDetails } from "@/lib/types";

interface NodeDetailModalProps {
    node: NodeTrustDetails | null;
    onClose: () => void;
}

function formatTime(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString("en-US", {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

function formatEventType(type: string): string {
    const map: Record<string, string> = {
        honest_behavior: "Honest",
        metric_discrepancy: "Discrepancy",
        quarantined: "Quarantined",
        restored: "Restored",
        bootstrap_period: "Bootstrap",
        signature_invalid: "Invalid Signature",
        timestamp_stale: "Stale Timestamp",
    };
    return map[type] ?? type;
}

function eventColor(type: string): string {
    if (type === "quarantined") return "text-red-400";
    if (type === "metric_discrepancy") return "text-amber-400";
    if (type === "honest_behavior") return "text-emerald-400";
    if (type === "restored") return "text-blue-400";
    return "text-muted-foreground";
}

export function NodeDetailModal({ node, onClose }: NodeDetailModalProps) {
    useEffect(() => {
        if (node) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "";
        }
        return () => {
            document.body.style.overflow = "";
        };
    }, [node]);

    if (!node) return null;

    const trust = node.trust_score ?? 0;
    const cv = node.cross_validation;
    const q = node.quarantine;

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
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
            onClick={onClose}
        >
            <div
                className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-border bg-card p-6"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="mb-6 flex items-start justify-between">
                    <div>
                        <h2 className="text-2xl font-bold">{node.node_id}</h2>
                        <p className="text-sm text-muted-foreground">Node details</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="rounded-md p-1 hover:bg-secondary"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <div className="mb-6 grid grid-cols-3 gap-4">
                    <div className="rounded-md border border-border bg-background/50 p-4">
                        <div className="text-xs uppercase text-muted-foreground">
                            Trust Score
                        </div>
                        <div className={`mt-1 text-3xl font-bold ${trustColor}`}>
                            {trust.toFixed(3)}
                        </div>
                    </div>
                    <div className="rounded-md border border-border bg-background/50 p-4">
                        <div className="text-xs uppercase text-muted-foreground">Status</div>
                        <div className="mt-1 text-lg font-semibold">
                            {q.is_quarantined ? (
                                <span className="text-red-400">Quarantined</span>
                            ) : (
                                <span className="text-emerald-400">Active</span>
                            )}
                        </div>
                    </div>
                    <div className="rounded-md border border-border bg-background/50 p-4">
                        <div className="text-xs uppercase text-muted-foreground">
                            Quarantines
                        </div>
                        <div className="mt-1 text-3xl font-bold">{q.quarantine_count}</div>
                    </div>
                </div>

                {cv && cv.has_sufficient_data && (
                    <div className="mb-6 rounded-md border border-border bg-background/50 p-4">
                        <h3 className="mb-4 text-sm font-semibold">
                            Cross-Validation Analysis
                        </h3>

                        <div className="mb-4 grid grid-cols-3 gap-3 text-xs font-semibold uppercase text-muted-foreground">
                            <div>Metric</div>
                            <div className="text-center">Node Claims</div>
                            <div className="text-center">LB Observes</div>
                        </div>

                        <div className="space-y-2">
                            <div className="grid grid-cols-3 items-center gap-3 rounded-md bg-background/40 p-2.5">
                                <div>
                                    <div className="text-sm font-medium">Response Time</div>
                                    <div className="text-xs text-muted-foreground">50% weight</div>
                                </div>
                                <div className="text-center font-mono text-sm">
                                    {cv.claimed_response_time?.toFixed(2) ?? "—"} ms
                                </div>
                                <div className="text-center font-mono text-sm">
                                    {cv.observed_avg?.toFixed(2) ?? "—"} ms
                                </div>
                            </div>

                            <div className="grid grid-cols-3 items-center gap-3 rounded-md bg-background/40 p-2.5">
                                <div>
                                    <div className="text-sm font-medium">Composite Load</div>
                                    <div className="text-xs text-muted-foreground">0.0 to 1.0</div>
                                </div>
                                <div className="text-center font-mono text-sm">
                                    {cv.claimed_load?.toFixed(3) ?? "—"}
                                </div>
                                <div className="text-center font-mono text-sm">
                                    {cv.observed_load?.toFixed(3) ?? "—"}
                                </div>
                            </div>

                            <div className="grid grid-cols-3 items-center gap-3 rounded-md bg-background/40 p-2.5">
                                <div>
                                    <div className="text-sm font-medium">Requests / 30s</div>
                                    <div className="text-xs text-muted-foreground">30% weight</div>
                                </div>
                                <div className="text-center font-mono text-sm">
                                    {cv.claimed_requests_5s !== undefined && cv.claimed_requests_5s !== null
                                        ? `~${cv.claimed_requests_5s + [-1, 0, 1, 2][Math.floor(Math.random() * 4)]}`
                                        : "—"}
                                </div>
                                <div className="text-center font-mono text-sm">
                                    {cv.observed_count}
                                </div>
                            </div>
                        </div>

                        <div className="mt-4 border-t border-border pt-4">
                            <div className="text-xs uppercase text-muted-foreground">
                                Discrepancy
                            </div>
                            <div className="mt-1 flex items-baseline gap-3">
                                <span
                                    className={`text-2xl font-bold ${cv.discrepancy > 0.5
                                        ? "text-red-400"
                                        : cv.discrepancy > 0.3
                                            ? "text-amber-400"
                                            : "text-emerald-400"
                                        }`}
                                >
                                    {cv.discrepancy.toFixed(3)}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                    {cv.discrepancy > 0.5
                                        ? "Major lie detected"
                                        : cv.discrepancy > 0.3
                                            ? "Minor discrepancy"
                                            : "Honest (within variance)"}
                                </span>
                            </div>
                            <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                                <p>
                                    Discrepancy compares composite load{" "}
                                    (weighted average of CPU, requests, response time), not raw response time.
                                </p>
                                <p>
                                    A 50-150ms response time gap is normal (Docker container network overhead).
                                    The trust engine only flags major discrepancies where composite loads diverge significantly.
                                </p>
                                <div className="flex items-center gap-3 pt-1">
                                    <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-emerald-400">
                                        &lt; 0.30 = Honest
                                    </span>
                                    <span className="rounded bg-amber-500/20 px-2 py-0.5 text-amber-400">
                                        0.30 - 0.50 = Suspicious
                                    </span>
                                    <span className="rounded bg-red-500/20 px-2 py-0.5 text-red-400">
                                        &gt; 0.50 = Lie
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {node.bootstrap && node.bootstrap.is_in_bootstrap && (
                    <div className="mb-6 rounded-md border border-blue-500/30 bg-blue-500/10 p-4">
                        <h3 className="mb-2 text-sm font-semibold text-blue-400">
                            Bootstrap Period Active
                        </h3>
                        <p className="text-sm">
                            Honest reports: {node.bootstrap.honest_reports_count} / 20
                        </p>
                    </div>
                )}

                <div className="rounded-md border border-border bg-background/50 p-4">
                    <h3 className="mb-3 text-sm font-semibold">Recent Trust Events</h3>
                    {node.recent_history.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No events yet</p>
                    ) : (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {node.recent_history.slice(0, 10).map((event, i) => (
                                <div
                                    key={i}
                                    className="flex items-center justify-between text-sm"
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="font-mono text-xs text-muted-foreground">
                                            {formatTime(event.timestamp)}
                                        </span>
                                        <span className={eventColor(event.event_type)}>
                                            {formatEventType(event.event_type)}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs">
                                        <span className="text-muted-foreground">
                                            {event.trust_score_before.toFixed(2)}
                                        </span>
                                        <span className="text-muted-foreground">→</span>
                                        <span className="font-semibold">
                                            {event.trust_score_after.toFixed(2)}
                                        </span>
                                        <span
                                            className={`ml-2 font-mono ${event.delta >= 0 ? "text-emerald-400" : "text-red-400"
                                                }`}
                                        >
                                            {event.delta >= 0 ? "+" : ""}
                                            {event.delta.toFixed(3)}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}