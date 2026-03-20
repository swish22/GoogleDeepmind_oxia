import type { ReactNode } from "react";

/** Shared “Oxia” surface language — one system across dashboard + substantiation. */
const ACCENTS = {
  neutral: {
    border: "border-zinc-800/80",
    orb: "bg-zinc-400/5",
    kicker: "text-zinc-500",
    dot: "bg-zinc-500/50",
  },
  sky: {
    border: "border-sky-500/25",
    orb: "bg-sky-400/10",
    kicker: "text-sky-200/80",
    dot: "bg-sky-400/80",
  },
  lime: {
    border: "border-lime-800/40",
    orb: "bg-lime-400/8",
    kicker: "text-lime-200/85",
    dot: "bg-lime-400/90",
  },
  emerald: {
    border: "border-emerald-500/25",
    orb: "bg-emerald-400/8",
    kicker: "text-emerald-200/80",
    dot: "bg-emerald-400/75",
  },
} as const;

export type OxiaAccent = keyof typeof ACCENTS;

export function OxiaEyebrow(props: { children: ReactNode; accent: OxiaAccent }) {
  const a = ACCENTS[props.accent];
  return (
    <div className="inline-flex w-fit items-center gap-2 rounded-full border border-zinc-800/70 bg-zinc-950/50 px-2.5 py-1">
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${a.dot}`} aria-hidden />
      <span className={`text-[10px] font-semibold uppercase tracking-[0.2em] ${a.kicker}`}>{props.children}</span>
    </div>
  );
}

export function OxiaPanel(props: {
  accent: OxiaAccent;
  eyebrow?: ReactNode;
  title?: ReactNode;
  description?: ReactNode;
  headerRight?: ReactNode;
  children?: ReactNode;
  className?: string;
  /** Skip decorative orb (e.g. nested charts). */
  noOrb?: boolean;
  /** Omit bottom padding on header slot (for full-bleed charts). */
  flushBody?: boolean;
}) {
  const a = ACCENTS[props.accent];
  const hasHeader = Boolean(props.eyebrow || props.title || props.description || props.headerRight);
  return (
    <section
      className={`relative min-w-0 overflow-hidden rounded-2xl border ${a.border} bg-zinc-900/40 p-5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] backdrop-blur-[2px] transition-shadow duration-300 hover:shadow-[0_0_0_1px_rgba(255,255,255,0.04)] sm:p-6 ${props.className ?? ""}`}
    >
      {!props.noOrb ? (
        <div
          className={`pointer-events-none absolute -right-28 -top-28 h-56 w-56 rounded-full ${a.orb} blur-3xl`}
          aria-hidden
        />
      ) : null}
      <div className="relative">
        {hasHeader ? (
          <header className="flex flex-col gap-3 border-b border-zinc-800/55 pb-4 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
            <div className="min-w-0 flex-1 space-y-2">
              {props.eyebrow}
              {props.title ? (
                <h3 className="text-lg font-semibold tracking-tight text-zinc-50 sm:text-xl">{props.title}</h3>
              ) : null}
              {props.description ? (
                <p className="max-w-2xl text-[13px] leading-relaxed text-zinc-500 sm:text-sm">{props.description}</p>
              ) : null}
            </div>
            {props.headerRight ? (
              <div className="flex shrink-0 flex-wrap items-center gap-2 sm:justify-end">{props.headerRight}</div>
            ) : null}
          </header>
        ) : null}
        {props.children != null && props.children !== false ? (
          <div className={hasHeader && !props.flushBody ? "mt-5" : hasHeader ? "mt-4" : ""}>{props.children}</div>
        ) : null}
      </div>
    </section>
  );
}

/** Nested metric band inside a panel. */
export function OxiaInset(props: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-xl border border-zinc-800/65 bg-zinc-950/35 p-4 shadow-inner shadow-black/20 sm:p-4 ${props.className ?? ""}`}
    >
      {props.children}
    </div>
  );
}

export function OxiaDatumPill(props: { label: string; value: string; emphasize?: boolean }) {
  return (
    <div
      className={`flex h-10 shrink-0 items-center gap-2.5 rounded-xl border px-3 transition-colors duration-200 ${
        props.emphasize
          ? "border-sky-500/30 bg-sky-950/40 hover:border-sky-500/45"
          : "border-zinc-800/75 bg-zinc-950/55 hover:border-zinc-700/80"
      }`}
    >
      <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-zinc-500">{props.label}</span>
      <span className="text-sm font-bold tabular-nums tracking-tight text-zinc-50 sm:text-[15px]">{props.value}</span>
    </div>
  );
}

export function OxiaScrollRow(props: { children: ReactNode }) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 pt-0.5 [-ms-overflow-style:none] [scrollbar-width:thin] [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-zinc-700/80">
      {props.children}
    </div>
  );
}

export type OxiaPersonaStripe = "sky" | "rose" | "violet";

const PERSONA_SKIN: Record<OxiaPersonaStripe, string> = {
  sky: "border-l-sky-400/85 bg-gradient-to-b from-sky-500/10 to-transparent",
  rose: "border-l-rose-400/85 bg-gradient-to-b from-rose-500/10 to-transparent",
  violet: "border-l-violet-400/85 bg-gradient-to-b from-violet-500/10 to-transparent",
};

export function OxiaPersonaCard(props: {
  stripe: OxiaPersonaStripe;
  monogram: string;
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
}) {
  const skin = PERSONA_SKIN[props.stripe];
  return (
    <article
      className={`relative min-w-0 overflow-hidden rounded-2xl border border-zinc-800/80 border-l-4 p-5 transition-colors duration-200 hover:border-zinc-700/90 sm:p-6 ${skin}`}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-zinc-700/60 bg-zinc-950/60 text-xs font-bold tracking-tight text-zinc-200"
          aria-hidden
        >
          {props.monogram}
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-zinc-500">{props.title}</h4>
          {props.subtitle ? <div className="mt-1.5">{props.subtitle}</div> : null}
        </div>
      </div>
      <div className="mt-4 space-y-3">{props.children}</div>
    </article>
  );
}
