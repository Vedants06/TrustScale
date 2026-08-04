"use client";

import { create } from "zustand";
import type { ActivityLogEntry, LogLevel } from "../types";

interface ActivityLogState {
  entries: ActivityLogEntry[];
  addEntry: (message: string, level?: LogLevel) => void;
  clear: () => void;
}

export const useActivityLog = create<ActivityLogState>((set) => ({
  entries: [],
  addEntry: (message, level = "info") =>
    set((state) => ({
      entries: [
        {
          id: `${Date.now()}-${Math.random()}`,
          timestamp: Date.now(),
          message,
          level,
        },
        ...state.entries,
      ].slice(0, 100),
    })),
  clear: () => set({ entries: [] }),
}));