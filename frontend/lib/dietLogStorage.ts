import type { AnalysisResponse } from "./types";

const STORAGE_KEY = "oxia_diet_logs_v1";
const MAX_LOGS = 24;

export type SavedDietLogEntry = {
  id: string;
  name: string;
  savedAt: number;
  analysis: AnalysisResponse;
};

function isFiniteNumber(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

function isAnalysisResponseLike(v: unknown): v is AnalysisResponse {
  const a = v as AnalysisResponse;
  if (!a || typeof a !== "object") return false;
  if (typeof a.meal_id !== "string") return false;
  if (typeof a.meal_name !== "string") return false;
  if (!Array.isArray(a.ingredients)) return false;
  if (!isFiniteNumber(a.estimated_glycemic_load)) return false;
  if (typeof a.micro_nutrient_density !== "string") return false;

  const mb: unknown = (a as any).macro_breakdown;
  if (!mb || typeof mb !== "object") return false;
  if (!isFiniteNumber((mb as any).carbs_g)) return false;
  if (!isFiniteNumber((mb as any).protein_g)) return false;
  if (!isFiniteNumber((mb as any).fat_g)) return false;

  const ga: unknown = (a as any).glucose_architect;
  if (!ga || typeof ga !== "object") return false;
  if (!isFiniteNumber((ga as any).peak_glucose)) return false;
  if (!isFiniteNumber((ga as any).spike_time_mins)) return false;
  if (!Array.isArray((ga as any).glucose_curve)) return false;

  const ih: unknown = (a as any).inflammation_hunter;
  if (!ih || typeof ih !== "object") return false;
  if (!isFiniteNumber((ih as any).stress_score)) return false;
  if (!Array.isArray((ih as any).hidden_disruptors)) return false;
  if (typeof (ih as any).disruptors_detected !== "boolean") return false;

  const pg: unknown = (a as any).performance_ghost;
  if (!pg || typeof pg !== "object") return false;
  if (!isFiniteNumber((pg as any).deep_work_window_mins)) return false;
  if (typeof (pg as any).brain_fog_risk !== "string") return false;
  if (typeof (pg as any).ghost_insight !== "string") return false;
  if (!(pg as any).cognitive_state || typeof (pg as any).cognitive_state !== "object") return false;
  if (typeof (pg as any).cognitive_state.state_label !== "string") return false;

  const nt: unknown = (a as any).nutritional_truth;
  if (!nt || typeof nt !== "object") return false;
  if (typeof (nt as any).source !== "string") return false;
  if (!Array.isArray((nt as any).dataset_matches)) return false;

  return true;
}

function readAll(): SavedDietLogEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (x): x is SavedDietLogEntry =>
        x &&
        typeof x === "object" &&
        typeof (x as SavedDietLogEntry).id === "string" &&
        typeof (x as SavedDietLogEntry).name === "string" &&
        typeof (x as SavedDietLogEntry).savedAt === "number" &&
        isAnalysisResponseLike((x as SavedDietLogEntry).analysis),
    );
  } catch {
    return [];
  }
}

function writeAll(entries: SavedDietLogEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

export function listSavedDietLogs(): SavedDietLogEntry[] {
  return readAll().sort((a, b) => b.savedAt - a.savedAt);
}

export function saveDietLog(name: string, analysis: AnalysisResponse): SavedDietLogEntry {
  const trimmed = name.trim() || `Meal ${new Date().toLocaleDateString()}`;
  const entry: SavedDietLogEntry = {
    id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`,
    name: trimmed.slice(0, 120),
    savedAt: Date.now(),
    analysis: JSON.parse(JSON.stringify(analysis)) as AnalysisResponse,
  };
  const all = readAll();
  all.unshift(entry);
  writeAll(all.slice(0, MAX_LOGS));
  return entry;
}

export function renameDietLog(id: string, newName: string): boolean {
  const name = newName.trim().slice(0, 120);
  if (!name) return false;
  const all = readAll();
  const idx = all.findIndex((e) => e.id === id);
  if (idx < 0) return false;
  all[idx] = { ...all[idx], name };
  writeAll(all);
  return true;
}

export function deleteDietLog(id: string): void {
  writeAll(readAll().filter((e) => e.id !== id));
}
