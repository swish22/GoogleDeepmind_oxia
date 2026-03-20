"use client";

type Props = {
  open: boolean;
  provider: "ollama" | "hf" | null;
  modelLabel: string;
  detail: string;
  progress?: number;
  error?: boolean;
  onDismiss: () => void;
};

export default function ModelPrepareOverlay(props: Props) {
  if (!props.open) return null;

  const title =
    props.provider === "hf"
      ? "Preparing Hugging Face model"
      : props.provider === "ollama"
        ? "Preparing Ollama model"
        : "Preparing model";

  const sub =
    props.provider === "ollama"
      ? "Same as running `ollama pull` — layers download in the background."
      : "Warming up inference (HF may cold-start or download weights).";

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
      role="alertdialog"
      aria-busy={!props.error}
      aria-labelledby="model-prepare-title"
    >
      <div className="w-full max-w-md rounded-2xl border border-sky-500/25 bg-gradient-to-b from-zinc-900 to-zinc-950 p-6 shadow-2xl shadow-sky-500/10">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-10 w-10 shrink-0 rounded-xl bg-sky-500/20 text-center text-xl leading-10">
            {props.error ? "⚠️" : "⬇️"}
          </div>
          <div className="min-w-0 flex-1">
            <h2 id="model-prepare-title" className="text-lg font-bold text-zinc-50">
              {title}
            </h2>
            <p className="mt-1 font-mono text-sm text-sky-200/90">{props.modelLabel}</p>
            <p className="mt-2 text-sm text-zinc-400">{sub}</p>
          </div>
        </div>

        {!props.error ? (
          <div className="mt-5">
            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-sky-400 to-indigo-500 transition-all duration-300 ease-out"
                style={{
                  width: `${typeof props.progress === "number" ? Math.max(8, props.progress) : 36}%`,
                }}
              />
            </div>
            <p className="mt-3 line-clamp-3 text-xs text-zinc-500">{props.detail}</p>
            <p className="mt-2 text-[11px] text-zinc-600">
              You can switch models again to cancel this download (aborts the current request).
            </p>
          </div>
        ) : (
          <div className="mt-5 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-100/90">
            {props.detail}
          </div>
        )}

        {props.error ? (
          <button
            type="button"
            className="mt-6 w-full rounded-xl bg-zinc-100 px-4 py-3 text-sm font-semibold text-zinc-900 hover:bg-white"
            onClick={props.onDismiss}
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </div>
  );
}
