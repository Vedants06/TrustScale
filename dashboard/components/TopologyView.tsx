"use client";

import { useMemo } from "react";
import { LoadBalancerHub } from "./LoadBalancerHub";
import { NodeOrbit } from "./NodeOrbit";
import { ConnectionLine } from "./ConnectionLine";
import { TrafficParticle } from "./TrafficParticle";
import { useTrafficDetection } from "@/lib/hooks/useTrafficDetection";
import type { NodeTrustDetails } from "@/lib/types";

interface TopologyViewProps {
  nodes: NodeTrustDetails[];
  requestRate: number;
  totalRequests: number;
  onNodeClick?: (node: NodeTrustDetails) => void;
}

const CONTAINER_SIZE = 700;
const CENTER = CONTAINER_SIZE / 2;
const ORBIT_RADIUS = 260;
const HUB_RADIUS = 80;
const NODE_RADIUS = 40;

export function TopologyView({
  nodes,
  requestRate,
  totalRequests,
  onNodeClick,
}: TopologyViewProps) {
  const trafficEvents = useTrafficDetection(nodes);

  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {};
    const n = nodes.length;

    nodes.forEach((node, i) => {
      const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
      positions[node.node_id] = {
        x: CENTER + ORBIT_RADIUS * Math.cos(angle),
        y: CENTER + ORBIT_RADIUS * Math.sin(angle),
      };
    });

    return positions;
  }, [nodes]);

  const activeNodes = nodes.filter((n) => !n.quarantine.is_quarantined).length;

  const activeConnections = new Set(trafficEvents.map((e) => e.nodeId));

  return (
    <div
      className="relative mx-auto"
      style={{ width: CONTAINER_SIZE, height: CONTAINER_SIZE }}
    >
      <svg
        className="pointer-events-none absolute inset-0"
        width={CONTAINER_SIZE}
        height={CONTAINER_SIZE}
      >
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
              hubRadius={HUB_RADIUS}
              nodeRadius={NODE_RADIUS}
            />
          );
        })}

        {trafficEvents.map((event, index) => {
          const pos = nodePositions[event.nodeId];
          if (!pos) return null;

          const dx = pos.x - CENTER;
          const dy = pos.y - CENTER;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const ux = dx / distance;
          const uy = dy / distance;

          const startX = CENTER + ux * HUB_RADIUS;
          const startY = CENTER + uy * HUB_RADIUS;
          const endX = pos.x - ux * NODE_RADIUS;
          const endY = pos.y - uy * NODE_RADIUS;

          return (
            <TrafficParticle
              key={event.id}
              startX={startX}
              startY={startY}
              endX={endX}
              endY={endY}
              delay={index * 0.05}
            />
          );
        })}
      </svg>

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