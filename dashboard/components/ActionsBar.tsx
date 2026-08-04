"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Play, Zap, Shuffle, RotateCcw, Settings } from "lucide-react";
import { api } from "@/lib/api";
import { useActivityLog } from "@/lib/hooks/useActivityLog";
import type {
  BehaviorMode,
  NodeTrustDetails,
  RoutingStrategy,
  ScenarioConfig,
} from "@/lib/types";

interface ActionsBarProps {
  nodes: NodeTrustDetails[];
  onTrafficSent?: () => void;
}

const BEHAVIOR_OPTIONS: { value: BehaviorMode; label: string }[] = [
  { value: "honest", label: "Honest" },
  { value: "under_reporter", label: "Under-Report" },
  { value: "over_reporter", label: "Over-Report" },
  { value: "colluder", label: "Colluder" },
];

export function ActionsBar({ nodes, onTrafficSent }: ActionsBarProps) {
  const [scenarios, setScenarios] = useState<ScenarioConfig[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [selectedNode, setSelectedNode] = useState<string>("");
  const [selectedBehavior, setSelectedBehavior] =
    useState<BehaviorMode>("under_reporter");
  const [intensity, setIntensity] = useState<number>(0.8);
  const [strategy, setStrategy] = useState<RoutingStrategy>("trust_aware");
  const [isSending, setIsSending] = useState(false);
  const [scenarioRunning, setScenarioRunning] = useState(false);

  const addLog = useActivityLog((s) => s.addEntry);

  useEffect(() => {
    async function init() {
      try {
        const list = await api.listScenarios();
        setScenarios(list);
        if (list.length > 0) setSelectedScenario(list[0].scenario_id);

        const s = await api.getRoutingStrategy();
        setStrategy(s);
      } catch {
        // ignore
      }
    }
    init();
  }, []);

  useEffect(() => {
    if (nodes.length > 0 && !selectedNode) {
      setSelectedNode(nodes[0].node_id);
    }
  }, [nodes, selectedNode]);

  useEffect(() => {
    async function checkStatus() {
      try {
        const response = await fetch("http://localhost:8200/scenarios/status");
        const data = await response.json();
        setScenarioRunning(data.is_running);
      } catch {
        // ignore
      }
    }
    checkStatus();
    const interval = setInterval(checkStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  async function handleSendTraffic() {
    setIsSending(true);
    try {
      addLog("Sending traffic burst (20 requests)", "info");
      onTrafficSent?.();
      await api.sendWork(300, 20);
      toast.success("Traffic burst sent");
      addLog("Traffic burst completed", "success");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      toast.error(`Traffic failed: ${msg}`);
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
        `${selectedNode} set to ${selectedBehavior} (intensity ${intensity})`,
        "warn",
      );

      if (selectedBehavior !== "honest") {
        onTrafficSent?.();
        await api.sendWork(300, 30);
        addLog("Auto-traffic sent to trigger detection", "info");
      }
    } catch (err) {
      toast.error(`Attack failed`);
    }
  }

  async function handleResetAll() {
    try {
      const nodeIds = nodes.map((n) => n.node_id);
      await api.resetAllNodes(nodeIds);
      toast.success("All nodes reset");
      addLog(`Reset all ${nodeIds.length} nodes to honest`, "success");
    } catch {
      toast.error("Reset failed");
    }
  }

  async function handleRunScenario() {
    if (!selectedScenario) return;
    try {
      await api.runScenario(selectedScenario, 1);
      const scenario = scenarios.find((s) => s.scenario_id === selectedScenario);
      toast.success(`Scenario: ${scenario?.name}`);
      addLog(`Scenario started: ${scenario?.name}`, "info");
    } catch (err) {
      toast.error(`Scenario failed`);
    }
  }

  async function handleToggleStrategy() {
    const newStrategy: RoutingStrategy =
      strategy === "trust_aware" ? "round_robin" : "trust_aware";
    try {
      await api.setRoutingStrategy(newStrategy);
      setStrategy(newStrategy);
      toast.success(`Strategy: ${newStrategy}`);
      addLog(`Strategy changed to ${newStrategy}`, "info");
    } catch {
      toast.error("Strategy change failed");
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-center gap-3">
        {/* Send Traffic */}
        <button
          onClick={handleSendTraffic}
          disabled={isSending}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          <Zap className="h-4 w-4" />
          {isSending ? "Sending..." : "Send Traffic"}
        </button>

        <div className="h-8 w-px bg-border" />

        {/* Attack Node */}
        <div className="flex items-center gap-2">
          <select
            value={selectedNode}
            onChange={(e) => setSelectedNode(e.target.value)}
            className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          >
            {nodes.map((n) => (
              <option key={n.node_id} value={n.node_id}>
                {n.node_id.replace("node_", "Node ")}
              </option>
            ))}
          </select>

          <select
            value={selectedBehavior}
            onChange={(e) => setSelectedBehavior(e.target.value as BehaviorMode)}
            className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          >
            {BEHAVIOR_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <div className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2">
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.1"
              value={intensity}
              onChange={(e) => setIntensity(Number(e.target.value))}
              className="w-20"
            />
            <span className="w-8 text-right text-xs font-mono">
              {intensity.toFixed(1)}
            </span>
          </div>

          <button
            onClick={handleAttackNode}
            className="flex items-center gap-2 rounded-md bg-amber-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-amber-700"
          >
            Apply
          </button>
        </div>

        <div className="h-8 w-px bg-border" />

        {/* Scenario */}
        <div className="flex items-center gap-2">
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="rounded-md border border-border bg-background px-3 py-2 text-sm max-w-64"
          >
            {scenarios.map((s) => (
              <option key={s.scenario_id} value={s.scenario_id}>
                {s.name}
              </option>
            ))}
          </select>

          <button
            onClick={handleRunScenario}
            disabled={scenarioRunning}
            className="flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-purple-700 disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {scenarioRunning ? "Running..." : "Run Scenario"}
          </button>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={handleToggleStrategy}
            className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary"
          >
            <Shuffle className="h-4 w-4" />
            {strategy === "trust_aware" ? "Trust-Aware" : "Round-Robin"}
          </button>

          <button
            onClick={handleResetAll}
            className="flex items-center gap-2 rounded-md border border-red-500/50 bg-red-500/10 px-3 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20"
          >
            <RotateCcw className="h-4 w-4" />
            Reset All
          </button>
        </div>
      </div>
    </div>
  );
}