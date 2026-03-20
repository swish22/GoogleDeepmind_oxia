from __future__ import annotations

import base64
import json
from typing import Any

import requests

from llm.flat_meal_coerce import flat_meal_from_llm_json_string
from llm.json_extract import extract_first_json_object
from llm.providers.base import LLMProvider
from models import ChatResponse, FlatMealAnalysisResult


SYSTEM_PROMPT = """
You are Oxia's metabolic intelligence: a clinical AI that predicts how food will affect the human body.
Analyze the provided food image with precision. Speak as the expert personas—confident, first-person, predictive.

VOICE: Start your glucose insight with "I'm the Glucose Architect." and your inflammation insight with "I'm the Inflammation Hunter."

Return ONLY a valid JSON object matching Oxia's `FlatMealAnalysisResult` schema.
Do not wrap it in markdown. Do not add any extra keys.

Required top-level keys and types:
- meal_name: string
- ingredients: string[]
- estimated_glycemic_load: number (0-100)
- micro_nutrient_density: string ('High','Moderate','Low')
- macro_carbs_g: number
- macro_protein_g: number
- macro_fat_g: number
- macro_fiber_g: number
- macro_fruits_veg_g: number

- ga_peak_glucose: int
- ga_spike_time_mins: int
- ga_glucose_0: int
- ga_glucose_15: int
- ga_glucose_30: int
- ga_glucose_45: int
- ga_glucose_60: int
- ga_glucose_90: int
- ga_glucose_120: int
- ga_glucose_150: int
- ga_glucose_180: int
- ga_architect_insight: string (first-person; must start with "I'm the Glucose Architect.")

- ih_stress_score: int (1-10)
- ih_hidden_disruptors: string[] (empty list if none)
- ih_disruptors_detected: boolean
- ih_hunter_insight: string (first-person; must start with "I'm the Inflammation Hunter.")

- pg_brain_fog_risk: string ('Low','Medium','High')
- pg_deep_work_window_mins: int
- pg_ghost_insight: string (first-person)
- cs_state_label: string
- cs_state_emoji: string
- cs_duration_mins: int

- holistic_health_insight: string (2-3 sentences)
- optimization_suggestions: string[] (EXACTLY 2-3 items)

Each item in optimization_suggestions must be formatted like:
"Replace X with Y → benefit" (quantitative when possible).
"""


def _ollama_error_detail(r: requests.Response) -> str:
    try:
        j = r.json()
        if isinstance(j, dict) and j.get("error"):
            return str(j["error"])
    except Exception:
        pass
    return (r.text or r.reason or f"HTTP {r.status_code}")[:800]


class OllamaProvider(LLMProvider):
    supports_vision = True

    def __init__(self, *, base_url: str = "http://localhost:11434") -> None:
        # Prefer IPv4 loopback — on some Windows setups "localhost" resolves oddly vs Ollama.
        self.base_url = base_url.rstrip("/")

    def _api(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _list_local_model_names(self) -> list[str]:
        try:
            r = requests.get(self._api("/api/tags"), timeout=8)
            if not r.ok:
                return []
            data = r.json()
            return [str(m.get("name", "")).strip() for m in data.get("models", []) if m.get("name")]
        except Exception:
            return []

    def resolve_model_name(self, model: str) -> str:
        """
        Map requested name to a tag Ollama actually has (e.g. llava <-> llava:latest).
        """
        want = (model or "").strip()
        if not want:
            return want
        names = self._list_local_model_names()
        if not names:
            return want

        by_lower = {n.lower(): n for n in names}

        if want in names:
            return want
        if want.lower() in by_lower:
            return by_lower[want.lower()]

        base = want.split(":")[0].strip()
        if not base:
            return want

        # Prefer llava:latest-style match for base name "llava"
        for suffix in (":latest", ""):
            candidate = f"{base}{suffix}" if suffix else base
            if candidate.lower() in by_lower:
                return by_lower[candidate.lower()]
            if candidate in names:
                return candidate

        for n in names:
            nl = n.lower()
            if nl == base.lower() or nl.startswith(base.lower() + ":"):
                return n

        return want

    def ensure_model(self, model: str) -> str:
        """
        Ensure the model exists locally; return the resolved tag to pass to /api/chat.
        """
        resolved = self.resolve_model_name(model)
        try:
            r = requests.post(self._api("/api/show"), json={"name": resolved}, timeout=12)
            if r.status_code == 200:
                return resolved
        except Exception:
            pass

        try:
            r = requests.get(self._api("/api/show"), params={"name": resolved}, timeout=12)
            if r.status_code == 200:
                return resolved
        except Exception:
            pass

        try:
            # Block until pull completes (no stream=) so the next chat call can run.
            requests.post(self._api("/api/pull"), json={"name": resolved}, timeout=600)
        except Exception:
            pass

        return resolved

    def _chat_non_stream(
        self,
        *,
        model: str,
        user_text: str,
        images_b64: list[str] | None = None,
        timeout: int = 240,
    ) -> str:
        """
        Use /api/chat (required for reliable vision on LLaVA; /api/generate often mis-handles images).
        """
        msg: dict[str, Any] = {"role": "user", "content": user_text}
        if images_b64:
            msg["images"] = images_b64

        r = requests.post(
            self._api("/api/chat"),
            json={"model": model, "messages": [msg], "stream": False},
            timeout=timeout,
        )
        if not r.ok:
            raise RuntimeError(f"Ollama: {_ollama_error_detail(r)}")

        data = r.json()
        if isinstance(data, dict):
            m = data.get("message")
            if isinstance(m, dict) and m.get("content"):
                return str(m["content"])
            if data.get("response"):
                return str(data["response"])
        return json.dumps(data)

    def generate_meal_analysis(self, *, image: Any, reasoning_model: str) -> FlatMealAnalysisResult:
        resolved = self.ensure_model(reasoning_model)

        buf = None
        try:
            import io

            buf = io.BytesIO()
            image.save(buf, format="JPEG")
            img_bytes = buf.getvalue()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
        finally:
            if buf is not None:
                buf.close()

        prompt = SYSTEM_PROMPT + "\nUser input: Analyze this meal photo and output the JSON."

        try:
            raw = self._chat_non_stream(
                model=resolved,
                user_text=prompt,
                images_b64=[b64],
                timeout=240,
            )
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Ollama vision request failed: {e}") from e

        extracted = extract_first_json_object(raw)
        return flat_meal_from_llm_json_string(extracted)

    def chat(self, *, context_packet: dict[str, Any], question: str, reasoning_model: str) -> ChatResponse:
        resolved = self.ensure_model(reasoning_model)
        prompt = (
            "You are Oxia's in-context metric chatbot.\n"
            "Use ONLY the JSON values in context_packet.\n"
            "Answer ONLY the user's question, concisely and action-oriented.\n"
            "Return JSON: {answer, suggested_questions, focus_metric}.\n"
            "suggested_questions must be 3 items.\n"
        )
        prompt = (
            prompt
            + f"\ncontext_packet={context_packet}\nquestion={question}\n"
            + "focus_metric must never be null."
        )

        raw = self._chat_non_stream(model=resolved, user_text=prompt, images_b64=None, timeout=120)
        extracted = extract_first_json_object(raw)
        return ChatResponse.model_validate_json(extracted)

