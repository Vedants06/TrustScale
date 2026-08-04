"use client";

interface ConnectionLineProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  active?: boolean;
  quarantined?: boolean;
  hubRadius?: number;
  nodeRadius?: number;
}

export function ConnectionLine({
  x1,
  y1,
  x2,
  y2,
  active = false,
  quarantined = false,
  hubRadius = 80,
  nodeRadius = 40,
}: ConnectionLineProps) {
  const color = quarantined ? "#ef4444" : active ? "#3b82f6" : "#2a2a35";
  const opacity = quarantined ? 0.3 : active ? 0.7 : 0.35;
  const width = active ? 2 : 1.5;

  // Calculate direction vector from hub to node
  const dx = x2 - x1;
  const dy = y2 - y1;
  const distance = Math.sqrt(dx * dx + dy * dy);

  if (distance === 0) return null;

  // Unit vector
  const ux = dx / distance;
  const uy = dy / distance;

  // Start line at hub edge, end line at node edge
  const startX = x1 + ux * hubRadius;
  const startY = y1 + uy * hubRadius;
  const endX = x2 - ux * nodeRadius;
  const endY = y2 - uy * nodeRadius;

  return (
    <line
      x1={startX}
      y1={startY}
      x2={endX}
      y2={endY}
      stroke={color}
      strokeWidth={width}
      strokeOpacity={opacity}
      strokeDasharray={quarantined ? "4 4" : undefined}
    />
  );
}