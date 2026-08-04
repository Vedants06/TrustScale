"use client";

interface ConnectionLineProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  active?: boolean;
  quarantined?: boolean;
}

export function ConnectionLine({
  x1,
  y1,
  x2,
  y2,
  active = false,
  quarantined = false,
}: ConnectionLineProps) {
  const color = quarantined ? "#ef4444" : active ? "#3b82f6" : "#2a2a35";
  const opacity = quarantined ? 0.3 : active ? 0.6 : 0.4;
  const width = active ? 2 : 1.5;

  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke={color}
      strokeWidth={width}
      strokeOpacity={opacity}
      strokeDasharray={quarantined ? "4 4" : undefined}
    />
  );
}