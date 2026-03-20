import type { AnalysisResponse } from "../../lib/types";
import { OxiaEyebrow, OxiaPanel } from "./OxiaShell";

type TimelineNode = {
  timeMin: number;
  glucose: number;
  stateLabel: string;
  variant: "now" | "peak" | "focus" | "default";
};

function getGlucoseAt(curve: Array<{ time_mins: number; glucose_mg_dl: number }>, t: number) {
  const pt = curve.find((p) => p.time_mins === t);
  return pt?.glucose_mg_dl ?? 85;
}

export default function Timeline3Hours(props: { analysis: AnalysisResponse }) {
  const analysis = props.analysis;
  const ga = analysis.glucose_architect;
  const pg = analysis.performance_ghost;
  const deepWork = Number(pg.deep_work_window_mins ?? 0);
  const peakTime = Number(ga.spike_time_mins ?? 0);
  const curve = ga.glucose_curve as Array<{ time_mins: number; glucose_mg_dl: number }>;

  const times = [0, 30, 60, 90, 120, 180];
  const nodes: TimelineNode[] = times.map((t) => {
    const glucose = getGlucoseAt(curve, t);
    let stateLabel = "Recovering";
    let variant: TimelineNode["variant"] = "default";

    if (t === 0) {
      stateLabel = "Digesting";
      variant = "now";
    } else if (t < peakTime) {
      stateLabel = "Glucose rising";
    } else if (t === peakTime) {
      stateLabel = "Peak glucose";
      variant = "peak";
    } else if (deepWork > 0 && t <= peakTime + deepWork) {
      stateLabel = "Deep focus window";
      variant = "focus";
    }

    return { timeMin: t, glucose, stateLabel, variant };
  });

  const momentText =
    deepWork >= 45
      ? `You'll have a ${deepWork}-minute deep work window. Schedule your hardest work now.`
      : deepWork > 0
        ? `Focus should hold for ~${deepWork} minutes. Start your hardest task soon.`
        : `Blood sugar peaks around ${peakTime} minutes. Align your work with recovery.`;

  return (
    <OxiaPanel
      accent="sky"
      eyebrow={<OxiaEyebrow accent="sky">Timeline</OxiaEyebrow>}
      title="Your next 3 hours"
      description={momentText}
    >
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3 lg:grid-cols-6">
        {nodes.map((n, idx) => {
          const border =
            n.variant === "now"
              ? "border-sky-500/40 bg-sky-500/5"
              : n.variant === "peak"
                ? "border-rose-500/40 bg-rose-500/5"
                : n.variant === "focus"
                  ? "border-emerald-500/40 bg-emerald-500/5"
                  : "border-zinc-800/80 bg-zinc-950/30";
          const text =
            n.variant === "now"
              ? "text-sky-200"
              : n.variant === "peak"
                ? "text-rose-200"
                : n.variant === "focus"
                  ? "text-emerald-200"
                  : "text-zinc-200";

          return (
            <div
              key={`tl-${n.timeMin}-${n.variant}-${idx}`}
              className={`rounded-xl border px-3 py-3 transition-transform duration-200 hover:scale-[1.02] sm:py-3.5 ${border}`}
            >
              <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-zinc-500">{n.timeMin} min</div>
              <div className={`mt-1.5 text-lg font-bold tabular-nums sm:text-xl ${text}`}>{n.glucose} mg/dL</div>
              <div className="mt-1 text-[11px] leading-snug text-zinc-500">{n.stateLabel}</div>
            </div>
          );
        })}
      </div>
    </OxiaPanel>
  );
}
