import { getToken, setToken, clearToken, TokenBundle } from "./auth";
import type { AnalysisResponse, ChatResponse, NutritionMatchApiResponse } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** Prefer FastAPI `detail` string over raw JSON in UI error toasts. */
async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const j = JSON.parse(text) as { detail?: unknown };
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail)) {
      return j.detail
        .map((item) => {
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: string }).msg);
          }
          return String(item);
        })
        .join("; ");
    }
  } catch {
    // not JSON
  }
  return text;
}

/** On 401 with an Authorization header, clear stored JWT so the UI can return to login. */
async function assertOk(res: Response, revokeSessionOn401: boolean): Promise<void> {
  if (res.ok) return;
  const msg = await readErrorMessage(res);
  if (revokeSessionOn401 && res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
    throw new Error(
      "Session expired or isn’t valid for this server. Please log in again. (If you changed JWT settings, this is expected.)",
    );
  }
  throw new Error(msg);
}

export async function apiRegister(username: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  await assertOk(res, false);
  const data: TokenBundle = await res.json();
  setToken(data.access_token);
  return data;
}

export async function apiLogin(username: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  await assertOk(res, false);
  const data: TokenBundle = await res.json();
  setToken(data.access_token);
  return data;
}

export function apiLogout() {
  clearToken();
}

export type UiModelsConfig = {
  reasoning_models: string[];
  default_ollama_vision: string;
  ollama_base_url: string;
};

/** Public: suggested model dropdown + env-driven Ollama vision default. */
export async function apiGetUiModelsConfig(): Promise<UiModelsConfig> {
  const res = await fetch(`${API_BASE_URL}/config/models`);
  if (!res.ok) throw new Error(await readErrorMessage(res));
  return res.json() as Promise<UiModelsConfig>;
}

/**
 * Stream NDJSON from Ollama pull (same as `ollama pull <name>`).
 * Parses each line as JSON and forwards to onLine.
 */
export async function apiPullOllamaStream(
  name: string,
  onLine: (data: Record<string, unknown>) => void,
  signal?: AbortSignal,
): Promise<void> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  const res = await fetch(`${API_BASE_URL}/providers/ollama/pull`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
    signal,
  });

  await assertOk(res, true);

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body from Ollama pull stream.");

  const dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
    for (const line of lines) {
      const t = line.trim();
      if (!t) continue;
      try {
        onLine(JSON.parse(t) as Record<string, unknown>);
      } catch {
        onLine({ status: "pulling", raw: t });
      }
    }
  }
  const tail = buf.trim();
  if (tail) {
    try {
      onLine(JSON.parse(tail) as Record<string, unknown>);
    } catch {
      onLine({ status: "pulling", raw: tail });
    }
  }
}

/** Wait until HF Inference API model is loadable (wait_for_model). */
export async function apiHfWarmup(hfModel: string, signal?: AbortSignal): Promise<void> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  const res = await fetch(`${API_BASE_URL}/providers/hf/warmup`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ hf_model: hfModel }),
    signal,
  });

  await assertOk(res, true);
}

export async function apiAnalyzeMeal(opts: {
  file: File;
  reasoning_model: string;
}): Promise<AnalysisResponse> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  const fd = new FormData();
  fd.append("file", opts.file);
  fd.append("reasoning_model", opts.reasoning_model);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/analyze_meal`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
  } catch {
    throw new Error(
      `Failed to reach backend at ${API_BASE_URL}. Start FastAPI on port 8000, then try again.`
    );
  }

  await assertOk(res, true);
  return res.json();
}

export async function apiChat(opts: {
  meal_id: string;
  question: string;
  focus_metric?: string | null;
  use_history: boolean;
  reasoning_model?: string | null;
}): Promise<ChatResponse> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        meal_id: opts.meal_id,
        question: opts.question,
        focus_metric: opts.focus_metric ?? null,
        use_history: opts.use_history,
        reasoning_model: opts.reasoning_model ?? null,
      }),
    });
  } catch {
    throw new Error(
      `Failed to reach backend at ${API_BASE_URL}. Start FastAPI, then try the chat again.`
    );
  }

  await assertOk(res, true);
  return res.json();
}

/** Re-fetch HuggingFace dataset matches for the current ingredient list (no full re-analysis). */
export async function apiNutritionMatch(ingredients: string[]): Promise<NutritionMatchApiResponse> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/nutrition/match`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ ingredients }),
    });
  } catch {
    throw new Error(`Failed to reach backend at ${API_BASE_URL}.`);
  }

  await assertOk(res, true);
  return res.json() as Promise<NutritionMatchApiResponse>;
}

export async function apiGetRecentMeals(): Promise<AnalysisResponse[]> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  const res = await fetch(`${API_BASE_URL}/meals/recent`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  await assertOk(res, true);
  return (await res.json()) as AnalysisResponse[];
}

export async function apiLoadMeal(meal_id: string): Promise<AnalysisResponse> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  const res = await fetch(`${API_BASE_URL}/meals/${meal_id}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  await assertOk(res, true);
  return (await res.json()) as AnalysisResponse;
}

export async function apiDeleteMeal(meal_id: string): Promise<void> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  const res = await fetch(`${API_BASE_URL}/meals/${meal_id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  await assertOk(res, true);
}

export async function apiSaveMealSnapshot(opts: {
  meal_id: string;
  analysis: AnalysisResponse;
}): Promise<void> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated.");

  const res = await fetch(`${API_BASE_URL}/meals/${opts.meal_id}/snapshot`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(opts.analysis),
  });
  await assertOk(res, true);
}

