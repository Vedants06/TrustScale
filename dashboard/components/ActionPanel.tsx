"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useActivityLog } from "@/lib/hooks/useActivityLog";
import type {
    BehaviorMode,
    NodeTrustDetails,
    RoutingStrategy,
    ScenarioConfig,
} from "@/lib/types";

interface ActionPanelProps {
    nodes: NodeTrustDetails[];
}

const BEHAVIOR_OPTIONS: { value: BehaviorMode; label: string }[] = [
    { value: "honest", label: "Honest (reset)" },
    { value: "under_reporter", label: "Under-Reporter" },
    { value: "over_reporter", label: "Over-Reporter" },
    { value: "colluder", label: "Colluder" },
];

export function ActionPanel({ nodes }: ActionPanelProps) {
    const [scenarios, setScenarios] = useState<ScenarioConfig[]>([]);
    const [selectedScenario, setSelectedScenario] = useState<string>("");
    const [selectedNode, setSelectedNode] = useState<string>("");
    const [selectedBehavior, setSelectedBehavior] =
        useState<BehaviorMode>("under_reporter");
    const [intensity, setIntensity] = useState<number>(0.8);
    const [strategy, setStrategy] = useState<RoutingStrategy>("trust_aware");
    const [isSending, setIsSending] = useState(false);
    const [scenarioRunning, setScenarioRunning] = useState(false);
    const [runningScenarioName, setRunningScenarioName] = useState<string>("");

    const addLog = useActivityLog((s) => s.addEntry);

    useEffect(() => {
        async function fetchScenarios() {
            try {
                const list = await api.listScenarios();
                setScenarios(list);
                if (list.length > 0 && !selectedScenario) {
                    setSelectedScenario(list[0].scenario_id);
                }
            } catch (err) {
                console.error("Failed to load scenarios", err);
            }
        }
        fetchScenarios();
    }, [selectedScenario]);

    useEffect(() => {
        async function checkStatus() {
            try {
                const response = await fetch("http://localhost:8200/scenarios/status");
                const data = await response.json();
                setScenarioRunning(data.is_running);
                setRunningScenarioName(data.running_scenario || "");
            } catch {
                // ignore
            }
        }
        checkStatus();
        const interval = setInterval(checkStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (nodes.length > 0 && !selectedNode) {
            setSelectedNode(nodes[0].node_id);
        }
    }, [nodes, selectedNode]);

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
    }, []);

    async function handleSendTraffic() {
        setIsSending(true);
        try {
            addLog("Sending traffic burst (20 requests)", "info");
            await api.sendWork(300, 20);
            toast.success("Traffic burst sent");
            addLog("Traffic burst completed", "success");
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Unknown error";
            toast.error(`Traffic failed: ${msg}`);
            addLog(`Traffic failed: ${msg}`, "error");
        } finally {
            setIsSending(false);
        }
    }

    async function handleAttackNode() {
        if (!selectedNode) return;
        try {
            await api.setNodeBehavior(selectedNode, selectedBehavior, intensity);
            toast.success(`${selectedNode} → ${selectedBehavior}`);
            addLog(
                `Attack triggered: ${selectedNode} → ${selectedBehavior} (intensity ${intensity})`,
                "warn",
            );
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Unknown error";
            toast.error(`Attack failed: ${msg}`);
            addLog(`Attack failed: ${msg}`, "error");
        }
    }

    async function handleResetAll() {
        try {
            const nodeIds = nodes.map((n) => n.node_id);
            await api.resetAllNodes(nodeIds);
            toast.success("All nodes reset to honest");
            addLog(`Reset all ${nodeIds.length} nodes to honest`, "success");
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Unknown error";
            toast.error(`Reset failed: ${msg}`);
            addLog(`Reset failed: ${msg}`, "error");
        }
    }

    async function handleRunScenario() {
        if (!selectedScenario) return;
        try {
            await api.runScenario(selectedScenario, 1);
            const scenario = scenarios.find((s) => s.scenario_id === selectedScenario);
            toast.success(`Scenario started: ${scenario?.name || selectedScenario}`);
            addLog(
                `Scenario running: ${scenario?.name || selectedScenario} (${scenario?.duration_seconds || "?"
                }s)`,
                "info",
            );
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Unknown error";
            toast.error(`Scenario failed: ${msg}`);
            addLog(`Scenario failed: ${msg}`, "error");
        }
    }

    async function handleToggleStrategy() {
        const newStrategy: RoutingStrategy =
            strategy === "trust_aware" ? "round_robin" : "trust_aware";
        try {
            await api.setRoutingStrategy(newStrategy);
            setStrategy(newStrategy);
            toast.success(`Strategy: ${newStrategy}`);
            addLog(`Routing strategy changed to: ${newStrategy}`, "info");
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Unknown error";
            toast.error(`Strategy change failed: ${msg}`);
        }
    }

    return (
        <div className="space-y-4 rounded-lg border border-border bg-card p-6">
            <h2 className="text-lg font-semibold">Actions</h2>

            <div className="space-y-3">
                <button
                    onClick={handleSendTraffic}
                    disabled={isSending}
                    className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                    {isSending ? "Sending..." : "Send Traffic Burst"}
                </button>

                <div className="space-y-2 rounded-md border border-border bg-background/50 p-3">
                    <label className="text-xs font-medium text-muted-foreground">
                        Attack a Node
                    </label>

                    <select
                        value={selectedNode}
                        onChange={(e) => setSelectedNode(e.target.value)}
                        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    >
                        {nodes.map((n) => (
                            <option key={n.node_id} value={n.node_id}>
                                {n.node_id}
                            </option>
                        ))}
                    </select>

                    <select
                        value={selectedBehavior}
                        onChange={(e) => setSelectedBehavior(e.target.value as BehaviorMode)}
                        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    >
                        {BEHAVIOR_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>

                    <div className="flex items-center gap-2">
                        <input
                            type="range"
                            min="0.1"
                            max="0.9"
                            step="0.1"
                            value={intensity}
                            onChange={(e) => setIntensity(Number(e.target.value))}
                            className="flex-1"
                        />
                        <span className="w-10 text-right text-xs text-muted-foreground">
                            {intensity.toFixed(1)}
                        </span>
                    </div>

                    <button
                        onClick={handleAttackNode}
                        className="w-full rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-700"
                    >
                        Apply Behavior
                    </button>
                </div>

                <div className="space-y-2 rounded-md border border-border bg-background/50 p-3">
                    <label className="text-xs font-medium text-muted-foreground">
                        Run Scenario
                    </label>
                    <select
                        value={selectedScenario}
                        onChange={(e) => setSelectedScenario(e.target.value)}
                        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    >
                        {scenarios.map((s) => (
                            <option key={s.scenario_id} value={s.scenario_id}>
                                {s.name} {s.defense_enabled ? "" : "(no defense)"}
                            </option>
                        ))}
                    </select>

                    {selectedScenario && (
                        <p className="text-xs text-muted-foreground">
                            {scenarios.find((s) => s.scenario_id === selectedScenario)
                                ?.description}
                        </p>
                    )}

                    <button
                        onClick={handleRunScenario}
                        disabled={scenarioRunning}
                        className="w-full rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {scenarioRunning ? `Running: ${runningScenarioName}...` : "Run Scenario"}
                    </button>
                </div>

                <button
                    onClick={handleToggleStrategy}
                    className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-secondary"
                >
                    Strategy: {strategy === "trust_aware" ? "Trust-Aware" : "Round-Robin"}
                </button>

                <button
                    onClick={handleResetAll}
                    className="w-full rounded-md border border-red-500/50 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20"
                >
                    Reset All Nodes
                </button>
            </div>
        </div>
    );
}