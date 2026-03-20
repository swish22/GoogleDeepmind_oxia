"use client";

import { useEffect, useMemo, useState } from "react";
import { buildFullReportHtml, downloadTextFile, sanitizeFilenameBase } from "../../lib/reportBuilders";
import type { AnalysisResponse } from "../../lib/types";
import { OxiaEyebrow, OxiaPanel } from "./OxiaShell";

export default function ReportExport(props: { analysis: AnalysisResponse | null }) {
  const a = props.analysis;
  const defaultBase = useMemo(
    () => (a ? sanitizeFilenameBase((a.meal_name || "oxia_report").replace(/\s+/g, "_")) : "oxia_report"),
    [a],
  );
  const [fileBase, setFileBase] = useState(defaultBase);

  useEffect(() => {
    setFileBase(defaultBase);
  }, [defaultBase]);

  if (!a) return null;

  const base = sanitizeFilenameBase(fileBase, defaultBase);
  const dateSuffix = new Date().toISOString().slice(0, 10);
  const title = `${a.meal_name || "Meal"} — Oxia report`;

  const downloadFullHtml = () => {
    downloadTextFile(buildFullReportHtml(a, title), `${base}_report_${dateSuffix}.html`, "text/html");
  };

  return (
    <OxiaPanel
      accent="neutral"
      noOrb
      eyebrow={<OxiaEyebrow accent="neutral">Export</OxiaEyebrow>}
      title="Shareable report"
      description="One branded HTML report card for this meal. For row-level JSON, CSV, or diet HTML, use Nutrition evidence."
    >
      <label className="block min-w-0">
        <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">Report export prefix</span>
        <input
          value={fileBase}
          onChange={(e) => setFileBase(e.target.value)}
          className="mt-1.5 w-full min-w-0 rounded-xl border border-zinc-800 bg-black/30 px-3 py-2.5 text-sm text-zinc-100 outline-none transition focus:border-sky-500/40"
          placeholder="oxia_report"
          autoComplete="off"
        />
      </label>
      <button
        type="button"
        onClick={downloadFullHtml}
        className="mt-4 w-full rounded-xl bg-gradient-to-r from-sky-400 to-indigo-500 px-4 py-3 text-sm font-semibold text-zinc-950 shadow-lg shadow-sky-950/20 transition hover:brightness-105 sm:text-base"
      >
        Download full report (HTML)
      </button>
      <p className="mt-3 text-xs leading-relaxed text-zinc-600">
        Educational estimates only. Not medical advice.
      </p>
    </OxiaPanel>
  );
}
