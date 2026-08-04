"use client";

import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";

interface TrustSparklineProps {
  data: Array<{ timestamp: number; score: number }>;
  color?: string;
}

export function TrustSparkline({ data, color = "#3b82f6" }: TrustSparklineProps) {
  if (data.length < 2) {
    return (
      <div className="flex h-8 items-center justify-center">
        <div className="flex items-center gap-1.5">
          <div className="h-1 w-1 animate-pulse rounded-full bg-muted-foreground" />
          <div className="h-1 w-1 animate-pulse rounded-full bg-muted-foreground [animation-delay:150ms]" />
          <div className="h-1 w-1 animate-pulse rounded-full bg-muted-foreground [animation-delay:300ms]" />
        </div>
      </div>
    );
  }

  return (
    <div className="h-8 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
          <YAxis domain={[0, 1]} hide />
          <Line
            type="monotone"
            dataKey="score"
            stroke={color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}