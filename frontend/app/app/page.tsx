'use client';

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  apiAnalyzeMeal,
  apiDeleteMeal,
  apiGetRecentMeals,
  apiGetUiModelsConfig,
  apiHfWarmup,
  apiLoadMeal,
  apiLogout,
  apiPullOllamaStream,
} from "../../lib/api";
import { getToken } from "../../lib/auth";
import {
  clearDashboardSnapshot,
  loadDashboardSnapshot,
  saveDashboardSnapshot,
} from "../../lib/sessionSnapshot";
import type { AnalysisResponse } from "../../lib/types";
import Timeline3Hours from "../../components/oxia/Timeline3Hours";
import StatStrip from "../../components/oxia/StatStrip";
import PersonaCards from "../../components/oxia/PersonaCards";
import GlucoseChart from "../../components/oxia/GlucoseChart";
import MacroDonut from "../../components/oxia/MacroDonut";
import OptimizationSuggestions from "../../components/oxia/OptimizationSuggestions";
import DietLogPanel from "../../components/oxia/DietLogPanel";
import ChatPanel from "../../components/oxia/ChatPanel";
import ReportExport from "../../components/oxia/ReportExport";
import CameraCapture from "../../components/oxia/CameraCapture";
import ModelPrepareOverlay from "../../components/oxia/ModelPrepareOverlay";
import { dedupeReasoningModels, FALLBACK_REASONING_MODELS } from "../../lib/reasoningModels";
import { OxiaEyebrow, OxiaPanel } from "../../components/oxia/OxiaShell";

export default function DashboardPage() {
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
  const [reasoningModels, setReasoningModels] = useState<string[]>(FALLBACK_REASONING_MODELS);
  const [reasoningModel, setReasoningModel] = useState(FALLBACK_REASONING_MODELS[0]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [exitModal, setExitModal] = useState<"none" | "dashboard" | "photo">("none");
  const [showRestoreBanner, setShowRestoreBanner] = useState(false);
  const [prepare, setPrepare] = useState<{
    open: boolean;
    provider: "ollama" | "hf" | null;
    modelLabel: string;
    detail: string;
    progress?: number;
    error?: boolean;
  }>({ open: false, provider: null, modelLabel: "", detail: "" });

  const isChatOnlyModel = reasoningModel.startsWith("hf:");
  const modelPreparing = prepare.open && !prepare.error;

  const [savedMeals, setSavedMeals] = useState<AnalysisResponse[]>([]);
  const [savedBusy, setSavedBusy] = useState(false);
  const [savedErr, setSavedErr] = useState<string | null>(null);

  async function refreshSavedMeals() {
    setSavedBusy(true);
    setSavedErr(null);
    try {
      const list = await apiGetRecentMeals();
      // Defensive: backend historical/legacy rows may be missing `meal_id`.
      const sanitized = Array.isArray(list)
        ? list.filter((v): v is AnalysisResponse => Boolean(v) && typeof (v as any).meal_id === "string")
        : [];
      setSavedMeals(sanitized);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setSavedErr(msg);
    } finally {
      setSavedBusy(false);
    }
  }

  useEffect(() => {
    if (!getToken()) return;
    void refreshSavedMeals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const onChanged = () => {
      void refreshSavedMeals();
    };
    window.addEventListener("oxia:saved-tests-changed", onChanged);
    return () => window.removeEventListener("oxia:saved-tests-changed", onChanged);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const t = getToken();
    if (!t) router.push("/");
  }, [router]);

  useEffect(() => {
    apiGetUiModelsConfig()
      .then((c) => {
        const list = dedupeReasoningModels(c.reasoning_models ?? []);
        setReasoningModels(list.length ? list : FALLBACK_REASONING_MODELS);
        setReasoningModel((prev) =>
          list.includes(prev) ? prev : (list[0] ?? FALLBACK_REASONING_MODELS[0] ?? prev),
        );
      })
      .catch(() => {
        /* keep FALLBACK_REASONING_MODELS */
      });
  }, []);

  useEffect(() => {
    const snap = loadDashboardSnapshot();
    if (snap) setShowRestoreBanner(true);
  }, []);

  useEffect(() => {
    if (!reasoningModel.startsWith("ollama:") && !reasoningModel.startsWith("hf:")) {
      return () => {};
    }

    const ctrl = new AbortController();
    let alive = true;

    const run = async () => {
      if (reasoningModel.startsWith("ollama:")) {
        const name = reasoningModel.slice("ollama:".length);
        setPrepare({
          open: true,
          provider: "ollama",
          modelLabel: name,
          detail: "Connecting to Ollama…",
          progress: undefined,
          error: false,
        });
        try {
          await apiPullOllamaStream(
            name,
            (data) => {
              if (!alive) return;
              const st = String(data.status ?? "");
              const err = data.error != null ? String(data.error) : "";
              let pct: number | undefined;
              const completed = data.completed;
              const total = data.total;
              if (typeof completed === "number" && typeof total === "number" && total > 0) {
                pct = Math.min(100, Math.round((completed / total) * 100));
              }
              setPrepare((p) => ({
                ...p,
                detail: err ? err : st || p.detail,
                progress: pct ?? p.progress,
                error: st === "error" || Boolean(err),
              }));
            },
            ctrl.signal,
          );
          if (alive) {
            setPrepare({
              open: false,
              provider: null,
              modelLabel: "",
              detail: "",
              progress: undefined,
              error: false,
            });
          }
        } catch (e) {
          if (!alive) return;
          if (e instanceof DOMException && e.name === "AbortError") return;
          if (e instanceof Error && e.name === "AbortError") return;
          const msg = e instanceof Error ? e.message : String(e);
          setPrepare((p) => ({
            ...p,
            error: true,
            detail: msg,
          }));
        }
        return;
      }

      if (reasoningModel.startsWith("hf:")) {
        const id = reasoningModel.slice("hf:".length);
        setPrepare({
          open: true,
          provider: "hf",
          modelLabel: id,
          detail: "Warming up Hugging Face model (cold start / download)…",
          progress: undefined,
          error: false,
        });
        try {
          await apiHfWarmup(id, ctrl.signal);
          if (alive) {
            setPrepare({
              open: false,
              provider: null,
              modelLabel: "",
              detail: "",
              progress: undefined,
              error: false,
            });
          }
        } catch (e) {
          if (!alive) return;
          if (e instanceof DOMException && e.name === "AbortError") return;
          if (e instanceof Error && e.name === "AbortError") return;
          const msg = e instanceof Error ? e.message : String(e);
          setPrepare((p) => ({
            ...p,
            error: true,
            detail: msg,
          }));
        }
      }
    };

    void run();
    return () => {
      alive = false;
      ctrl.abort();
    };
  }, [reasoningModel]);

  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (analysis || file) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [analysis, file]);

  function performSignOutAndHome() {
    apiLogout();
    setAnalysis(null);
    setFile(null);
    setExitModal("none");
    router.push("/");
  }

  function onExitClick() {
    if (analysis) {
      setExitModal("dashboard");
      return;
    }
    if (file) {
      setExitModal("photo");
      return;
    }
    performSignOutAndHome();
  }

  function onSaveAndSignOut() {
    if (analysis) saveDashboardSnapshot(analysis, reasoningModel);
    performSignOutAndHome();
  }

  function onDiscardAndSignOut() {
    clearDashboardSnapshot();
    performSignOutAndHome();
  }

  function onRestoreSnapshot() {
    const snap = loadDashboardSnapshot();
    if (!snap) return;
    setReasoningModel(snap.reasoningModel);
    setAnalysis(snap.analysis);
    setShowRestoreBanner(false);
  }

  async function onAnalyze() {
    if (!file) return;
    if (isChatOnlyModel) {
      setError("HuggingFace models are chat-only in this build. Use Gemini or Ollama to analyze meal photos.");
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const res = await apiAnalyzeMeal({ file, reasoning_model: reasoningModel });
      setAnalysis(res);
      void refreshSavedMeals();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setBusy(false);
    }
  }

  async function onLoadSavedMeal(meal_id: string) {
    setError(null);
    setSavedErr(null);
    try {
      const snap = await apiLoadMeal(meal_id);
      setAnalysis(snap);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.toLowerCase().includes("meal not found")) {
        setSavedErr("That saved test is no longer available. Refresh the list and try again.");
        void refreshSavedMeals();
        return;
      }
      setSavedErr(msg);
    }
  }

  async function onDeleteSavedMeal(meal_id: string) {
    if (!confirm("Delete this saved metabolic test?")) return;
    setSavedBusy(true);
    setSavedErr(null);
    try {
      await apiDeleteMeal(meal_id);
      if (analysis?.meal_id === meal_id) setAnalysis(null);
      await refreshSavedMeals();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.toLowerCase().includes("meal not found")) {
        setSavedErr("That saved test was already removed. Refreshing…");
        void refreshSavedMeals();
        return;
      }
      setSavedErr(msg);
    } finally {
      setSavedBusy(false);
    }
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-zinc-950 text-zinc-100">
      <ModelPrepareOverlay
        open={prepare.open}
        provider={prepare.provider}
        modelLabel={prepare.modelLabel}
        detail={prepare.detail}
        progress={prepare.progress}
        error={prepare.error}
        onDismiss={() =>
          setPrepare({
            open: false,
            provider: null,
            modelLabel: "",
            detail: "",
            progress: undefined,
            error: false,
          })
        }
      />

      {exitModal !== "none" ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="exit-dialog-title"
        >
          <div className="w-full max-w-md rounded-2xl border border-zinc-700 bg-zinc-900 p-6 shadow-xl">
            {exitModal === "dashboard" ? (
              <>
                <h2 id="exit-dialog-title" className="text-lg font-bold text-zinc-100">
                  Sign out and leave?
                </h2>
                <p className="mt-2 text-sm text-zinc-400">
                  Save this dashboard to <span className="text-zinc-300">this device</span> so you can restore
                  metrics after signing in again. Signing out clears your session; it does not delete server data for
                  analyses you already ran.
                </p>
                <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:justify-end">
                  <button
                    type="button"
                    className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
                    onClick={() => setExitModal("none")}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm text-rose-200 hover:bg-rose-500/20"
                    onClick={onDiscardAndSignOut}
                  >
                    Discard &amp; sign out
                  </button>
                  <button
                    type="button"
                    className="rounded-xl bg-gradient-to-r from-sky-400 to-indigo-500 px-4 py-2 text-sm font-semibold text-zinc-950"
                    onClick={onSaveAndSignOut}
                  >
                    Save &amp; sign out
                  </button>
                </div>
              </>
            ) : (
              <>
                <h2 id="exit-dialog-title" className="text-lg font-bold text-zinc-100">
                  Photo not analyzed yet
                </h2>
                <p className="mt-2 text-sm text-zinc-400">
                  You selected a meal photo but haven’t run analysis. Sign out anyway, or stay to analyze first (then
                  you can save metrics on exit).
                </p>
                <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
                  <button
                    type="button"
                    className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
                    onClick={() => setExitModal("none")}
                  >
                    Stay
                  </button>
                  <button
                    type="button"
                    className="rounded-xl border border-zinc-600 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
                    onClick={performSignOutAndHome}
                  >
                    Sign out without analyzing
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      ) : null}

      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-sky-300/80">Oxia</div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-zinc-50 sm:text-3xl">Metabolic dashboard</h1>
            <p className="mt-1 max-w-lg text-sm leading-relaxed text-zinc-500">
              One layout: capture → metrics → personas → evidence → twin chat.
            </p>
          </div>
          <button
            type="button"
            className="shrink-0 rounded-xl border border-zinc-700/90 bg-zinc-950/50 px-4 py-2.5 text-sm font-medium text-zinc-200 transition hover:border-zinc-600 hover:bg-zinc-900"
            onClick={onExitClick}
          >
            Exit
          </button>
        </div>

        {showRestoreBanner && loadDashboardSnapshot() && !analysis ? (
          <div className="mb-6 flex flex-col gap-3 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-emerald-100/90">
              A <span className="font-semibold">saved dashboard</span> is on this device. Restore it to continue where
              you left off.
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-xl bg-emerald-500/20 px-4 py-2 text-sm font-semibold text-emerald-100 hover:bg-emerald-500/30"
                onClick={onRestoreSnapshot}
              >
                Restore
              </button>
              <button
                type="button"
                className="rounded-xl border border-emerald-500/30 px-4 py-2 text-sm text-emerald-200/80 hover:bg-emerald-500/10"
                onClick={() => setShowRestoreBanner(false)}
              >
                Dismiss
              </button>
            </div>
          </div>
        ) : null}

        <div className="grid min-w-0 grid-cols-1 gap-6 lg:grid-cols-3">
          <OxiaPanel
            accent="neutral"
            className="min-w-0 lg:col-span-1"
            eyebrow={<OxiaEyebrow accent="neutral">Capture</OxiaEyebrow>}
            title="Meal photo"
            description="Upload or use the camera, pick a model, then analyze. Chat uses the same model picker."
          >
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="text-xs font-semibold tracking-[0.14em] text-zinc-500">Option 1: Upload</div>
                <input
                  type="file"
                  accept="image/*"
                  className="block w-full text-sm text-zinc-300 file:mr-4 file:rounded-xl file:border-0 file:bg-sky-500/20 file:px-4 file:py-2 file:text-sm file:text-sky-200"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-4">
                <CameraCapture
                  onCaptured={(f) => {
                    setFile(f);
                  }}
                />
              </div>

              <label className="block">
                <div className="mb-1 text-sm text-zinc-400">AI model</div>
                <select
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-zinc-100 outline-none focus:border-sky-400"
                  value={reasoningModel}
                  onChange={(e) => setReasoningModel(e.target.value)}
                >
                  {reasoningModels.map((m, idx) => (
                    <option key={`${idx}:${m}`} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </label>

              {isChatOnlyModel ? (
                <div className="rounded-xl border border-amber-400/30 bg-amber-500/10 p-3 text-sm text-amber-200">
                  This model is chat-only. Use Gemini or Ollama for photo analysis.
                </div>
              ) : null}

              <div className="rounded-xl border border-zinc-800/70 bg-zinc-950/40 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-xs font-semibold tracking-[0.14em] text-zinc-500">Saved metabolic tests</div>
                    <div className="mt-1 text-xs leading-relaxed text-zinc-600">
                      {savedBusy
                        ? "Loading…"
                        : savedMeals.length
                          ? "Load or delete your account tests."
                          : "No saved tests yet. Run an analysis to create one."}
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled={savedBusy}
                    onClick={() => void refreshSavedMeals()}
                    className="shrink-0 rounded-lg border border-zinc-700 bg-zinc-900/30 px-2.5 py-1 text-[11px] font-medium text-zinc-200 transition hover:bg-zinc-800 disabled:opacity-60"
                  >
                    {savedBusy ? "…" : "Refresh"}
                  </button>
                </div>

                {savedErr ? (
                  <div className="mt-3 rounded-xl border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-xs text-amber-100">
                    {savedErr}
                  </div>
                ) : null}

                {savedMeals.length ? (
                  <ul className="mt-3 space-y-2">
                    {savedMeals.slice(0, 5).map((m) => {
                      const id = m.meal_id;
                      const name = m.meal_name ?? "Untitled";
                      return (
                        <li key={id} className="flex items-center justify-between gap-2">
                          <button
                            type="button"
                            className="min-w-0 flex-1 rounded-lg px-2 py-1 text-left transition hover:bg-zinc-800/40"
                            onClick={() => void onLoadSavedMeal(id)}
                          >
                            <div className="truncate text-xs font-semibold text-zinc-100">{name}</div>
                            <div className="truncate text-[11px] text-zinc-500">{id.slice(0, 10)}…</div>
                          </button>
                          <button
                            type="button"
                            disabled={savedBusy}
                            onClick={() => void onDeleteSavedMeal(id)}
                            className="rounded-lg p-2 text-rose-400/90 transition hover:bg-rose-500/10 hover:text-rose-300 disabled:opacity-60"
                            title="Delete saved test"
                          >
                            Delete
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </div>

              <button
                disabled={busy || !file || isChatOnlyModel || modelPreparing}
                onClick={onAnalyze}
                className="w-full rounded-xl bg-gradient-to-r from-sky-400 to-indigo-500 px-4 py-3 font-semibold text-zinc-950 disabled:opacity-60"
              >
                {busy ? "Analyzing..." : "Analyze meal"}
              </button>

              {error ? (
                <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
                  {error}
                </div>
              ) : null}

              <div className="text-xs leading-relaxed text-zinc-600">
                Educational estimates only. Not medical advice.
              </div>
            </div>
          </OxiaPanel>

          <main className="lg:col-span-2">
            {busy ? (
              <OxiaPanel accent="sky" className="mb-6" eyebrow={<OxiaEyebrow accent="sky">Working</OxiaEyebrow>} title="Analyzing your meal">
                <p className="text-sm leading-relaxed text-zinc-400">
                  Vision model is reading the plate, then we compose metrics, personas, and evidence in one pass.
                </p>
                <div className="mt-4 flex items-center gap-3">
                  <span className="inline-flex h-5 w-5 animate-spin rounded-full border-2 border-sky-400/25 border-t-sky-400" />
                  <span className="text-sm font-medium text-sky-200/90">Hold tight — almost there.</span>
                </div>
              </OxiaPanel>
            ) : null}
            {analysis ? (
              <div className="space-y-6">
                <OxiaPanel
                  accent="neutral"
                  eyebrow={<OxiaEyebrow accent="neutral">Meal</OxiaEyebrow>}
                  title={analysis?.meal_name ?? "Unknown meal"}
                  description="Ingredients detected from your photo — used everywhere below for a single coherent read."
                >
                  <div className="flex flex-wrap gap-2">
                    {(analysis?.ingredients ?? []).slice(0, 12).map((ing: string, idx: number) => (
                      <span
                        key={`ing-${idx}-${ing}`}
                        className="max-w-full break-words rounded-full border border-zinc-700/80 bg-zinc-950/50 px-3 py-1.5 text-xs font-medium text-zinc-200 transition hover:border-zinc-600"
                      >
                        {ing}
                      </span>
                    ))}
                  </div>
                </OxiaPanel>

                <Timeline3Hours analysis={analysis} />
                <StatStrip analysis={analysis} />
                <PersonaCards analysis={analysis} />

                <section className="grid min-w-0 grid-cols-1 gap-6 lg:grid-cols-2">
                  <div className="min-w-0">
                    <GlucoseChart analysis={analysis} />
                  </div>
                  <div className="min-w-0">
                    <MacroDonut analysis={analysis} />
                  </div>
                </section>

                <section className="grid min-w-0 grid-cols-1 gap-6 lg:grid-cols-2">
                  <div className="min-w-0">
                    <OptimizationSuggestions analysis={analysis} />
                  </div>
                  <div className="min-w-0">
                    <DietLogPanel
                      analysis={analysis}
                      onNutritionUpdate={(truth) =>
                        setAnalysis((prev) => (prev ? { ...prev, nutritional_truth: truth } : null))
                      }
                    />
                  </div>
                </section>

                <ChatPanel analysis={analysis} reasoningModel={reasoningModel} />

                <ReportExport analysis={analysis} />
              </div>
            ) : !busy ? (
              <OxiaPanel
                accent="neutral"
                noOrb
                eyebrow={<OxiaEyebrow accent="neutral">Dashboard</OxiaEyebrow>}
                title="Waiting for a meal"
                description="Upload a photo in the capture column. You’ll get metrics, three personas, charts, nutrition evidence, and chat — same visual system end to end."
              />
            ) : null}
          </main>
        </div>
      </div>
    </div>
  );
}

