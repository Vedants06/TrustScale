"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import type { NodeTrustDetails } from "@/lib/types";

interface TrafficFlowProps {
  nodes: NodeTrustDetails[];
  triggerCount: number;
}

interface Particle {
  id: string;
  startX: number;
  startY: number;
  targetX: number;
  targetY: number;
}

export function TrafficFlow({ nodes, triggerCount }: TrafficFlowProps) {
  const [particles, setParticles] = useState<Particle[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (triggerCount === 0 || nodes.length === 0) return;

    const container = containerRef.current;
    if (!container) return;

    const eligible = nodes.filter((n) => !n.quarantine.is_quarantined);
    if (eligible.length === 0) return;

    const containerRect = container.getBoundingClientRect();

    const newParticles: Particle[] = [];

    for (let i = 0; i < 8; i++) {
      const targetNode = eligible[Math.floor(Math.random() * eligible.length)];
      const nodeEl = document.querySelector(
        `[data-node-id="${targetNode.node_id}"]`,
      );

      if (!nodeEl) continue;

      const nodeRect = nodeEl.getBoundingClientRect();

      const targetX = nodeRect.left - containerRect.left + nodeRect.width / 2;
      const targetY = nodeRect.top - containerRect.top + nodeRect.height / 2;

      newParticles.push({
        id: `${Date.now()}-${i}-${Math.random()}`,
        startX: containerRect.width / 2,
        startY: 0,
        targetX,
        targetY,
      });
    }

    setParticles((prev) => [...prev, ...newParticles]);

    const timer = setTimeout(() => {
      setParticles((prev) =>
        prev.filter((p) => !newParticles.some((np) => np.id === p.id)),
      );
    }, 2500);

    return () => clearTimeout(timer);
  }, [triggerCount, nodes]);

  return (
    <div
      ref={containerRef}
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      <AnimatePresence>
        {particles.map((particle, index) => (
          <motion.div
            key={particle.id}
            className="absolute h-3 w-3 rounded-full"
            style={{
              background: "#3b82f6",
              boxShadow: "0 0 12px #3b82f6, 0 0 24px #3b82f6",
            }}
            initial={{
              x: particle.startX,
              y: particle.startY,
              opacity: 0,
              scale: 0.5,
            }}
            animate={{
              x: particle.targetX,
              y: particle.targetY,
              opacity: [0, 1, 1, 0],
              scale: [0.5, 1.5, 1, 0.3],
            }}
            transition={{
              duration: 1.8,
              ease: "easeOut",
              delay: index * 0.08,
            }}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}