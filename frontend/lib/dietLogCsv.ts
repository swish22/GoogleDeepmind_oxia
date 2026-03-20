import type { AnalysisResponse, NutritionalMatch } from "./types";

/** Excel-friendly UTF-8 with BOM */
const CSV_BOM = "\ufeff";

function csvEscape(cell: string): string {
  const s = String(cell).replace(/"/g, '""');
  return /[",\n\r]/.test(s) ? `"${s}"` : s;
}

function line(cells: string[]): string {
  return cells.map(csvEscape).join(",");
}

/**
 * Structured diet log CSV: meal block, full-width ingredient table, rollup, metadata.
 */
export function buildDietLogCsvStructured(a: AnalysisResponse): string {
  const truth = a.nutritional_truth;
  const matches = truth?.dataset_matches ?? [];
  const agg = truth?.aggregates;
  const rows: string[] = [];

  rows.push(line(["section", "value"]));
  rows.push(line(["meal_name", a.meal_name ?? ""]));
  rows.push(line(["meal_id", a.meal_id ?? ""]));
  rows.push(line(["glycemic_load_est", String(a.estimated_glycemic_load ?? "")]));
  rows.push(line(["macro_carbs_g", String(a.macro_breakdown?.carbs_g ?? "")]));
  rows.push(line(["macro_protein_g", String(a.macro_breakdown?.protein_g ?? "")]));
  rows.push(line(["macro_fat_g", String(a.macro_breakdown?.fat_g ?? "")]));
  rows.push(line(["macro_fiber_g", String(a.macro_breakdown?.fiber_g ?? "")]));
  rows.push(line(["macro_fruits_veg_g", String(a.macro_breakdown?.fruits_veg_g ?? "")]));
  rows.push(line(["nutrition_source_summary", truth?.source ?? ""]));
  rows.push(line([]));

  rows.push(
    line([
      "ingredient_name",
      "data_source",
      "data_source_label",
      "calories",
      "protein_g",
      "carbs_g",
      "fat_g",
      "grams_g",
      "portion_note",
    ]),
  );
  for (const m of matches as NutritionalMatch[]) {
    rows.push(
      line([
        String(m.name ?? ""),
        String(m.data_source ?? ""),
        String(m.data_source_label ?? ""),
        String(m.calories ?? ""),
        String(m.protein ?? ""),
        String(m.carbs ?? ""),
        String(m.fat ?? ""),
        String(m.grams ?? ""),
        String(m.portion_note ?? ""),
      ]),
    );
  }

  rows.push(line([]));
  if (agg) {
    rows.push(
      line([
        "rollup_total_calories",
        "rollup_protein_g",
        "rollup_carbs_g",
        "rollup_fat_g",
        "rollup_grams_g",
        "rollup_match_count",
      ]),
    );
    rows.push(
      line([
        String(agg.total_calories),
        String(agg.total_protein_g),
        String(agg.total_carbs_g),
        String(agg.total_fat_g),
        String(agg.total_grams),
        String(agg.match_count),
      ]),
    );
  }

  if (truth?.sources_breakdown && Object.keys(truth.sources_breakdown).length > 0) {
    rows.push(line([]));
    rows.push(line(["sources_breakdown_key", "match_count"]));
    for (const [k, v] of Object.entries(truth.sources_breakdown)) {
      rows.push(line([k, String(v)]));
    }
  }

  return CSV_BOM + rows.join("\r\n");
}
