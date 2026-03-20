from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from llm.providers.base import LLMProvider
from models import ChatResponse, FlatMealAnalysisResult


SYSTEM_PROMPT = """
You are Oxia's metabolic intelligence: a clinical AI that predicts how food will affect the human body.
Analyze the provided food image with precision. Speak as the expert personas—confident, first-person, predictive.

VOICE: Each insight should feel like a specialist speaking directly to the user. Start with "I'm the Glucose Architect." or "I'm the Inflammation Hunter." Be punchy and predictive: "This will..." not "This may...".

1. Meal Identification
   - meal_name, ingredients list.

2. Macro Breakdown
   - macro_carbs_g, macro_protein_g, macro_fat_g, macro_fiber_g, macro_fruits_veg_g.

3. Glucose Architect (ga_*)
   - estimated_glycemic_load (0-100).
   - 180-min curve: 0, 15, 30, 45, 60, 90, 120, 150, 180 minutes. Fasting ~85 mg/dL.
   - ga_peak_glucose, ga_spike_time_mins.
   - ga_architect_insight: First-person, predictive. "I'm the Glucose Architect. This meal will peak your blood sugar at [N] mg/dL in [M] minutes. [One concrete tip to blunt the spike if applicable]."

4. Inflammation Hunter (ih_*)
   - ih_stress_score (1-10), ih_hidden_disruptors list, ih_disruptors_detected.
   - ih_hunter_insight: First-person. "I'm the Inflammation Hunter. [Verdict: clean/detected disruptors]. [One specific observation]."

5. Performance Ghost (pg_*, cs_*)
   - cs_state_label (Peak Flow / Steady Focus / Post-Meal Dip / Brain Fog Alert), cs_state_emoji, cs_duration_mins.
   - pg_deep_work_window_mins, pg_brain_fog_risk.
   - pg_ghost_insight: First-person. "I'm the Performance Ghost. [State] for [N] minutes. Schedule your hardest work in the next [M] minutes."

6. holistic_health_insight
   - 2-3 sentences. One bold prediction + one actionable takeaway.

7. optimization_suggestions
   - EXACTLY 2-3 swaps. Format: "Replace X with Y → benefit". Be quantitative. Examples:
     "Swap white rice for cauliflower rice → -35% glycemic load"
     "Add 20g protein (chicken/egg) → +45 min focus window"
     "Drizzle olive oil instead of ranch → -2 stress score"
  
Return ONLY valid JSON matching the schema. No markdown.
"""


class GeminiProvider(LLMProvider):
    supports_vision = True
    def __init__(
        self,
        *,
        api_key: str | None,
        fallback_chain: list[str] | None = None,
    ) -> None:
        self._client = None
        self._api_key = api_key
        self._fallback_chain = fallback_chain or [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
        ]

        if api_key:
            try:
                self._client = genai.Client(api_key=api_key)
            except Exception:
                self._client = None

    @property
    def configured(self) -> bool:
        return self._client is not None

    def generate_meal_analysis(self, *, image: Any, reasoning_model: str) -> FlatMealAnalysisResult:
        if self._client is None:
            raise RuntimeError("Gemini client not configured (missing GEMINI_API_KEY).")

        candidates = [reasoning_model] + [m for m in self._fallback_chain if m != reasoning_model]
        last_err: Exception | None = None

        for candidate in candidates:
            try:
                response = self._client.models.generate_content(
                    model=candidate,
                    contents=[SYSTEM_PROMPT, image],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=FlatMealAnalysisResult,
                        temperature=0.15,
                    ),
                )

                return FlatMealAnalysisResult.model_validate_json(response.text)
            except Exception as e:  # pragma: no cover (provider errors are runtime-only)
                last_err = e

                # The upstream API errors can be noisy; retry fallback models on 404/not-found.
                msg = str(e)
                if "404" not in msg and "NOT_FOUND" not in msg:
                    raise

        raise last_err or RuntimeError("Gemini analysis failed for all candidates.")

    def chat(
        self,
        *,
        context_packet: dict[str, Any],
        question: str,
        reasoning_model: str,
    ) -> ChatResponse:
        if self._client is None:
            raise RuntimeError("Gemini client not configured (missing GEMINI_API_KEY).")

        # Keep chat prompts short (in-context budget) and strictly grounded.
        chat_prompt = (
            "You are Oxia's in-context metric chatbot.\n"
            "Use ONLY the values from context_packet.\n"
            "Rules:\n"
            "- Answer ONLY what the user asks.\n"
            "- If the question is not answerable from context_packet, respond with ONE sentence:\n"
            "  \"I can only answer questions about this meal's selected metric predictions. Ask a relevant question like: ...\"\n"
            "- Never mention unrelated topics.\n"
            "- Do not give medical diagnosis; educational only.\n"
            "- Format answer in <=3 short lines.\n"
            "Return JSON: {answer, suggested_questions, focus_metric}.\n"
            "focus_metric must be exactly one of: glucose, inflammation, performance, nutrition, optimization. Never null.\n"
            "suggested_questions: 3 short, specific follow-ups relevant to the same context."
        )

        candidates = [reasoning_model] + [m for m in self._fallback_chain if m != reasoning_model]
        last_err: Exception | None = None

        for candidate in candidates:
            try:
                contents = [
                    chat_prompt,
                    f"context_packet={context_packet}",
                    f"question={question}",
                ]
                response = self._client.models.generate_content(
                    model=candidate,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ChatResponse,
                        temperature=0.2,
                    ),
                )
                return ChatResponse.model_validate_json(response.text)
            except Exception as e:  # pragma: no cover
                last_err = e
                msg = str(e)
                if "404" not in msg and "NOT_FOUND" not in msg:
                    raise

        raise last_err or RuntimeError("Gemini chat failed for all candidates.")

