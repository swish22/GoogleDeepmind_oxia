import type { ReactNode } from "react";
import type { AnalysisResponse } from "../../lib/types";
import { OxiaPersonaCard } from "./OxiaShell";

export default function PersonaCards(props: { analysis: AnalysisResponse }) {
  const a = props.analysis;
  const ga = a.glucose_architect;
  const ih = a.inflammation_hunter;
  const pg = a.performance_ghost;
  const cs = pg.cognitive_state;

  const peak = Number(ga.peak_glucose ?? 0);
  const spikeTime = Number(ga.spike_time_mins ?? 0);
  const architectInsight = ga.architect_insight ?? "";

  const disruptors = (ih.hidden_disruptors ?? []) as string[];
  const disruptorsDetected = Boolean(ih.disruptors_detected);
  const stress = Number(ih.stress_score ?? 0);
  const hunterInsight = ih.hunter_insight ?? "";

  const brainFogRisk: string = String(pg.brain_fog_risk ?? "Low");
  const deepWork = Number(pg.deep_work_window_mins ?? 0);
  const ghostInsight = pg.ghost_insight ?? "";
  const stateLabel = String(cs.state_label ?? "—");
  const stateEmoji = String(cs.state_emoji ?? "");
  const durationMins = Number(cs.duration_mins ?? 0);

  const brainColor =
    brainFogRisk === "Low"
      ? "text-emerald-300"
      : brainFogRisk === "Medium"
        ? "text-amber-300"
        : "text-rose-300";

  const stat = (label: string, value: ReactNode, valueClass = "text-zinc-100") => (
    <div className="flex items-baseline justify-between gap-2 border-b border-zinc-800/50 py-2 last:border-0">
      <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-zinc-500">{label}</span>
      <span className={`text-right text-sm font-semibold tabular-nums sm:text-base ${valueClass}`}>{value}</span>
    </div>
  );

  return (
    <div className="grid min-w-0 grid-cols-1 gap-4 lg:grid-cols-3">
      <OxiaPersonaCard
        stripe="sky"
        monogram="GA"
        title="Glucose architect"
        subtitle={
          <p className="text-sm text-zinc-400">
            Peak <span className="font-semibold text-sky-300">{spikeTime} min</span>
            <span className="text-zinc-600"> · </span>
            <span className="font-bold tabular-nums text-sky-200">{peak} mg/dL</span>
          </p>
        }
      >
        <p className="text-sm leading-relaxed text-zinc-400">{architectInsight}</p>
      </OxiaPersonaCard>

      <OxiaPersonaCard
        stripe="rose"
        monogram="IH"
        title="Inflammation hunter"
        subtitle={
          disruptorsDetected ? (
            <span className="inline-flex rounded-full border border-rose-500/35 bg-rose-500/10 px-2.5 py-0.5 text-xs font-medium text-rose-200">
              Disruptors flagged
            </span>
          ) : (
            <span className="inline-flex rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-200">
              Clear scan
            </span>
          )
        }
      >
        {stat("Stress score", `${stress}/10`, "text-rose-300")}
        {disruptorsDetected && disruptors.length ? (
          <div className="flex flex-wrap gap-1.5">
            {disruptors.slice(0, 6).map((d, idx) => (
              <span
                key={`dis-${idx}-${d.slice(0, 40)}`}
                className="rounded-lg border border-zinc-700/80 bg-zinc-950/40 px-2.5 py-1 text-xs text-amber-100/90"
              >
                {d}
              </span>
            ))}
          </div>
        ) : null}
        <p className="text-sm leading-relaxed text-zinc-400">{hunterInsight}</p>
      </OxiaPersonaCard>

      <OxiaPersonaCard
        stripe="violet"
        monogram="PG"
        title="Performance ghost"
        subtitle={
          <p className="text-sm text-zinc-400">
            <span className="text-lg">{stateEmoji}</span>{" "}
            <span className="font-semibold text-violet-200">{stateLabel}</span>
            <span className="text-zinc-600"> · </span>
            <span className="tabular-nums text-zinc-500">{durationMins} min state</span>
          </p>
        }
      >
        {stat("Deep work window", `${deepWork} min`, "text-violet-200")}
        <div className="flex items-baseline justify-between gap-2 border-b border-zinc-800/50 py-2">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-zinc-500">Brain fog risk</span>
          <span className={`text-sm font-semibold sm:text-base ${brainColor}`}>{brainFogRisk}</span>
        </div>
        <p className="pt-1 text-sm leading-relaxed text-zinc-400">{ghostInsight}</p>
      </OxiaPersonaCard>
    </div>
  );
}
