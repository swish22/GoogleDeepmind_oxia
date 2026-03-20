"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AnalysisResponse } from "../../lib/types";
import { apiChat } from "../../lib/api";
import { OxiaEyebrow, OxiaPanel } from "./OxiaShell";

type FocusMetric = "glucose" | "inflammation" | "performance" | "nutrition" | "optimization";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

const METRICS: Array<{ key: FocusMetric; label: string }> = [
  { key: "glucose", label: "Glucose" },
  { key: "inflammation", label: "Inflammation" },
  { key: "performance", label: "Performance" },
  { key: "nutrition", label: "Nutrition" },
  { key: "optimization", label: "Optimization" },
];

/** High-priority starters (shown first). */
const DEFAULT_SUGGESTIONS: Record<FocusMetric, string[]> = {
  glucose: [
    "Next glucose peak — what time?",
    "How do I blunt the spike 15–30 minutes after eating?",
    "When should I schedule deep work after this meal?",
  ],
  inflammation: [
    "What disruptors should I avoid next time?",
    "Which swap lowers stress score most?",
    "What’s the best timing for calm recovery after this meal?",
  ],
  performance: [
    "When is my best deep work window?",
    "How long will brain fog risk last?",
    "What should I do next for maximum focus?",
  ],
  nutrition: [
    "Which ingredient drives fiber/nutrient density most?",
    "What swap improves nutrition without worsening glucose?",
    "How should I balance macros for a calmer response?",
  ],
  optimization: [
    "Which single swap has the biggest impact?",
    "If I change only one ingredient, what should it be?",
    "What’s the most important takeaway from this result?",
  ],
};

/** Lower-priority follow-ups — rotate in after a chip is used. */
const FOLLOWUP_SUGGESTIONS: Record<FocusMetric, string[]> = {
  glucose: [
    "Is my spike mostly from carbs, timing, or meal composition?",
    "What walk or movement timing helps this curve most?",
    "How does this meal compare to a lower-GL alternative?",
    "Any red flags in the glucose curve for the next 2 hours?",
    "What should I eat next to smooth the descent?",
  ],
  inflammation: [
    "Which ingredient most likely raised the stress score?",
    "How does sleep debt change this inflammation read?",
    "What anti-inflammatory add-on helps without spiking glucose?",
    "Should I prioritize protein or fiber next meal?",
    "What’s a realistic 7-day pattern if I repeat this lunch?",
  ],
  performance: [
    "When does cognitive risk peak vs recover on this curve?",
    "What’s the minimum break I need before intense focus?",
    "How does caffeine timing interact with this response?",
    "What snack stabilizes focus without a second spike?",
    "If I train today, when is the safest hard effort window?",
  ],
  nutrition: [
    "Which macro is most out of balance vs my goal?",
    "What whole-food swap preserves taste but adds fiber?",
    "How credible is the database match vs the photo estimate?",
    "Any micronutrient gaps implied by these ingredients?",
    "What portion change moves GL the most with least sacrifice?",
  ],
  optimization: [
    "What’s the second-best swap if I can’t change the first?",
    "How do I prioritize cost vs impact for these swaps?",
    "What would a ‘good enough’ version of this meal look like?",
    "Which change helps both glucose and inflammation?",
    "What one habit stacks best with this meal pattern?",
  ],
};

function dedupeStrings(items: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of items) {
    const s = (raw ?? "").trim();
    if (!s || seen.has(s)) continue;
    seen.add(s);
    out.push(s);
  }
  return out;
}

function buildPool(metric: FocusMetric, fromApi: string[]): string[] {
  return dedupeStrings([
    ...fromApi,
    ...DEFAULT_SUGGESTIONS[metric],
    ...FOLLOWUP_SUGGESTIONS[metric],
  ]);
}

function clampSlots(poolLen: number): [number | null, number | null, number | null] {
  return [
    poolLen > 0 ? 0 : null,
    poolLen > 1 ? 1 : null,
    poolLen > 2 ? 2 : null,
  ];
}

function nextPoolIndex(
  poolLen: number,
  consumed: Set<number>,
  slotIndices: [number | null, number | null, number | null],
  replaceSlot: number,
): number | null {
  const occupied = new Set<number>();
  for (let i = 0; i < 3; i++) {
    if (i === replaceSlot) continue;
    const v = slotIndices[i];
    if (v !== null) occupied.add(v);
  }
  const nums = slotIndices.filter((x): x is number => x !== null);
  const currentMax = nums.length ? Math.max(...nums) : -1;
  for (let j = currentMax + 1; j < poolLen; j++) {
    if (consumed.has(j)) continue;
    if (occupied.has(j)) continue;
    return j;
  }
  for (let j = 0; j < poolLen; j++) {
    if (consumed.has(j)) continue;
    if (occupied.has(j)) continue;
    return j;
  }
  return null;
}

function renderAnswer(text: string) {
  return (
    <div className="whitespace-pre-wrap leading-relaxed text-zinc-100">
      {text}
    </div>
  );
}

const STRIKE_MS = 320;

export default function ChatPanel(props: { analysis: AnalysisResponse | null; reasoningModel: string }) {
  const [focusMetric, setFocusMetric] = useState<FocusMetric>("glucose");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [pool, setPool] = useState<string[]>(() => buildPool("glucose", []));
  const [slotIndices, setSlotIndices] = useState<[number | null, number | null, number | null]>(() =>
    clampSlots(buildPool("glucose", []).length),
  );
  const [strikingSlot, setStrikingSlot] = useState<number | null>(null);
  const [enterSlot, setEnterSlot] = useState<number | null>(null);
  const strikeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const consumedRef = useRef<Set<number>>(new Set());

  const mealId = props.analysis?.meal_id;
  const canChat = Boolean(mealId);

  const resetSuggestionState = useCallback((metric: FocusMetric, apiPrefix: string[]) => {
    const p = buildPool(metric, apiPrefix);
    setPool(p);
    const empty = new Set<number>();
    consumedRef.current = empty;
    setSlotIndices(clampSlots(p.length));
    setStrikingSlot(null);
    setEnterSlot(null);
  }, []);

  useEffect(() => {
    setMessages([]);
    setQuestion("");
    setError(null);
  }, [props.analysis?.meal_id]);

  useEffect(() => {
    resetSuggestionState(focusMetric, []);
  }, [props.analysis?.meal_id, focusMetric, resetSuggestionState]);

  useEffect(
    () => () => {
      if (strikeTimer.current) clearTimeout(strikeTimer.current);
    },
    [],
  );

  const send = async (q: string) => {
    if (!mealId) return;
    const trimmed = q.trim();
    if (!trimmed) return;

    setError(null);
    setBusy(true);

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    try {
      const resp = await apiChat({
        meal_id: mealId,
        question: trimmed,
        focus_metric: focusMetric,
        use_history: true,
        reasoning_model: props.reasoningModel,
      });

      setMessages((prev) => [...prev, { role: "assistant", content: resp.answer }]);
      const apiQs = resp.suggested_questions ?? [];
      resetSuggestionState(focusMetric, apiQs);
      setQuestion("");
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setBusy(false);
    }
  };

  const onSuggestionSlotClick = (slot: number) => {
    if (!canChat || busy) return;
    const pi = slotIndices[slot];
    if (pi === null || pi >= pool.length) return;
    const text = pool[pi];
    if (!text) return;

    if (strikeTimer.current) clearTimeout(strikeTimer.current);
    setStrikingSlot(slot);

    strikeTimer.current = setTimeout(() => {
      consumedRef.current = new Set(consumedRef.current);
      consumedRef.current.add(pi);

      setSlotIndices((prev) => {
        const nextIdx = nextPoolIndex(pool.length, consumedRef.current, prev, slot);
        const copy: [number | null, number | null, number | null] = [...prev];
        copy[slot] = nextIdx;
        return copy;
      });

      setStrikingSlot(null);
      setEnterSlot(slot);
      void send(text);
      setTimeout(() => setEnterSlot(null), 400);
    }, STRIKE_MS);
  };

  const placeholder = useMemo(() => {
    switch (focusMetric) {
      case "glucose":
        return "Ask about your next glucose peak, curve, or spike-blunting moves…";
      case "inflammation":
        return "Ask about disruptors and how to lower the stress score…";
      case "performance":
        return "Ask about focus timing, deep work scheduling, or brain fog risk…";
      case "nutrition":
        return "Ask about macros, fiber, or ingredient-level nutrition mismatches…";
      case "optimization":
        return "Ask which swap gives the biggest impact and why…";
    }
  }, [focusMetric]);

  const slots = [0, 1, 2] as const;

  return (
    <OxiaPanel
      accent="sky"
      noOrb
      eyebrow={<OxiaEyebrow accent="sky">Live context</OxiaEyebrow>}
      title="Metabolic twin"
      description="Three ranked prompts refresh as you use them — grounded in your meal metrics."
      className="min-w-0"
      flushBody
    >
      {!canChat ? (
        <div className="mb-3 rounded-xl border border-zinc-700 bg-zinc-950/40 px-3 py-2 text-xs text-zinc-400">
          Upload a meal first
        </div>
      ) : null}

      <div className="relative flex flex-wrap gap-2">
        {METRICS.map((m) => (
          <button
            key={m.key}
            type="button"
            disabled={!canChat}
            onClick={() => setFocusMetric(m.key)}
            className={[
              "rounded-full border px-3 py-1.5 text-xs font-medium transition",
              focusMetric === m.key
                ? "border-sky-400/50 bg-sky-500/15 text-sky-100 shadow-[0_0_16px_-4px_rgba(56,189,248,0.4)]"
                : "border-zinc-800/90 bg-zinc-950/40 text-zinc-400 hover:border-zinc-700 hover:bg-zinc-900/50 hover:text-zinc-200",
            ].join(" ")}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="relative mt-4 max-h-[min(360px,50vh)] overflow-auto rounded-xl border border-zinc-800/80 bg-black/35 p-4 shadow-inner">
        {messages.length ? (
          <div className="space-y-4">
            {messages.map((m, idx) => (
              <div
                key={`${m.role}-${idx}`}
                className={m.role === "assistant" ? "rounded-xl border border-zinc-800/60 bg-zinc-900/40 p-3" : ""}
              >
                <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                  {m.role === "user" ? "You" : "Oxia twin"}
                </div>
                <div className={m.role === "user" ? "mt-1 text-sm text-zinc-100" : "mt-1"}>
                  {renderAnswer(m.content)}
                </div>
              </div>
            ))}
            {busy ? (
              <div className="flex items-center gap-2 text-sm text-sky-200/90">
                <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-sky-400/30 border-t-sky-400" />
                Grounding answer in your dashboard…
              </div>
            ) : null}
          </div>
        ) : (
          <div className="text-sm leading-relaxed text-zinc-500">
            Pick a metric, tap a <span className="text-zinc-400">smart prompt</span> below, or type your own. Used
            prompts strike through and the next-best question slides in.
          </div>
        )}
      </div>

      <div className="relative mt-4">
        <div className="mb-2 flex items-center justify-between gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
            Smart prompts
          </span>
          <span className="text-[10px] text-zinc-600">Tap to ask · auto-rotates</span>
        </div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          {slots.map((slot) => {
            const pi = slotIndices[slot];
            const text = pi !== null && pi < pool.length ? pool[pi] : null;
            const striking = strikingSlot === slot;
            const entering = enterSlot === slot;

            return (
              <button
                key={slot}
                type="button"
                disabled={!canChat || busy || !text || strikingSlot !== null}
                onClick={() => onSuggestionSlotClick(slot)}
                className={[
                  "group relative min-h-[4.25rem] rounded-xl border px-3 py-2.5 text-left text-xs leading-snug transition disabled:cursor-not-allowed disabled:opacity-40",
                  text
                    ? "border-zinc-700/80 bg-zinc-950/50 text-zinc-200 hover:border-sky-500/40 hover:bg-sky-500/5 hover:shadow-[0_0_20px_-8px_rgba(56,189,248,0.35)]"
                    : "border-dashed border-zinc-800/80 bg-zinc-950/20 text-zinc-600",
                  striking ? "scale-[0.98] border-zinc-600" : "",
                  entering ? "oxia-chip-in" : "",
                ].join(" ")}
              >
                <span className="mb-1 flex items-center justify-between gap-1">
                  <span className="font-mono text-[9px] font-bold text-zinc-600 tabular-nums">#{slot + 1}</span>
                  <span className="text-[9px] font-medium uppercase tracking-wider text-sky-500/70 opacity-0 transition group-hover:opacity-100 group-disabled:opacity-0">
                    Ask
                  </span>
                </span>
                <span
                  className={[
                    "block transition-all duration-300",
                    striking ? "text-zinc-500 line-through decoration-zinc-500 decoration-2" : "",
                  ].join(" ")}
                >
                  {text ?? "—"}
                </span>
                {striking ? (
                  <span className="mt-1 block text-[10px] font-medium text-sky-400/80">Sending…</span>
                ) : null}
              </button>
            );
          })}
        </div>
      </div>

      <div className="relative mt-4 flex flex-col gap-3 sm:flex-row">
        <input
          value={question}
          disabled={!canChat || busy}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={placeholder}
          className="min-w-0 flex-1 rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-sm text-zinc-100 outline-none ring-0 transition placeholder:text-zinc-600 focus:border-sky-500/50 focus:shadow-[0_0_0_1px_rgba(56,189,248,0.2)] disabled:opacity-60"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send(question);
            }
          }}
        />
        <button
          type="button"
          disabled={!canChat || busy || !question.trim()}
          onClick={() => void send(question)}
          className="shrink-0 rounded-xl bg-gradient-to-r from-sky-400 to-indigo-500 px-6 py-3 text-sm font-semibold text-zinc-950 shadow-lg shadow-sky-900/20 transition hover:brightness-105 disabled:opacity-60"
        >
          {busy ? "Sending…" : "Send"}
        </button>
      </div>

      {error ? (
        <div className="relative mt-3 rounded-xl border border-red-500/35 bg-red-950/30 p-3 text-sm text-red-200">
          {error}
        </div>
      ) : null}
    </OxiaPanel>
  );
}
