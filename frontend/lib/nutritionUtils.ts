import type { NutritionAggregates, NutritionalMatch } from "./types";

/** Client-side roll-up when `aggregates` is missing (e.g. older saved snapshots). */
export function aggregatesFromMatches(matches: NutritionalMatch[]): NutritionAggregates {
  let cal = 0;
  let p = 0;
  let c = 0;
  let f = 0;
  let g = 0;
  for (const m of matches) {
    cal += Number(m.calories) || 0;
    p += Number(m.protein) || 0;
    c += Number(m.carbs) || 0;
    f += Number(m.fat) || 0;
    g += Number(m.grams) || 0;
  }
  return {
    total_calories: Math.round(cal * 10) / 10,
    total_protein_g: Math.round(p * 100) / 100,
    total_carbs_g: Math.round(c * 100) / 100,
    total_fat_g: Math.round(f * 100) / 100,
    total_grams: Math.round(g * 10) / 10,
    match_count: matches.length,
  };
}
