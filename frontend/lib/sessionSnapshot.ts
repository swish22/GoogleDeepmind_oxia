import type { AnalysisResponse } from "./types";

const KEY = "oxia_dashboard_snapshot_v1";

export type DashboardSnapshot = {
  version: 1;
  analysis: AnalysisResponse;
  reasoningModel: string;
  savedAt: number;
};

/** Persist last dashboard on this device (local only; not a server backup). */
export function saveDashboardSnapshot(analysis: AnalysisResponse, reasoningModel: string): void {
  if (typeof window === "undefined") return;
  const payload: DashboardSnapshot = {
    version: 1,
    analysis,
    reasoningModel,
    savedAt: Date.now(),
  };
  try {
    localStorage.setItem(KEY, JSON.stringify(payload));
  } catch {
    // Quota exceeded — ignore; user can still export from Report card.
  }
}

export function loadDashboardSnapshot(): DashboardSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as DashboardSnapshot;
    if (data?.version !== 1 || !data.analysis || typeof data.reasoningModel !== "string") return null;
    return data;
  } catch {
    return null;
  }
}

export function clearDashboardSnapshot(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
}
