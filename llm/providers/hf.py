from __future__ import annotations

import json
from typing import Any

import requests

from llm.json_extract import extract_first_json_object
from llm.providers.base import LLMProvider
from models import ChatResponse, FlatMealAnalysisResult


SYSTEM_PROMPT_CHAT = """
You are Oxia's in-context metric chatbot.
Use ONLY the provided context_packet values.
Answer ONLY the user's question with <=3 short lines.
Do not give medical diagnosis. Educational only.
If the question is not answerable from the context, reply with ONE sentence asking a relevant question.
Return JSON: {answer, suggested_questions, focus_metric}.
suggested_questions: exactly 3 short, metric-relevant follow-ups.
focus_metric must be exactly one of: glucose, inflammation, performance, nutrition, optimization.
"""


class HFProvider(LLMProvider):
    supports_vision = False

    def __init__(self, *, hf_token: str | None = None, base_url: str | None = None) -> None:
        self.hf_token = hf_token
        self.base_url = base_url or "https://api-inference.huggingface.co/models"

    def generate_meal_analysis(self, *, image: Any, reasoning_model: str) -> FlatMealAnalysisResult:
        raise RuntimeError("HuggingFace provider is chat-only in this lightweight build. Use Gemini or Ollama for meal photo analysis.")

    def chat(self, *, context_packet: dict[str, Any], question: str, reasoning_model: str) -> ChatResponse:
        # reasoning_model is expected to be a full HF model id, e.g. "mistralai/Mistral-7B-Instruct-v0.3"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        prompt = (
            SYSTEM_PROMPT_CHAT
            + f"\ncontext_packet={context_packet}\nquestion={question}\n"
            + "Return ONLY JSON."
        )

        # Many HF endpoints accept {inputs: "..."}.
        r = requests.post(
            f"{self.base_url}/{reasoning_model}",
            headers=headers,
            json={"inputs": prompt, "options": {"wait_for_model": True}},
            timeout=180,
        )
        if r.status_code in (401, 403):
            raise RuntimeError(
                "HuggingFace request was unauthorized. Set `HF_TOKEN` in `.env` (or use Ollama/Gemini)."
            )
        r.raise_for_status()

        data = r.json()
        # HF sometimes returns {"generated_text": "..."} in different schemas
        if isinstance(data, list) and data and "generated_text" in data[0]:
            raw = data[0]["generated_text"]
        else:
            raw = json.dumps(data)

        extracted = extract_first_json_object(raw)
        return ChatResponse.model_validate_json(extracted)

