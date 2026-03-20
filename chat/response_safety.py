from __future__ import annotations

from typing import Any


def ensure_three_suggestions(suggested_questions: list[str] | None, focus_metric: str) -> list[str]:
    suggestions = []
    for s in suggested_questions or []:
        if isinstance(s, str):
            cleaned = s.strip()
            if cleaned:
                suggestions.append(cleaned)

    suggestions = suggestions[:3]

    def fallback(metric: str) -> list[str]:
        m = (metric or "").lower()
        if m == "glucose":
            return [
                "When is the next glucose peak for this meal?",
                "How can I blunt the spike 15–30 minutes after eating?",
                "What should I schedule right after the peak?",
            ]
        if m == "inflammation":
            return [
                "What disruptors should I avoid next time for lower stress score?",
                "What swap lowers inflammation risk the most?",
                "When should I focus or rest after this meal?",
            ]
        if m == "performance":
            return [
                "When is my best deep work window after this meal?",
                "How long will brain fog risk last?",
                "What’s the best timing for focus based on this meal?",
            ]
        if m == "nutrition":
            return [
                "Which ingredient contributes most to fiber or micronutrient density?",
                "What swap increases nutrient density while reducing spike?",
                "How should I balance macros for better glucose response next time?",
            ]
        if m == "optimization":
            return [
                "Which single swap has the biggest measurable impact here?",
                "If I only change one ingredient, what should it be?",
                "How does this meal compare to a better version of itself?",
            ]
        return [
            f"How do I optimize {metric or 'this'} for my next meal?",
            "What should I do next based on this result?",
            "What’s the most important takeaway?",
        ]

    fb = fallback(focus_metric)
    while len(suggestions) < 3:
        suggestions.append(fb[len(suggestions)])
    return suggestions


def coerce_to_focus_metric(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    return "glucose"

