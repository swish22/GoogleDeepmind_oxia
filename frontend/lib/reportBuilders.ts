import { buildDietLogCsvStructured } from "./dietLogCsv";
import type { AnalysisResponse, NutritionalMatch } from "./types";

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getGlucoseAt(
  curve: Array<{ time_mins: number; glucose_mg_dl: number }>,
  t: number,
) {
  const pt = curve.find((p) => p.time_mins === t);
  return pt?.glucose_mg_dl ?? 85;
}

function sourceAbbr(m: NutritionalMatch): string {
  const id = m.data_source ?? "huggingface_maressay";
  if (id === "open_food_facts") return "OFF";
  if (id === "usda_fdc") return "USDA";
  return "HF";
}

function matchesRowsHtml(matches: NutritionalMatch[]): string {
  if (!matches.length) {
    return `<tr><td colspan="7" style="padding:10px;color:#94a3b8;border-top:1px solid #1f2937;">No verified matches</td></tr>`;
  }
  return matches
    .slice(0, 12)
    .map(
      (m) =>
        `<tr>
              <td style="padding:8px 10px;border-top:1px solid #1f2937;word-break:break-word;">${escapeHtml(String(m.name ?? "—"))}</td>
              <td style="padding:8px 10px;border-top:1px solid #1f2937;font-size:11px;color:#94a3b8;">${escapeHtml(sourceAbbr(m))}</td>
              <td style="padding:8px 10px;border-top:1px solid #1f2937;">${m.calories ?? "—"}</td>
              <td style="padding:8px 10px;border-top:1px solid #1f2937;">${m.protein ?? "—"}</td>
              <td style="padding:8px 10px;border-top:1px solid #1f2937;">${m.carbs ?? "—"}</td>
              <td style="padding:8px 10px;border-top:1px solid #1f2937;">${m.fat ?? "—"}</td>
              <td style="padding:8px 10px;border-top:1px solid #1f2937;">${m.grams ?? "—"}</td>
            </tr>`,
    )
    .join("");
}

/** Full branded shareable report (HTML). */
export function buildFullReportHtml(a: AnalysisResponse, title?: string): string {
  const ga = a.glucose_architect;
  const ih = a.inflammation_hunter;
  const pg = a.performance_ghost;
  const cs = pg.cognitive_state;

  const peak = ga.peak_glucose;
  const spikeTime = ga.spike_time_mins;
  const deepWork = pg.deep_work_window_mins;
  const brainFogRisk = pg.brain_fog_risk;

  const times = [0, 30, 60, 90, 120, 180];
  const curve = ga.glucose_curve;
  const timelineRows = times
    .map((t) => ({ t, g: getGlucoseAt(curve, t) }))
    .map(
      (r) =>
        `<tr><td style="padding:8px 10px;border-top:1px solid #1f2937;">${r.t}</td><td style="padding:8px 10px;border-top:1px solid #1f2937;">${r.g}</td></tr>`,
    )
    .join("");

  const opts = (a.optimization_suggestions ?? []).slice(0, 3);
  const optsHtml = opts.length
    ? `<ul style="margin:0;padding-left:18px;">${opts.map((o) => `<li style="margin:6px 0;">${escapeHtml(o)}</li>`).join("")}</ul>`
    : `<div style="color:#94a3b8;font-size:13px;">No suggestions available.</div>`;

  const matches = a.nutritional_truth?.dataset_matches ?? [];
  const matchesHtml = matchesRowsHtml(matches);
  const agg = a.nutritional_truth?.aggregates;
  const aggLine =
    agg && agg.match_count > 0
      ? `<div class="muted" style="margin-top:8px;">Dataset roll-up: ~${agg.total_calories} kcal · P ${agg.total_protein_g}g · C ${agg.total_carbs_g}g · F ${agg.total_fat_g}g · ${agg.match_count} matches</div>`
      : "";

  const dateStr = new Date().toLocaleString();
  const docTitle = escapeHtml(title || `Oxia — ${a.meal_name || "Meal"}`);

  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>${docTitle}</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Space Grotesk', sans-serif; background:#05070a; color:#e2e8f0; margin:0; padding:28px; box-sizing:border-box; }
    .wrap { max-width:900px; margin:0 auto; }
    .hero { border:1px solid rgba(56,189,248,0.25); border-radius:22px; padding:22px 26px; background:linear-gradient(145deg,#0a0f1a 0%,#0d1321 55%,#0f172a 100%); }
    .brand { color:#38bdf8; font-weight:800; letter-spacing:-0.02em; font-size:22px; }
    .meal { margin-top:10px; font-size:clamp(22px,4vw,32px); font-weight:800; word-break:break-word; }
    .meta { color:#94a3b8; font-size:13px; margin-top:6px; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:14px; margin-top:18px; }
    .card { border:1px solid #1f2937; border-radius:18px; padding:16px; background:#0b1220; min-width:0; }
    .k { font-size:12px; letter-spacing:0.14em; text-transform:uppercase; color:#94a3b8; font-weight:700; }
    .v { margin-top:10px; font-size:clamp(20px,4vw,28px); font-weight:800; font-family:'JetBrains Mono',monospace; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    .muted { color:#94a3b8; font-size:13px; line-height:1.6; }
    .disclaimer { margin-top:14px; font-size:12px; color:#64748b; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div class="brand">Oxia · Metabolic Digital Twin</div>
      <div class="meal">${escapeHtml(a.meal_name ?? "Meal")}</div>
      <div class="meta">${escapeHtml(dateStr)}</div>
      <div class="grid">
        <div class="card">
          <div class="k">Estimated Glycemic Load</div>
          <div class="v">${a.estimated_glycemic_load?.toFixed?.(1) ?? a.estimated_glycemic_load}</div>
        </div>
        <div class="card">
          <div class="k">Peak Glucose</div>
          <div class="v">${peak} mg/dL</div>
          <div class="muted" style="margin-top:8px;">Spikes around ${spikeTime} min</div>
        </div>
        <div class="card">
          <div class="k">Inflammation Stress</div>
          <div class="v" style="color:#fb7185;">${ih.stress_score}/10</div>
        </div>
        <div class="card">
          <div class="k">Performance</div>
          <div class="v" style="color:#a78bfa;">${escapeHtml(String(cs.state_emoji))} ${escapeHtml(String(cs.state_label))}</div>
          <div class="muted" style="margin-top:8px;">Deep work window: ${deepWork} min · Brain fog risk: ${escapeHtml(String(brainFogRisk))}</div>
        </div>
      </div>
    </div>

    <div style="margin-top:18px;" class="card">
      <div class="k">Your Next 3 Hours (sparse glucose)</div>
      <div class="muted" style="margin-top:8px;">Predicted readings at key time points.</div>
      <div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">
      <table>
        <thead>
          <tr>
            <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Time (min)</th>
            <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Glucose (mg/dL)</th>
          </tr>
        </thead>
        <tbody>${timelineRows}</tbody>
      </table>
      </div>
    </div>

    <div style="margin-top:18px;" class="grid">
      <div class="card">
        <div class="k">Make It Better</div>
        <div class="muted" style="margin-top:10px;">Actionable swaps to optimize this exact result.</div>
        ${optsHtml}
      </div>
      <div class="card">
        <div class="k">Verified Nutrition Matches</div>
        <div class="muted" style="margin-top:10px;">${escapeHtml(a.nutritional_truth?.source ?? "Dataset")}</div>
        ${aggLine}
        <div style="overflow-x:auto;-webkit-overflow-scrolling:touch;margin-top:10px;">
        <table>
          <thead>
            <tr>
              <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Ingredient</th>
              <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Src</th>
              <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Cal</th>
              <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Protein</th>
              <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Carbs</th>
              <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Fat</th>
              <th style="text-align:left;padding:8px 10px;border-bottom:1px solid #1f2937;">Serv</th>
            </tr>
          </thead>
          <tbody>${matchesHtml}</tbody>
        </table>
        </div>
      </div>
    </div>

    <div class="disclaimer">
      Educational estimates only. Not medical advice. Consult a healthcare professional for health decisions.
    </div>
  </div>
</body>
</html>`;
}

/** Compact diet-log export: meal context + matches + aggregates only. */
export function buildDietLogHtml(a: AnalysisResponse): string {
  const truth = a.nutritional_truth;
  const matches = truth?.dataset_matches ?? [];
  const agg = truth?.aggregates;
  const matchesHtml = matchesRowsHtml(matches);
  const meal = escapeHtml(a.meal_name ?? "Meal");
  const src = escapeHtml(truth?.source ?? "—");
  const dateStr = escapeHtml(new Date().toLocaleString());

  const macro = a.macro_breakdown;
  const macroBlock = `
    <div class="grid">
      <div class="card"><div class="k">Glycemic load (est.)</div><div class="v">${a.estimated_glycemic_load?.toFixed?.(1) ?? a.estimated_glycemic_load}</div></div>
      <div class="card"><div class="k">Carbs (g)</div><div class="v">${macro?.carbs_g ?? "—"}</div></div>
      <div class="card"><div class="k">Protein (g)</div><div class="v">${macro?.protein_g ?? "—"}</div></div>
      <div class="card"><div class="k">Fat (g)</div><div class="v">${macro?.fat_g ?? "—"}</div></div>
    </div>`;

  const aggBlock =
    agg && agg.match_count > 0
      ? `<div class="card" style="margin-top:14px;">
          <div class="k">Verified matches roll-up</div>
          <div class="muted" style="margin-top:8px;">Sums from dataset rows (see source).</div>
          <div class="muted" style="margin-top:8px;">
            ${agg.total_calories} kcal · P ${agg.total_protein_g}g · C ${agg.total_carbs_g}g · F ${agg.total_fat_g}g · ${agg.total_grams}g serving · ${agg.match_count} matches
          </div>
        </div>`
      : "";

  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Oxia Diet Log — ${meal}</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family:'Space Grotesk',sans-serif;background:#05070a;color:#e2e8f0;margin:0;padding:24px;box-sizing:border-box; }
    .wrap { max-width:720px;margin:0 auto; }
    .brand { color:#34d399;font-weight:800;font-size:18px; }
    .meal { font-size:clamp(20px,4vw,28px);font-weight:800;margin-top:8px;word-break:break-word; }
    .meta { color:#94a3b8;font-size:12px;margin-top:6px; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(140px,1fr)); gap:10px; margin-top:14px; }
    .card { border:1px solid #1f2937;border-radius:16px;padding:14px;background:#0b1220;min-width:0; }
    .k { font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#94a3b8;font-weight:700; }
    .v { margin-top:8px;font-size:22px;font-weight:800;color:#a7f3d0; }
    table { width:100%;border-collapse:collapse;font-size:12px;margin-top:10px; }
    .muted { color:#94a3b8;font-size:12px;line-height:1.5; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">Oxia · Diet log export</div>
    <div class="meal">${meal}</div>
    <div class="meta">${dateStr}</div>
    <div class="muted" style="margin-top:10px;">Source: ${src}</div>
    ${macroBlock}
    ${aggBlock}
    <div class="card" style="margin-top:14px;">
      <div class="k">Ingredient matches</div>
      <div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">
      <table>
        <thead>
          <tr>
            <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #1f2937;">Name</th>
            <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #1f2937;">Src</th>
            <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #1f2937;">Cal</th>
            <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #1f2937;">P</th>
            <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #1f2937;">C</th>
            <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #1f2937;">F</th>
            <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #1f2937;">g</th>
          </tr>
        </thead>
        <tbody>${matchesHtml}</tbody>
      </table>
      </div>
    </div>
    <p class="muted" style="margin-top:16px;">Educational estimates only. Not medical advice.</p>
  </div>
</body>
</html>`;
}

export function buildDietLogCsv(a: AnalysisResponse): string {
  return buildDietLogCsvStructured(a);
}

export function buildAnalysisJson(a: AnalysisResponse): string {
  return JSON.stringify(a, null, 2);
}

export function sanitizeFilenameBase(name: string, fallback = "oxia_export"): string {
  const t = name
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80);
  return t || fallback;
}

export function downloadTextFile(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
