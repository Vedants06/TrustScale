"use client";

import { useActivityLog } from "@/lib/hooks/useActivityLog";
import type { LogLevel } from "@/lib/types";

function LevelIcon({ level }: { level: LogLevel }) {
  const colors: Record<LogLevel, string> = {
    info: "bg-blue-500",
    warn: "bg-amber-500",
    error: "bg-red-500",
    success: "bg-emerald-500",
  };

  return (
    <span className={`inline-block h-2 w-2 flex-shrink-0 rounded-full ${colors[level]}`} />
  );
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function ActivityLog() {
  const entries = useActivityLog((s) => s.entries);
  const clear = useActivityLog((s) => s.clear);

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border p-4">
        <h2 className="text-lg font-semibold">Activity Log</h2>
        {entries.length > 0 && (
          <button
            onClick={clear}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Clear
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {entries.length === 0 ? (
          <p className="text-center text-sm text-muted-foreground">
            No activity yet
          </p>
        ) : (
          <div className="space-y-2">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start gap-3 rounded-md bg-background/50 p-2 text-sm"
              >
                <div className="mt-1.5">
                  <LevelIcon level={entry.level} />
                </div>
                <div className="flex-1">
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-xs text-muted-foreground">
                      {formatTime(entry.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm">{entry.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}