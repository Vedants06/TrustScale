"use client";

import { useEffect } from "react";
import { X, Menu } from "lucide-react";
import { useActivityLog } from "@/lib/hooks/useActivityLog";
import type { LogLevel } from "@/lib/types";

interface ActivityDrawerProps {
  open: boolean;
  onClose: () => void;
}

function levelColors(level: LogLevel) {
  const map: Record<LogLevel, { bg: string; text: string; dot: string }> = {
    info: {
      bg: "bg-blue-500/10 border-blue-500/30",
      text: "text-blue-400",
      dot: "bg-blue-500",
    },
    warn: {
      bg: "bg-amber-500/10 border-amber-500/30",
      text: "text-amber-400",
      dot: "bg-amber-500",
    },
    error: {
      bg: "bg-red-500/10 border-red-500/30",
      text: "text-red-400",
      dot: "bg-red-500",
    },
    success: {
      bg: "bg-emerald-500/10 border-emerald-500/30",
      text: "text-emerald-400",
      dot: "bg-emerald-500",
    },
  };
  return map[level];
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function ActivityDrawer({ open, onClose }: ActivityDrawerProps) {
  const entries = useActivityLog((s) => s.entries);
  const clear = useActivityLog((s) => s.clear);

  useEffect(() => {
    if (open) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 right-0 z-50 h-screen w-96 border-l border-border bg-card shadow-2xl transition-transform duration-300 ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between border-b border-border p-4">
          <h2 className="text-lg font-semibold">Activity Log</h2>
          <div className="flex items-center gap-2">
            {entries.length > 0 && (
              <button
                onClick={clear}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            )}
            <button
              onClick={onClose}
              className="rounded-md p-1 hover:bg-secondary"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="h-[calc(100vh-60px)] overflow-y-auto p-4">
          {entries.length === 0 ? (
            <p className="pt-8 text-center text-sm text-muted-foreground">
              No activity yet
            </p>
          ) : (
            <div className="space-y-2">
              {entries.map((entry) => {
                const colors = levelColors(entry.level);
                return (
                  <div
                    key={entry.id}
                    className={`flex items-start gap-3 rounded-md border p-2.5 text-sm ${colors.bg}`}
                  >
                    <div className="mt-1.5">
                      <span className={`h-2 w-2 flex-shrink-0 rounded-full block ${colors.dot}`} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`font-mono text-xs ${colors.text}`}>
                          {formatTime(entry.timestamp)}
                        </span>
                        <span className={`text-xs font-semibold uppercase ${colors.text}`}>
                          {entry.level}
                        </span>
                      </div>
                      <p className="mt-1 text-sm break-words">{entry.message}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

export function ActivityDrawerToggle({ onClick }: { onClick: () => void }) {
  const count = useActivityLog((s) => s.entries.length);

  return (
    <button
      onClick={onClick}
      className="relative flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm transition-colors hover:bg-secondary"
    >
      <Menu className="h-4 w-4" />
      <span>Activity Log</span>
      {count > 0 && (
        <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-bold text-primary-foreground">
          {count}
        </span>
      )}
    </button>
  );
}