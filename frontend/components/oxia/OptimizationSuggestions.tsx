import type { AnalysisResponse } from "../../lib/types";
import { OxiaEyebrow, OxiaInset, OxiaPanel } from "./OxiaShell";

export default function OptimizationSuggestions(props: { analysis: AnalysisResponse }) {
  const a = props.analysis;
  const opts = (a.optimization_suggestions ?? []) as string[];
  const holistic = a.holistic_health_insight ?? "";

  return (
    <OxiaPanel
      accent="emerald"
      eyebrow={<OxiaEyebrow accent="emerald">Optimization</OxiaEyebrow>}
      title="Make it better"
      description="Synthesis plus a short list of high-leverage swaps — same voice as the rest of your dashboard."
    >
      <OxiaInset className="border-emerald-900/30 bg-emerald-950/15">
        <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-200/60">Synthesis</div>
        <p className="mt-2 text-sm leading-relaxed text-zinc-300">{holistic || "—"}</p>
      </OxiaInset>

      <OxiaInset className="mt-3 border-emerald-900/25">
        <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-200/60">
          Quantified swaps
        </div>
        {opts.length ? (
          <ul className="mt-3 space-y-2.5">
            {opts.slice(0, 3).map((o, idx) => (
              <li
                key={`opt-${idx}-${o.slice(0, 48)}`}
                className="flex gap-3 text-sm leading-relaxed text-zinc-200"
              >
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border border-emerald-500/25 bg-emerald-500/10 text-[11px] font-bold tabular-nums text-emerald-200">
                  {idx + 1}
                </span>
                <span className="min-w-0 pt-0.5">{o}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-zinc-500">No swap list returned for this meal.</p>
        )}
      </OxiaInset>
    </OxiaPanel>
  );
}
