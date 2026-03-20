from pydantic import BaseModel, Field
from typing import Any, List, Literal

class FlatMealAnalysisResult(BaseModel):
    meal_name: str = Field(description="A short, descriptive name for the identified meal (e.g., 'Grilled Salmon with Brown Rice').")
    ingredients: List[str] = Field(description="List of identified ingredients.")
    estimated_glycemic_load: float = Field(description="Estimated glycemic load of the meal (0-100 scale).")
    micro_nutrient_density: str = Field(description="Overall micronutrient profile: 'High', 'Moderate', or 'Low'.")
    
    # MacroBreakdown
    macro_carbs_g: float = Field(description="Estimated grams of total carbohydrates.")
    macro_protein_g: float = Field(description="Estimated grams of protein.")
    macro_fat_g: float = Field(description="Estimated grams of fat.")
    macro_fiber_g: float = Field(description="Estimated grams of dietary fiber.")
    macro_fruits_veg_g: float = Field(description="Estimated grams of fruits and vegetables.")
    
    # GlucoseArchitect
    ga_peak_glucose: int = Field(description="Predicted peak blood sugar in mg/dL.")
    ga_spike_time_mins: int = Field(description="Minutes until predicted peak glucose.")
    ga_glucose_0: int = Field(description="Glucose at 0 mins")
    ga_glucose_15: int = Field(description="Glucose at 15 mins")
    ga_glucose_30: int = Field(description="Glucose at 30 mins")
    ga_glucose_45: int = Field(description="Glucose at 45 mins")
    ga_glucose_60: int = Field(description="Glucose at 60 mins")
    ga_glucose_90: int = Field(description="Glucose at 90 mins")
    ga_glucose_120: int = Field(description="Glucose at 120 mins")
    ga_glucose_150: int = Field(description="Glucose at 150 mins")
    ga_glucose_180: int = Field(description="Glucose at 180 mins")
    ga_architect_insight: str = Field(description="One-sentence insight on how the meal affects glucose.")
    
    # InflammationHunter
    ih_stress_score: int = Field(description="Estimated systemic stress score 1-10 (10 is high).")
    ih_hidden_disruptors: List[str] = Field(description="List of flagged hidden disruptors found in the actual ingredients (e.g., 'oxidized seed oils', 'refined sugars'). Empty list if none found.")
    ih_disruptors_detected: bool = Field(description="True if any actual metabolic disruptors were detected in the listed ingredients, False otherwise.")
    ih_hunter_insight: str = Field(description="One-sentence insight on inflammatory risk.")
    
    # PerformanceGhost
    pg_brain_fog_risk: str = Field(description="Risk level of brain fog: 'Low', 'Medium', or 'High'.")
    pg_deep_work_window_mins: int = Field(description="Estimated optimal duration for deep cognitive work in minutes post-meal.")
    pg_ghost_insight: str = Field(description="One-sentence insight mapping the meal to neurotransmitter response and cognitive performance.")
    
    # CognitiveState
    cs_state_label: str = Field(description="The cognitive state label, e.g. 'Peak Flow', 'Steady Focus', 'Post-Meal Dip', 'Brain Fog Alert'.")
    cs_state_emoji: str = Field(description="A single representative emoji for this cognitive state.")
    cs_duration_mins: int = Field(description="Estimated duration of this cognitive state in minutes.")
    
    holistic_health_insight: str = Field(description="A 2-3 sentence medically-grounded synthesis of the overall meal quality, its metabolic impact, and one actionable recommendation to optimize it.")
    
    # Optimization suggestions — concrete swaps to improve the meal
    optimization_suggestions: List[str] = Field(
        default_factory=list,
        description="Exactly 2-3 specific, actionable swaps to improve this meal. Each format: 'Replace X with Y → benefit'. Be quantitative (e.g. '→ -25% glycemic load', '→ +45 min focus'). Examples: 'Swap white rice for cauliflower rice → -35% glycemic load', 'Add 20g nuts → extends focus window 30 min'."
    )


class ChatRequest(BaseModel):
    meal_id: str = Field(description="Meal id from the analysis step.")
    question: str = Field(description="User question to answer using meal context.")
    focus_metric: Literal["glucose", "inflammation", "performance", "nutrition", "optimization"] | None = Field(
        default=None,
        description="Optional: force the chatbot to focus on a specific metric category."
    )
    use_history: bool = Field(default=True, description="Whether to use recent logged meal history in the context packet.")
    reasoning_model: str | None = Field(
        default=None,
        description="Optional: which Gemini model to use for this chat turn.",
    )


class ChatResponse(BaseModel):
    answer: str = Field(description="Concise, grounded answer with concrete next steps.")
    suggested_questions: List[str] = Field(
        description="Relevant follow-up questions for this specific result (ideally 3).",
    )
    focus_metric: str = Field(
        default="glucose",
        description="The metric category used to ground the answer.",
    )


class AuthRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=6, max_length=200)


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OllamaPullRequest(BaseModel):
    """Ollama model name to pull (e.g. llava:latest). Same as `ollama run llava` / `ollama pull llava`."""

    name: str = Field(min_length=1, max_length=200, description="Model name, e.g. llava:latest")


class HFWarmupRequest(BaseModel):
    """HuggingFace Inference API model id (without hf: prefix)."""

    hf_model: str = Field(min_length=1, max_length=200, description="e.g. google/flan-t5-large")


class UiModelsConfigResponse(BaseModel):
    reasoning_models: list[str]
    default_ollama_vision: str
    ollama_base_url: str


class NutritionMatchRequest(BaseModel):
    """Ingredient strings for multi-source nutrition matching (HF Maressay + open fallbacks)."""

    ingredients: list[str] = Field(
        min_length=1,
        max_length=40,
        description="Detected or user-edited ingredient names",
    )


class NutritionMatchResponse(BaseModel):
    """Nutritional matches + rolled-up macros (multi-source)."""

    source: str
    dataset_matches: list[dict[str, Any]]
    aggregates: dict[str, Any]
    sources_breakdown: dict[str, Any] = Field(default_factory=dict)