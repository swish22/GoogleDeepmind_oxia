/**
 * Reasoning model IDs for meal analysis / chat (must stay in sync with backend
 * `build_reasoning_models_list` ordering when possible).
 */
export function dedupeReasoningModels(models: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of models) {
    const m = (raw ?? "").trim();
    if (!m || seen.has(m)) continue;
    seen.add(m);
    out.push(m);
  }
  return out;
}

/** Offline / API-failure fallback — same order intent as `oxia/infrastructure/model_catalog.py`. */
export const FALLBACK_REASONING_MODELS = dedupeReasoningModels([
  "gemini-2.0-flash",
  "gemini-2.5-flash",
  "ollama:llava:latest",
  "ollama:llava-llama3:latest",
  "hf:google/flan-t5-large",
  "gemini-1.5-flash",
]);
