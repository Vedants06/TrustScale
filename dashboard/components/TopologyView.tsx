"use client";

import { useEffect, useMemo, useState } from "react";
import { LoadBalancerHub } from "./LoadBalancerHub";
import { NodeOrbit } from "./NodeOrbit";
import { ConnectionLine } from "./ConnectionLine";
import { TrafficParticle } from "./TrafficParticle";
import type { NodeTrustDetails } from "@/lib/types";

interface TopologyViewProps {
  nodes: NodeTrustDetails[];
  requestRate: number;
  totalRequests: number;
  trafficTrigger: number;
  onNodeClick?: (node: NodeTrustDetails) => void;
}

interface TrafficBurst {
  id: string;
  targetNodeId: string;
  delay: number;
}

const CONTAINER_SIZE = 700;
const CENTER = CONTAINER_SIZE / 2;
const ORBIT_RADIUS = 260;

export function TopologyView({
  nodes,
  requestRate,
  totalRequests,
  trafficTrigger,
  onNodeClick,
}: TopologyViewProps) {
  const [activeBursts, setActiveBursts] = useState<TrafficBurst[]>([]);

  // Calculate node positions in a circle
  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {};
    const n = nodes.length;

    nodes.forEach((node, i) => {
      // Start from top (-90 degrees) and go clockwise
      const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
      positions[node.node_id] = {
        x: CENTER + ORBIT_RADIUS * Math.cos(angle),
        y: CENTER + ORBIT_RADIUS * Math.sin(angle),
      };
    });

    return positions;
  }, [nodes]);

  // Trigger traffic bursts
  useEffect(() => {
    if (trafficTrigger === 0 || nodes.length === 0) return;

    const eligible = nodes.filter((n) => !n.quarantine.is_quarantined);
    if (eligible.length === 0) return;

    const newBursts: TrafficBurst[] = [];
    for (let i = 0; i < 10; i++) {
      const targetNode = eligible[Math.floor(Math.random() * eligible.length)];
      newBursts.push({
        id: `${Date.now()}-${i}-${Math.random()}`,
        targetNodeId: targetNode.node_id,
        delay: i * 0.15,
      });
    }

    setActiveBursts((prev) => [...prev, ...newBursts]);

    const timer = setTimeout(() => {
      setActiveBursts((prev) =>
        prev.filter((b) => !newBursts.some((nb) => nb.id === b.id)),
      );
    }, 3500);

    return () => clearTimeout(timer);
  }, [trafficTrigger, nodes]);

  const activeNodes = nodes.filter((n) => !n.quarantine.is_quarantined).length;

  // Which nodes are currently receiving traffic (for line highlighting)
  const activeConnections = new Set(activeBursts.map((b) => b.targetNodeId));

  return (
    <div
      className="relative mx-auto"
      style={{ width: CONTAINER_SIZE, height: CONTAINER_SIZE }}
    >
      {/* SVG layer for lines and particles */}
      <svg
        className="absolute inset-0 pointer-events-none"
        width={CONTAINER_SIZE}
        height={CONTAINER_SIZE}
      >
        {/* Connection lines */}
        {nodes.map((node) => {
          const pos = nodePositions[node.node_id];
          if (!pos) return null;

          return (
            <ConnectionLine
              key={node.node_id}
              x1={CENTER}
              y1={CENTER}
              x2={pos.x}
              y2={pos.y}
              active={activeConnections.has(node.node_id)}
              quarantined={node.quarantine.is_quarantined}
            />
          );
        })}

        {/* Traffic particles */}
        {activeBursts.map((burst) => {
          const pos = nodePositions[burst.targetNodeId];
          if (!pos) return null;

          return (
            <TrafficParticle
              key={burst.id}
              startX={CENTER}
              startY={CENTER}
              endX={pos.x}
              endY={pos.y}
              delay={burst.delay}
            />
          );
        })}
      </svg>

      {/* Load Balancer at center */}
      <div
        className="absolute z-10"
        style={{
          left: CENTER,
          top: CENTER,
          transform: "translate(-50%, -50%)",
        }}
      >
        <LoadBalancerHub
          totalRequests={totalRequests}
          requestRate={requestRate}
          activeNodes={activeNodes}
          totalNodes={nodes.length}
        />
      </div>

      {/* Node orbits */}
      {nodes.map((node) => {
        const pos = nodePositions[node.node_id];
        if (!pos) return null;

        return (
          <NodeOrbit
            key={node.node_id}
            node={node}
            x={pos.x}
            y={pos.y}
            onClick={onNodeClick ? () => onNodeClick(node) : undefined}
          />
        );
      })}
    </div>
  );
}