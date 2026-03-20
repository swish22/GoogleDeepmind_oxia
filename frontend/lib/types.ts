export type ReasoningModel =
  | "gemini-2.5-flash"
  | "gemini-2.0-flash"
  | "gemini-1.5-flash"
  | "gemini-1.5-flash-8b"
  | "gemini-1.5-pro"
  | string;

export type CognitiveState = {
  state_label: string;
  state_emoji: string;
  duration_mins: number;
};

export type GlucoseCurvePoint = {
  time_mins: number;
  glucose_mg_dl: number;
};

export type MacroBreakdown = {
  carbs_g: number;
  protein_g: number;
  fat_g: number;
  fiber_g: number;
  fruits_veg_g: number;
};

export type NutritionalMatch = {
  name: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  grams: number;
  /** Backend: huggingface_maressay | open_food_facts | usda_fdc */
  data_source?: string;
  data_source_label?: string;
  portion_note?: string;
};

/** Rolled-up macros from verified dataset_matches (sums; interpret with source notes). */
export type NutritionAggregates = {
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  total_grams: number;
  match_count: number;
};

export type NutritionalTruth = {
  source: string;
  dataset_matches: NutritionalMatch[];
  aggregates?: NutritionAggregates;
  /** Count of matches per backend data_source id */
  sources_breakdown?: Record<string, number>;
};

/** Response from POST /nutrition/match (same shape as nutritional_truth + aggregates). */
export type NutritionMatchApiResponse = {
  source: string;
  dataset_matches: NutritionalMatch[];
  aggregates: NutritionAggregates;
  sources_breakdown?: Record<string, number>;
};

export type AnalysisResponse = {
  meal_id: string;
  meal_name: string;
  ingredients: string[];
  estimated_glycemic_load: number;
  micro_nutrient_density: string;
  macro_breakdown: MacroBreakdown;
  glucose_architect: {
    peak_glucose: number;
    spike_time_mins: number;
    glucose_curve: GlucoseCurvePoint[];
    architect_insight: string;
  };
  inflammation_hunter: {
    stress_score: number;
    hidden_disruptors: string[];
    disruptors_detected: boolean;
    hunter_insight: string;
  };
  performance_ghost: {
    brain_fog_risk: "Low" | "Medium" | "High" | string;
    deep_work_window_mins: number;
    ghost_insight: string;
    cognitive_state: CognitiveState;
  };
  holistic_health_insight: string;
  optimization_suggestions: string[];
  nutritional_truth: NutritionalTruth;
};

export type ChatResponse = {
  answer: string;
  suggested_questions: string[];
  focus_metric?: string;
};

