"""
Extract the first JSON object from LLM text with tolerances for common invalid output.

Used by Ollama and HuggingFace providers (Gemini uses API-enforced JSON schema).
"""

from __future__ import annotations

import json
import re


def strip_trailing_commas_json(text: str) -> str:
    """
    Remove trailing commas before `}` or `]` (invalid in strict JSON, common in LLM output).

    Applied iteratively for nested structures. Does not parse strings; assumes LLM output
    is mostly well-formed aside from trailing commas.
    """
    prev: str | None = None
    while prev != text:
        prev = text
        text = re.sub(r",(\s*)([}\]])", r"\1\2", text)
    return text


def extract_first_json_object(text: str) -> str:
    """
    Return the substring of the first valid JSON object found in `text`.

    Handles: markdown fences, invalid `\\_` escapes, trailing commas, trailing junk after JSON.
    """
    if not text:
        return text

    cleaned = text.strip()
    cleaned = re.sub(r"^```[a-zA-Z0-9]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = re.sub(r"\\_", "_", cleaned)
    cleaned = strip_trailing_commas_json(cleaned)

    decoder = json.JSONDecoder()
    start = cleaned.find("{")
    while start != -1:
        fragment = cleaned[start:]
        fragment = strip_trailing_commas_json(fragment)
        try:
            _, end_idx = decoder.raw_decode(fragment)
            return fragment[:end_idx]
        except json.JSONDecodeError:
            start = cleaned.find("{", start + 1)

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        candidate = strip_trailing_commas_json(match.group(0))
        try:
            _, end_idx = decoder.raw_decode(candidate)
            return candidate[:end_idx]
        except json.JSONDecodeError:
            return candidate

    return cleaned
