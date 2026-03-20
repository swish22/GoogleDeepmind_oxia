import type { AnalysisResponse } from "../../lib/types";
import { OxiaEyebrow, OxiaPanel } from "./OxiaShell";

export default function StatStrip(props: { analysis: AnalysisResponse }) {
  const a = props.analysis;
  const ga = a.glucose_architect;
  const ih = a.inflammation_hunter;

  const gl = Number(a.estimated_glycemic_load ?? 0);
  const nd = a.micro_nutrient_density ?? "—";
  const peak = Number(ga.peak_glucose ?? 0);
  const ss = Number(ih.stress_score ?? 0);

  const cells = [
    { label: "Glycemic load", value: Number.isFinite(gl) ? gl.toFixed(1) : "—", tone: "text-sky-300" as const },
    { label: "Nutrient density", value: String(nd), tone: "text-indigo-300" as const },
    { label: "Peak glucose", value: `${peak} mg/dL`, tone: "text-amber-300" as const },
    { label: "Stress score", value: `${ss}/10`, tone: "text-rose-300" as const },
  ];

  return (
    <OxiaPanel
      accent="neutral"
      eyebrow={<OxiaEyebrow accent="neutral">At a glance</OxiaEyebrow>}
      title="Core metrics"
      description="Four numbers the personas below interpret — same meal, one coherent story."
    >
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-zinc-800/70 bg-zinc-800/70 lg:grid-cols-4">
        {cells.map((c, i) => (
          <div
            key={c.label}
            className={`group relative bg-zinc-950/50 px-4 py-5 text-center transition-colors duration-200 hover:bg-zinc-900/50 sm:py-6 ${
              i > 0 ? "lg:border-l lg:border-zinc-800/60" : ""
            }`}
          >
            <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">{c.label}</div>
            <div
              className={`mt-2 break-words text-2xl font-bold tabular-nums tracking-tight sm:text-3xl ${c.tone}`}
            >
              {c.value}
            </div>
          </div>
        ))}
      </div>
    </OxiaPanel>
  );
}
