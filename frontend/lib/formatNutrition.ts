/** Display helpers — full values, no ellipsis truncation in tables/metrics. */

export function formatNutritionNumber(value: unknown, decimals = 2): string {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return "—";
  if (decimals <= 0) return String(Math.round(n));
  const s = n.toFixed(decimals);
  return s.replace(/\.?0+$/, "").replace(/\.$/, "") || "0";
}

export function formatCalories(value: unknown): string {
  return formatNutritionNumber(value, 2);
}
