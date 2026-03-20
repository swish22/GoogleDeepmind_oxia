"use client";

import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiNutritionMatch, apiSaveMealSnapshot } from "../../lib/api";
import { formatCalories, formatNutritionNumber } from "../../lib/formatNutrition";
import { aggregatesFromMatches } from "../../lib/nutritionUtils";
import {
  buildAnalysisJson,
  buildDietLogCsv,
  buildDietLogHtml,
  downloadTextFile,
  sanitizeFilenameBase,
} from "../../lib/reportBuilders";
import type { AnalysisResponse, NutritionalMatch, NutritionalTruth } from "../../lib/types";
import DietLogMatchesTable from "./DietLogMatchesTable";
import { IconDocument, IconDownload } from "./OxiaIcons";
import { OxiaDatumPill, OxiaEyebrow, OxiaInset, OxiaPanel, OxiaScrollRow } from "./OxiaShell";

function MetricBand(props: { title: string; hint: string; children: ReactNode }) {
  return (
    <OxiaInset className="h-full">
      <div className="mb-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-500">{props.title}</div>
        <p className="mt-1 text-[11px] leading-relaxed text-zinc-600">{props.hint}</p>
      </div>
      <OxiaScrollRow>{props.children}</OxiaScrollRow>
    </OxiaInset>
  );
}

const CSV_HELP =
  "UTF-8 CSV: meal name, GL, photo macros, full ingredient table (HF / Open Food Facts / USDA), roll-ups, source breakdown.";

export default function DietLogPanel(props: {
  analysis: AnalysisResponse;
  onNutritionUpdate: (truth: NutritionalTruth) => void;
}) {
  const { analysis, onNutritionUpdate } = props;
  const truth = analysis.nutritional_truth;
  const matches = useMemo(
    () => (truth?.dataset_matches ?? []) as NutritionalMatch[],
    [truth?.dataset_matches],
  );

  const agg = useMemo(() => {
    if (truth?.aggregates) return truth.aggregates;
    if (matches.length) return aggregatesFromMatches(matches);
    return null;
  }, [truth?.aggregates, matches]);

  const mb = analysis.macro_breakdown;

  const defaultBase = useMemo(
    () => sanitizeFilenameBase((analysis.meal_name || "diet_log").replace(/\s+/g, "_")),
    [analysis.meal_name],
  );

  const [fileBase, setFileBase] = useState(defaultBase);
  const [saveLabel, setSaveLabel] = useState(analysis.meal_name || "My meal log");
  const [refreshBusy, setRefreshBusy] = useState(false);
  const [refreshErr, setRefreshErr] = useState<string | null>(null);
  const [saveDbBusy, setSaveDbBusy] = useState(false);
  const [saveDbErr, setSaveDbErr] = useState<string | null>(null);
  const [saveDbOk, setSaveDbOk] = useState<string | null>(null);

  useEffect(() => {
    setFileBase(sanitizeFilenameBase((analysis.meal_name || "diet_log").replace(/\s+/g, "_")));
    setSaveLabel(analysis.meal_name || "My meal log");
    setRefreshErr(null);
  }, [analysis.meal_id, analysis.meal_name]);

  const onRefreshMatches = async () => {
    const ing = (analysis.ingredients ?? []).filter(Boolean);
    if (!ing.length) {
      setRefreshErr("No ingredients on this analysis to match.");
      return;
    }
    setRefreshErr(null);
    setRefreshBusy(true);
    try {
      const data = await apiNutritionMatch(ing);
      const next: NutritionalTruth = {
        source: data.source,
        dataset_matches: data.dataset_matches,
        aggregates: data.aggregates,
        sources_breakdown: data.sources_breakdown,
      };
      onNutritionUpdate(next);
    } catch (e) {
      setRefreshErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRefreshBusy(false);
    }
  };

  const base = sanitizeFilenameBase(fileBase, defaultBase);
  const dateSuffix = new Date().toISOString().slice(0, 10);

  const downloadJson = () =>
    downloadTextFile(buildAnalysisJson(analysis), `${base}_${dateSuffix}.json`, "application/json");
  const downloadCsv = () =>
    downloadTextFile(buildDietLogCsv(analysis), `${base}_diet_log_${dateSuffix}.csv`, "text/csv");
  const downloadDietHtml = () =>
    downloadTextFile(buildDietLogHtml(analysis), `${base}_diet_${dateSuffix}.html`, "text/html");

  const onSaveDevice = async () => {
    setSaveDbBusy(true);
    setSaveDbErr(null);
    setSaveDbOk(null);
    try {
      await apiSaveMealSnapshot({
        meal_id: analysis.meal_id,
        analysis: { ...analysis, meal_name: saveLabel },
      });
      setSaveDbOk("Saved to your account.");
      window.dispatchEvent(new Event("oxia:saved-tests-changed"));
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.toLowerCase().includes("meal not found")) {
        setSaveDbErr("Saved test wasn’t found yet in the database. Re-run analysis and try saving again.");
        return;
      }
      setSaveDbErr(msg);
    } finally {
      setSaveDbBusy(false);
    }
  };

  const gl = analysis.estimated_glycemic_load;
  const glStr =
    typeof gl === "number" && Number.isFinite(gl) ? formatNutritionNumber(gl, 1) : String(gl ?? "—");

  const hasDatasetRows = matches.length > 0;

  return (
    <OxiaPanel
      accent="lime"
      eyebrow={<OxiaEyebrow accent="lime">Substantiation</OxiaEyebrow>}
      title="Nutrition evidence"
      description="Vision estimate (GL + macros) and database rows (HF Maressay, Open Food Facts, USDA). Exports merge both for a clean audit trail."
      headerRight={
        <button
          type="button"
          disabled={refreshBusy}
          onClick={() => void onRefreshMatches()}
          className="rounded-xl border border-lime-700/50 bg-lime-950/40 px-4 py-2.5 text-xs font-semibold text-lime-100 transition hover:border-lime-500/60 hover:bg-lime-950/55 disabled:opacity-50 sm:text-sm"
        >
          {refreshBusy ? "Syncing…" : "Sync database"}
        </button>
      }
    >
      {refreshErr ? (
        <div className="mb-4 rounded-xl border border-amber-500/35 bg-amber-950/25 px-3 py-2 text-xs text-amber-100">
          {refreshErr}
        </div>
      ) : null}

      <div className="grid min-w-0 grid-cols-1 gap-3 md:grid-cols-2">
        <MetricBand
          title="From meal photo (AI)"
          hint="Always shown — glycemic load and macros from vision, even before any database match."
        >
          <OxiaDatumPill label="GL" value={glStr} emphasize />
          <OxiaDatumPill label="Carbs" value={`${formatNutritionNumber(mb?.carbs_g)}g`} />
          <OxiaDatumPill label="Protein" value={`${formatNutritionNumber(mb?.protein_g)}g`} />
          <OxiaDatumPill label="Fat" value={`${formatNutritionNumber(mb?.fat_g)}g`} />
          <OxiaDatumPill label="Fiber" value={`${formatNutritionNumber(mb?.fiber_g)}g`} />
          <OxiaDatumPill label="F+V" value={`${formatNutritionNumber(mb?.fruits_veg_g)}g`} />
        </MetricBand>

        <MetricBand
          title="From ingredient database"
          hint={
            hasDatasetRows
              ? "Roll-up of matched rows — HF primary; OFF / USDA when used."
              : "No rows yet. Sync, or try clearer ingredient names (some items rarely hit Maressay)."
          }
        >
          <OxiaDatumPill
            label="Σ kcal"
            value={agg && hasDatasetRows ? formatCalories(agg.total_calories) : "—"}
            emphasize={hasDatasetRows}
          />
          <OxiaDatumPill
            label="Σ P"
            value={agg && hasDatasetRows ? `${formatNutritionNumber(agg.total_protein_g)}g` : "—"}
          />
          <OxiaDatumPill
            label="Σ C"
            value={agg && hasDatasetRows ? `${formatNutritionNumber(agg.total_carbs_g)}g` : "—"}
          />
          <OxiaDatumPill
            label="Σ F"
            value={agg && hasDatasetRows ? `${formatNutritionNumber(agg.total_fat_g)}g` : "—"}
          />
          <OxiaDatumPill label="Rows" value={hasDatasetRows ? String(matches.length) : "0"} />
        </MetricBand>
      </div>

      {truth?.sources_breakdown && Object.keys(truth.sources_breakdown).length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.entries(truth.sources_breakdown).map(([k, n]) => (
            <span
              key={k}
              className="rounded-lg border border-lime-800/45 bg-lime-950/35 px-3 py-1.5 text-[10px] font-semibold text-lime-100/90"
            >
              {k === "huggingface_maressay"
                ? "HF"
                : k === "open_food_facts"
                  ? "OFF"
                  : k === "usda_fdc"
                    ? "USDA"
                    : k}
              <span className="mx-1.5 text-lime-600/70">·</span>
              {String(n)}
            </span>
          ))}
        </div>
      ) : null}

      {hasDatasetRows ? (
        <div className="mt-6 min-w-0 border-t border-lime-900/25 pt-5">
          <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
            <div>
              <OxiaEyebrow accent="lime">Ingredient table</OxiaEyebrow>
              <p className="mt-2 max-w-xl text-[11px] leading-relaxed text-zinc-600">
                Compact by default; expand for the full evidence set. Scroll sideways on small screens.
              </p>
            </div>
          </div>
          <DietLogMatchesTable matches={matches} />
        </div>
      ) : (
        <OxiaInset className="mt-6 border-dashed border-lime-900/40 bg-lime-950/10">
          <p className="text-sm font-medium text-lime-100/95">No database rows yet</p>
          <p className="mt-2 text-xs leading-relaxed text-zinc-500">
            Photo metrics still apply. After sync, HF / OFF / USDA lines appear here and in CSV + JSON exports.
          </p>
          <button
            type="button"
            className="mt-4 text-sm font-semibold text-lime-300 transition hover:text-lime-200"
            onClick={() => void onRefreshMatches()}
          >
            Run database lookup →
          </button>
        </OxiaInset>
      )}

      <OxiaInset className="mt-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <label className="min-w-0 flex-1">
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
              Evidence export prefix
            </span>
            <input
              value={fileBase}
              onChange={(e) => setFileBase(e.target.value)}
              className="mt-1.5 w-full min-w-0 rounded-xl border border-zinc-800 bg-black/35 px-3 py-2.5 text-sm text-zinc-100 outline-none transition focus:border-lime-700/45 focus:ring-1 focus:ring-lime-500/15"
              autoComplete="off"
            />
          </label>
          <div className="min-w-0 sm:max-w-[280px] sm:shrink-0">
            <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-3">
            <button
              type="button"
              onClick={downloadJson}
              title="Structured analysis JSON"
              className="flex flex-col items-center gap-1 rounded-xl border border-zinc-700/85 bg-zinc-900/45 py-2.5 text-center transition hover:border-zinc-600 hover:bg-zinc-800/40"
            >
              <IconDocument className="h-5 w-5 text-zinc-400" />
              <span className="text-[10px] font-bold uppercase tracking-wide text-zinc-300">JSON</span>
            </button>
            <button
              type="button"
              title={CSV_HELP}
              onClick={downloadCsv}
              className="flex flex-col items-center gap-1 rounded-xl border border-lime-700/50 bg-lime-950/40 py-2.5 text-center transition hover:border-lime-500/55 hover:bg-lime-950/55"
            >
              <IconDownload className="h-5 w-5 text-lime-300/90" />
              <span className="text-[10px] font-bold uppercase tracking-wide text-lime-50">CSV</span>
            </button>
            <button
              type="button"
              title="Print-friendly HTML report"
              onClick={downloadDietHtml}
              className="flex flex-col items-center gap-1 rounded-xl border border-zinc-700/85 bg-zinc-900/45 py-2.5 text-center transition hover:border-zinc-600 hover:bg-zinc-800/40"
            >
              <span className="font-mono text-sm font-bold leading-none text-zinc-400" aria-hidden>{"</>"}</span>
              <span className="text-[10px] font-bold uppercase tracking-wide text-zinc-300">HTML</span>
            </button>
            </div>
          </div>
        </div>
        <div className="mt-4 border-t border-zinc-800/70 pt-3">
          <details className="group">
            <summary className="cursor-pointer list-none text-[11px] font-medium leading-relaxed text-zinc-600 hover:text-zinc-300">
              What’s included in the CSV?
            </summary>
            <p className="mt-2 whitespace-normal text-[11px] leading-relaxed text-zinc-600">{CSV_HELP}</p>
          </details>
        </div>
      </OxiaInset>

      <OxiaInset className="mt-4">
        <div className="flex flex-row items-center justify-between gap-2">
          <OxiaEyebrow accent="neutral">Save to account</OxiaEyebrow>
          <div className="text-[11px] text-zinc-600">
            Load & delete in the Capture panel after login.
          </div>
        </div>

        {saveDbErr ? (
          <div className="mt-3 rounded-xl border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-xs text-amber-100">
            {saveDbErr}
          </div>
        ) : null}
        {saveDbOk ? (
          <div className="mt-3 rounded-xl border border-emerald-500/30 bg-emerald-950/20 px-3 py-2 text-xs text-emerald-100">
            {saveDbOk}
          </div>
        ) : null}

        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-end">
          <label className="min-w-0 flex-1">
            <span className="text-xs text-zinc-500">Test name</span>
            <input
              value={saveLabel}
              onChange={(e) => setSaveLabel(e.target.value)}
              className="mt-1 w-full rounded-xl border border-zinc-800 bg-black/30 px-3 py-2.5 text-sm text-zinc-100 outline-none focus:border-zinc-600"
            />
          </label>
          <button
            type="button"
            disabled={saveDbBusy}
            onClick={() => void onSaveDevice()}
            className="shrink-0 rounded-xl bg-gradient-to-r from-sky-400 to-indigo-500 px-5 py-2.5 text-sm font-semibold text-zinc-950 shadow-md transition hover:brightness-105 disabled:opacity-60"
          >
            {saveDbBusy ? "Saving…" : "Save"}
          </button>
        </div>
      </OxiaInset>
    </OxiaPanel>
  );
}
