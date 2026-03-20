"use client";

import { useMemo } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { AnalysisResponse } from "../../lib/types";
import { OxiaEyebrow, OxiaPanel } from "./OxiaShell";

type MacroRow = {
  name: string;
  value: number;
  fill: string;
  pct: number;
};

const PALETTE: Record<string, string> = {
  Carbs: "#fbbf24",
  Protein: "#38bdf8",
  Fat: "#fb7185",
  Fiber: "#4ade80",
  "Fruits & Veg": "#c4b5fd",
};

function formatG(n: number): string {
  if (!Number.isFinite(n)) return "—";
  if (n >= 100) return n.toFixed(0);
  if (n >= 10) return n.toFixed(1);
  return n.toFixed(1);
}

function CustomTooltip(props: {
  active?: boolean;
  payload?: Array<{ payload: MacroRow }>;
}) {
  if (!props.active || !props.payload?.length) return null;
  const row = props.payload[0].payload;
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-950/95 px-3 py-2 text-xs shadow-xl backdrop-blur-sm">
      <div className="font-semibold text-zinc-100">{row.name}</div>
      <div className="mt-1 font-mono tabular-nums text-zinc-300">
        {formatG(row.value)} g
        <span className="text-zinc-500"> · </span>
        <span className="text-sky-300">{row.pct}%</span>
        <span className="text-zinc-500"> of macro mass</span>
      </div>
    </div>
  );
}

export default function MacroDonut(props: { analysis: AnalysisResponse }) {
  const a = props.analysis;
  const mb = a.macro_breakdown ?? {};

  const { rows, total, hasRealData } = useMemo(() => {
    const raw = [
      { name: "Carbs", value: Math.max(0, Number(mb.carbs_g ?? 0)) },
      { name: "Protein", value: Math.max(0, Number(mb.protein_g ?? 0)) },
      { name: "Fat", value: Math.max(0, Number(mb.fat_g ?? 0)) },
      { name: "Fiber", value: Math.max(0, Number(mb.fiber_g ?? 0)) },
      { name: "Fruits & Veg", value: Math.max(0, Number(mb.fruits_veg_g ?? 0)) },
    ];
    const filtered = raw.filter((d) => d.value > 0);
    const sum = filtered.reduce((s, d) => s + d.value, 0);
    const withPct: MacroRow[] = filtered.map((d) => ({
      name: d.name,
      value: d.value,
      fill: PALETTE[d.name] ?? "#64748b",
      pct: sum > 0 ? Math.round((d.value / sum) * 1000) / 10 : 0,
    }));
    return {
      rows: withPct,
      total: sum,
      hasRealData: withPct.length > 0,
    };
  }, [mb.carbs_g, mb.protein_g, mb.fat_g, mb.fiber_g, mb.fruits_veg_g]);

  const chartData: MacroRow[] = hasRealData
    ? rows
    : [{ name: "No macro data", value: 1, fill: "#3f3f46", pct: 100 }];

  return (
    <OxiaPanel
      accent="neutral"
      noOrb
      eyebrow={<OxiaEyebrow accent="neutral">Composition</OxiaEyebrow>}
      title="Macro distribution"
      description="Grams from vision analysis. Percentages are shares of total mass in this chart (including fiber and produce)."
    >
      <div className="relative mx-auto w-full max-w-[320px] sm:max-w-none">
        <div className="h-[220px] w-full min-h-[200px] sm:h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(56,189,248,0.06)" }} />
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                innerRadius="58%"
                outerRadius="88%"
                paddingAngle={hasRealData ? 2.5 : 0}
                strokeWidth={2}
                stroke="#09090b"
                isAnimationActive
                animationDuration={600}
              >
                {chartData.map((entry, i) => (
                  <Cell key={`pie-${i}-${entry.name}`} fill={entry.fill} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="pointer-events-none absolute inset-0 flex items-center justify-center pt-1">
          <div className="text-center">
            <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-500">
              Total (shown)
            </div>
            <div className="mt-0.5 text-2xl font-bold tabular-nums tracking-tight text-zinc-50 sm:text-3xl">
              {hasRealData ? `${formatG(total)}` : "—"}
              <span className="text-base font-semibold text-zinc-500 sm:text-lg">g</span>
            </div>
            {!hasRealData ? (
              <div className="mt-1 max-w-[9rem] text-[10px] leading-snug text-zinc-500">
                Run meal analysis for macro estimates
              </div>
            ) : (
              <div className="mt-1 text-[10px] text-zinc-600">by mass</div>
            )}
          </div>
        </div>
      </div>

      {hasRealData ? (
        <ul className="mt-4 space-y-2.5 border-t border-zinc-800/80 pt-4">
          {rows.map((r, i) => (
            <li
              key={`macro-row-${i}-${r.name}`}
              className="flex min-w-0 items-center gap-3 rounded-xl border border-zinc-800/60 bg-zinc-950/30 px-3 py-2.5"
            >
              <span
                className="h-3 w-3 shrink-0 rounded-full shadow-[0_0_10px_rgba(0,0,0,0.4)] ring-2 ring-black/40"
                style={{ backgroundColor: r.fill }}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
                <div className="break-words text-sm font-medium text-zinc-200">{r.name}</div>
                <div className="mt-0.5 font-mono text-xs tabular-nums text-zinc-500">
                  {formatG(r.value)} g
                </div>
              </div>
              <div className="shrink-0 text-right">
                <div className="text-lg font-bold tabular-nums text-sky-300">{r.pct}%</div>
                <div className="text-[10px] uppercase tracking-wide text-zinc-600">share</div>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </OxiaPanel>
  );
}
