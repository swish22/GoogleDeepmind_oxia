"use client";

import { useId, useState } from "react";
import { formatCalories, formatNutritionNumber } from "../../lib/formatNutrition";
import type { NutritionalMatch } from "../../lib/types";

function SourceBadge({ m }: { m: NutritionalMatch }) {
  const id = m.data_source ?? "huggingface_maressay";
  const short =
    id === "open_food_facts" ? "OFF" : id === "usda_fdc" ? "USDA" : "HF";
  const cls =
    id === "open_food_facts"
      ? "border-amber-500/35 bg-amber-500/10 text-amber-100"
      : id === "usda_fdc"
        ? "border-sky-500/35 bg-sky-500/10 text-sky-100"
        : "border-lime-600/35 bg-lime-500/10 text-lime-100";
  return (
    <span
      className={`inline-flex shrink-0 rounded-md border px-1.5 py-0.5 text-[10px] font-bold tracking-wide ${cls}`}
      title={m.data_source_label ?? id}
    >
      {short}
    </span>
  );
}

const COLLAPSED_ROWS = 5;

/**
 * Ingredient rows — expandable when long; horizontal scroll preserved.
 */
export default function DietLogMatchesTable(props: { matches: NutritionalMatch[] }) {
  const { matches } = props;
  const [expanded, setExpanded] = useState(false);
  const panelId = useId();
  if (!matches.length) return null;

  const needsToggle = matches.length > COLLAPSED_ROWS;
  const visible = expanded || !needsToggle ? matches : matches.slice(0, COLLAPSED_ROWS);

  return (
    <div className="mt-1 min-w-0">
      <div
        id={`${panelId}-region`}
        role="region"
        aria-label="Ingredient nutrition matches"
        className={[
          "relative rounded-xl border border-lime-900/35 bg-zinc-950/40 shadow-[inset_0_1px_0_0_rgba(163,230,53,0.06)]",
          !expanded && needsToggle ? "max-h-[min(320px,55vh)] overflow-y-auto" : "",
        ].join(" ")}
      >
        <div className="overflow-x-auto [-webkit-overflow-scrolling:touch]">
          <table className="w-full min-w-[680px] border-separate border-spacing-0 text-left text-sm">
            <caption className="sr-only">Ingredient nutrition matches by data source</caption>
            <thead>
              <tr className="bg-zinc-950/98 text-[10px] uppercase tracking-wide text-lime-200/50">
                <th
                  scope="col"
                  className="border-b border-lime-900/25 px-3 py-3 pl-4 font-semibold sm:px-4"
                >
                  Ingredient
                </th>
                <th scope="col" className="border-b border-lime-900/25 px-2 py-3 font-semibold">
                  Src
                </th>
                <th scope="col" className="border-b border-lime-900/25 px-2 py-3 text-right font-semibold">
                  kcal
                </th>
                <th scope="col" className="border-b border-lime-900/25 px-2 py-3 text-right font-semibold">
                  P
                </th>
                <th scope="col" className="border-b border-lime-900/25 px-2 py-3 text-right font-semibold">
                  C
                </th>
                <th scope="col" className="border-b border-lime-900/25 px-2 py-3 text-right font-semibold">
                  F
                </th>
                <th scope="col" className="border-b border-lime-900/25 px-2 py-3 pr-4 text-right font-semibold sm:pr-4">
                  g
                </th>
              </tr>
            </thead>
            <tbody className="text-zinc-200">
              {visible.map((m, idx) => (
                <tr
                  key={`${m.name}-${idx}`}
                  className="transition-colors hover:bg-lime-950/20"
                >
                  <td className="max-w-[min(92vw,280px)] border-b border-zinc-800/50 px-3 py-2.5 align-top pl-4 sm:max-w-md sm:px-4">
                    <div className="break-words font-medium text-zinc-100">{m.name ?? "—"}</div>
                    {m.portion_note ? (
                      <div className="mt-1 break-words text-[11px] leading-snug text-zinc-500">
                        {m.portion_note}
                      </div>
                    ) : null}
                  </td>
                  <td className="border-b border-zinc-800/50 px-2 py-2.5 align-top whitespace-nowrap">
                    <SourceBadge m={m} />
                  </td>
                  <td className="border-b border-zinc-800/50 px-2 py-2.5 text-right font-mono text-[13px] tabular-nums text-zinc-100">
                    {formatCalories(m.calories)}
                  </td>
                  <td className="border-b border-zinc-800/50 px-2 py-2.5 text-right font-mono text-[13px] tabular-nums">
                    {formatNutritionNumber(m.protein)}
                  </td>
                  <td className="border-b border-zinc-800/50 px-2 py-2.5 text-right font-mono text-[13px] tabular-nums">
                    {formatNutritionNumber(m.carbs)}
                  </td>
                  <td className="border-b border-zinc-800/50 px-2 py-2.5 text-right font-mono text-[13px] tabular-nums">
                    {formatNutritionNumber(m.fat)}
                  </td>
                  <td className="border-b border-zinc-800/50 px-2 py-2.5 pr-4 text-right font-mono text-[13px] tabular-nums sm:pr-4">
                    {formatNutritionNumber(m.grams)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {needsToggle ? (
        <button
          type="button"
          id={`${panelId}-toggle`}
          aria-expanded={expanded}
          aria-controls={`${panelId}-region`}
          onClick={() => setExpanded((e) => !e)}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-lime-800/40 bg-lime-950/25 py-2 text-xs font-semibold text-lime-100/90 transition hover:border-lime-600/50 hover:bg-lime-950/40"
        >
          <span className="tabular-nums text-lime-200/70">
            {expanded ? "Collapse" : `Show all ${matches.length} rows`}
          </span>
          <span className="text-lime-400/80" aria-hidden>
            {expanded ? "▲" : "▼"}
          </span>
        </button>
      ) : (
        <p className="mt-2 text-center text-[10px] text-zinc-600">
          {matches.length} row{matches.length === 1 ? "" : "s"} · scroll horizontally on small screens
        </p>
      )}
    </div>
  );
}
