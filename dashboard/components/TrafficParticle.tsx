"use client";

import { motion } from "framer-motion";

interface TrafficParticleProps {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  duration?: number;
  delay?: number;
}

export function TrafficParticle({
  startX,
  startY,
  endX,
  endY,
  duration = 1.2,
  delay = 0,
}: TrafficParticleProps) {
  return (
    <motion.circle
      r={4}
      fill="#3b82f6"
      style={{
        filter: "drop-shadow(0 0 6px #3b82f6)",
      }}
      initial={{ cx: startX, cy: startY, opacity: 0 }}
      animate={{
        cx: [startX, endX],
        cy: [startY, endY],
        opacity: [0, 1, 1, 0],
      }}
      transition={{
        duration,
        delay,
        ease: "easeOut",
        times: [0, 0.1, 0.9, 1],
      }}
    />
  );
}