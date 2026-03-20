"""Reasoning / vision model IDs exposed to the UI (no secrets)."""

from __future__ import annotations

import os


def normalized_ollama_env_model() -> str:
    raw = (os.getenv("OXIA_OLLAMA_VISION_MODEL") or "llava:latest").strip()
    if raw.lower().startswith("ollama:"):
        raw = raw[7:].strip()
    return raw or "llava:latest"


def default_gemini_vision_model() -> str:
    """Prefer Gemini 2.x Flash for latency; override with OXIA_GEMINI_VISION_MODEL."""
    return (os.getenv("OXIA_GEMINI_VISION_MODEL") or "gemini-2.0-flash").strip() or "gemini-2.0-flash"


def build_reasoning_models_list() -> list[str]:
    """Dashboard dropdown: Gemini 2.0 first, then env Ollama, then alternates."""
    tag = f"ollama:{normalized_ollama_env_model()}"
    primary_gemini = default_gemini_vision_model()
    candidates = [
        primary_gemini,
        "gemini-2.5-flash",
        tag,
        "ollama:llava-llama3:latest",
        "hf:google/flan-t5-large",
        "gemini-1.5-flash",
    ]
    seen: set[str] = set()
    out: list[str] = []
    for m in candidates:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
