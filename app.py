import streamlit as st
import requests
import pandas as pd
import altair as alt
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("OXIA_API_URL", "http://localhost:8000/analyze_meal")
DATA_FILE = "users_data.json"
REQUEST_TIMEOUT = 120  # seconds for AI analysis

st.set_page_config(
    page_title="Oxia · Metabolic Digital Twin",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

if "meal_history" not in st.session_state:
    st.session_state.meal_history = []
if "username" not in st.session_state:
    st.session_state.username = None

# Premium CSS — Oxia Metabolic Digital Twin
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background: #05070a !important;
    color: #e2e8f0;
    font-family: 'Space Grotesk', -apple-system, sans-serif;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2rem 4rem 2rem; max-width: 1400px; }

/* Hero — refined gradient */
.oxia-hero {
    background: linear-gradient(145deg, #0a0f1a 0%, #0d1321 40%, #0f172a 100%);
    border: 1px solid rgba(30, 58, 95, 0.6);
    border-radius: 24px;
    padding: 36px 44px 32px 44px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
.oxia-hero::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(56,189,248,0.15) 0%, transparent 65%);
    border-radius: 50%;
}
.oxia-hero::after {
    content: '';
    position: absolute;
    bottom: -40px; left: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(232,121,249,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.oxia-hero h1 {
    font-size: 3rem; font-weight: 800;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 45%, #e879f9 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; letter-spacing: -0.03em;
    text-shadow: 0 0 80px rgba(56,189,248,0.3);
}
.oxia-hero p {
    color: #64748b; font-size: 1.05rem; margin: 10px 0 0 0; font-weight: 400;
}

/* Stat chips — hover effect */
.stat-strip { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 24px; }
.stat-chip {
    background: linear-gradient(180deg, #0f1624 0%, #0d1321 100%);
    border: 1px solid #1e2d45;
    border-radius: 14px;
    padding: 16px 22px;
    flex: 1; min-width: 150px;
    text-align: center;
    transition: border-color 0.2s, transform 0.15s;
}
.stat-chip:hover { border-color: #334155; transform: translateY(-1px); }
.stat-chip .label { font-size: 0.7rem; color: #475569; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }
.stat-chip .value { font-size: 1.6rem; font-weight: 700; margin-top: 6px; font-family: 'JetBrains Mono', monospace; }
.stat-chip.cyan .value  { color: #38bdf8; }
.stat-chip.violet .value { color: #818cf8; }
.stat-chip.amber .value  { color: #f59e0b; }
.stat-chip.rose .value   { color: #fb7185; }

/* Section headers */
.section-header {
    font-size: 0.75rem; font-weight: 700; color: #475569;
    text-transform: uppercase; letter-spacing: 0.14em;
    margin: 32px 0 14px 0;
    display: flex; align-items: center; gap: 10px;
}
.section-header::after {
    content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, #1e2d45, transparent);
}

/* Persona cards — subtle glow */
.persona-card {
    background: linear-gradient(135deg, #0d1424 0%, #0a0f1a 100%);
    border-radius: 18px;
    padding: 24px 26px;
    border-left: 4px solid;
    margin-bottom: 14px;
    position: relative;
    border: 1px solid #1e2d45;
    border-left: 4px solid;
    transition: border-color 0.2s;
}
.persona-card.glucose { border-color: #1e2d45; border-left-color: #38bdf8; }
.persona-card.inflam  { border-color: #1e2d45; border-left-color: #fb7185; }
.persona-card.perf    { border-color: #1e2d45; border-left-color: #a78bfa; }

.persona-card .p-title {
    font-size: 0.82rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; margin-bottom: 8px;
}
.persona-card.glucose .p-title { color: #38bdf8; }
.persona-card.inflam  .p-title { color: #fb7185; }
.persona-card.perf    .p-title { color: #a78bfa; }

.persona-card .p-insight {
    font-size: 0.9rem; color: #94a3b8; line-height: 1.65; margin-top: 10px; font-style: italic;
}

/* Ingredient pills */
.ingredient-pill {
    display: inline-block;
    background: rgba(30, 45, 69, 0.6);
    border: 1px solid #1e2d45;
    border-radius: 20px;
    padding: 6px 14px;
    margin: 4px 6px 4px 0;
    font-size: 0.85rem;
    color: #94a3b8;
}

/* Inflammation badge */
.inflam-safe  { display:inline-block; background:#052e16; color:#4ade80; border:1px solid #166534; border-radius:8px; padding:5px 14px; font-size:0.82rem; font-weight:600; }
.inflam-alert { display:inline-block; background:#450a0a; color:#f87171; border:1px solid #7f1d1d; border-radius:8px; padding:5px 14px; font-size:0.82rem; font-weight:600; }
.disruptor-tag { display:inline-block; background:#1c1917; color:#d97706; border:1px solid #44381f; border-radius:6px; padding:3px 10px; font-size:0.75rem; margin:3px; }

/* Cognitive state badge */
.cog-state {
    display: inline-block;
    border-radius: 12px;
    padding: 10px 22px;
    font-size: 1rem; font-weight: 700;
    margin-bottom: 6px;
}
.cog-peak   { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.cog-focus  { background: #0f172a; color: #818cf8; border: 1px solid #3730a3; }
.cog-dip    { background: #1c1400; color: #fbbf24; border: 1px solid #92400e; }
.cog-fog    { background: #450a0a; color: #f87171; border: 1px solid #7f1d1d; }

/* Holistic insight */
.holistic-card {
    background: linear-gradient(135deg, #0f1e35 0%, #0d1424 100%);
    border: 1px solid #1e3a5f;
    border-radius: 18px;
    padding: 24px 26px;
    margin-bottom: 14px;
}
.holistic-card p { font-size: 0.95rem; color: #94a3b8; line-height: 1.75; margin: 0; }

/* Buttons */
button[kind="primary"] {
    background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
    color: white !important; font-weight: 700 !important;
    border: none !important; border-radius: 12px !important;
    padding: 14px 20px !important; font-size: 1rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 2px 12px rgba(14, 165, 233, 0.3) !important;
}
button[kind="primary"]:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }

/* Camera */
.stCameraInput > div > div { border-radius: 16px !important; border: 1px solid #1e2d45 !important; }

/* Select / checkbox */
.stSelectbox label, .stCheckbox label { color: #64748b !important; font-size: 0.85rem !important; }

div[data-testid="stMetric"] { background: transparent !important; }

/* Chart container */
.chart-wrap {
    background: linear-gradient(180deg, #0d1424 0%, #0a0f1a 100%);
    border: 1px solid #1e2d45;
    border-radius: 18px;
    padding: 20px 20px 12px 20px;
    margin-bottom: 14px;
}

/* Tips callout */
.tips-callout {
    background: rgba(56, 189, 248, 0.06);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 20px;
    font-size: 0.88rem;
    color: #94a3b8;
}
.tips-callout strong { color: #38bdf8; }

/* Success banner */
.stSuccess { border-radius: 12px !important; }

/* Timeline — Your Next 3 Hours */
.timeline-hero {
    background: linear-gradient(160deg, #0a0f1a 0%, #0f172a 50%, #0d1321 100%);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 20px;
    padding: 28px 32px 24px 32px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.timeline-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #e879f9);
    opacity: 0.8;
}
.timeline-hero h2 {
    font-size: 1.1rem; font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin: 0 0 16px 0;
}
.timeline-hero .moment {
    font-size: 1.5rem; font-weight: 700;
    background: linear-gradient(135deg, #38bdf8, #e879f9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 20px;
    line-height: 1.3;
}
.timeline-strip {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 16px;
}
.timeline-node {
    flex: 1;
    min-width: 100px;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 14px 16px;
    text-align: center;
}
.timeline-node .t-time { font-size: 0.75rem; color: #64748b; font-weight: 600; }
.timeline-node .t-value { font-size: 1.1rem; font-weight: 700; color: #38bdf8; font-family: 'JetBrains Mono', monospace; }
.timeline-node .t-state { font-size: 0.78rem; color: #94a3b8; margin-top: 4px; }
.timeline-node.now { border-color: #38bdf8; box-shadow: 0 0 20px rgba(56,189,248,0.2); }
.timeline-node.peak { border-color: #fb7185; }
.timeline-node.focus { border-color: #4ade80; }

/* Make It Better card */
.optimize-card {
    background: linear-gradient(135deg, #052e16 0%, #0d1321 100%);
    border: 1px solid rgba(74, 222, 128, 0.3);
    border-radius: 18px;
    padding: 22px 26px;
    margin-bottom: 16px;
}
.optimize-card h3 { color: #4ade80; font-size: 0.9rem; margin: 0 0 12px 0; letter-spacing: 0.08em; }
.optimize-card ul { margin: 0; padding-left: 20px; color: #94a3b8; line-height: 2; }
.optimize-card li { margin: 6px 0; }

/* Your Twin Is Learning */
.twin-card {
    background: linear-gradient(135deg, rgba(129, 140, 248, 0.1) 0%, #0d1321 100%);
    border: 1px solid rgba(129, 140, 248, 0.25);
    border-radius: 18px;
    padding: 22px 26px;
    margin-bottom: 16px;
}
.twin-card h3 { color: #818cf8; font-size: 0.9rem; margin: 0 0 10px 0; }
.twin-card p { color: #94a3b8; margin: 0; font-size: 0.92rem; line-height: 1.6; }

/* Shareable Report */
.report-card {
    background: linear-gradient(145deg, #0f172a 0%, #0a0f1a 100%);
    border: 1px solid #1e3a5f;
    border-radius: 20px;
    padding: 32px 40px;
    text-align: center;
}
.report-card .report-title { font-size: 1.4rem; font-weight: 700; color: #e2e8f0; margin-bottom: 8px; }
.report-card .report-meta { font-size: 0.85rem; color: #64748b; margin-bottom: 20px; }
.report-stats { display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; margin: 20px 0; }
.report-stat { text-align: center; }
.report-stat .val { font-size: 1.8rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.report-stat .lbl { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; }
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR (Login & History) ───────────────────────────────────────────────
st.sidebar.title("🧬 Oxia")
st.sidebar.caption("Metabolic Digital Twin")

with st.sidebar.expander("⚙️ AI Model", expanded=False):
    model_choice = st.selectbox(
        "Reasoning Model",
        ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"],
        index=0,
        help="Falls back automatically if unavailable.",
        label_visibility="collapsed",
    )

st.sidebar.markdown("---")
st.sidebar.subheader("👤 Account")
if not st.session_state.username:
    user_input = st.sidebar.text_input("Username to track meals", placeholder="Enter your name")
    if st.sidebar.button("Login", use_container_width=True):
        if user_input and user_input.strip():
            st.session_state.username = user_input.strip()
            users_db = load_data()
            st.session_state.meal_history = users_db.get(st.session_state.username, [])
            st.rerun()
else:
    st.sidebar.success(f"**{st.session_state.username}**")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.username = None
        st.session_state.meal_history = []
        for key in ["latest_analysis", "latest_meal_summary", "captured_image"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📓 Meal History")
if not st.session_state.username:
    st.sidebar.info("Log in to track & export meals.")
else:
    if st.session_state.meal_history:
        n = len(st.session_state.meal_history)
        st.sidebar.metric("Meals Logged", n)
        df_history = pd.DataFrame(st.session_state.meal_history)
        # Reorder columns to show Date first if present
        if "Date" in df_history.columns:
            cols = ["Date", "Meal"] + [c for c in df_history.columns if c not in ("Date", "Meal", "Ingredients")]
            df_history = df_history[[c for c in cols if c in df_history.columns]]
        st.sidebar.dataframe(df_history, hide_index=True, use_container_width=True)
        
        csv = df_history.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="📥 Export CSV",
            data=csv,
            file_name=f"oxia_{st.session_state.username}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        
        if st.sidebar.button("Clear All", use_container_width=True):
            st.session_state.meal_history = []
            users_db = load_data()
            users_db[st.session_state.username] = []
            save_data(users_db)
            st.rerun()
    else:
        st.sidebar.info("No meals yet. Snap a photo to start!")
    
    if st.session_state.username and len(st.session_state.meal_history) >= 1:
        st.sidebar.caption(f"🔮 Your twin has learned from {len(st.session_state.meal_history)} meal{'s' if len(st.session_state.meal_history) != 1 else ''}")

# ─── HERO ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="oxia-hero">
  <h1>🧬 Oxia</h1>
  <p>Your body's operating system. See your future self — before you eat.</p>
  <p style="font-size:0.75rem;margin-top:16px;opacity:0.6;">Powered by Google Gemini · HuggingFace nutritional data</p>
</div>
""", unsafe_allow_html=True)

st.caption("⚠️ *AI-generated estimates for education only. Not medical advice. Consult a healthcare professional.*")

# ─── CAMERA / UPLOAD ─────────────────────────────────────────────────────────
if "latest_analysis" not in st.session_state:
    st.markdown("""
    <div class="tips-callout">
        <strong>📸 Better results:</strong> Good lighting, plate filling the frame, and visible ingredients improve accuracy.
    </div>
    """, unsafe_allow_html=True)
    
    use_camera = st.checkbox("📷 Use Camera", value=True)
    img_file_buffer = None
    if use_camera:
        img_file_buffer = st.camera_input("Snap your meal")
    else:
        img_file_buffer = st.file_uploader("Upload meal photo", type=["png", "jpg", "jpeg"])

    if img_file_buffer:
        col_img, col_btn = st.columns([2, 1])
        with col_img:
            st.image(img_file_buffer.getvalue(), caption="Captured Meal", use_column_width=True)
        with col_btn:
            st.write("")
            st.write("")
            analyze = st.button("⚡ Analyze Meal", type="primary", use_container_width=True)

        if analyze:
            with st.spinner("🔬 Analyzing your meal across glucose, inflammation, cognition & macros…"):
                try:
                    files = {"file": ("meal.jpg", img_file_buffer.getvalue(), "image/jpeg")}
                    data  = {"reasoning_model": model_choice}
                    resp  = requests.post(API_URL, files=files, data=data, timeout=REQUEST_TIMEOUT)

                    if resp.status_code != 200:
                        st.error(f"Engine error {resp.status_code}: {resp.text}")
                        st.stop()

                    r = resp.json()
                    
                    meal_summary = {
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Meal": r.get("meal_name", "Unknown"),
                        "Ingredients": ", ".join(r.get("ingredients", [])),
                        "Peak Glucose (mg/dL)": r.get("glucose_architect", {}).get("peak_glucose", 0),
                        "Protein (g)": r.get("macro_breakdown", {}).get("protein_g", 0),
                        "Carbs (g)": r.get("macro_breakdown", {}).get("carbs_g", 0),
                        "Fat (g)": r.get("macro_breakdown", {}).get("fat_g", 0),
                        "Stress Score (1-10)": r.get("inflammation_hunter", {}).get("stress_score", 0),
                        "Cognitive State": r.get("performance_ghost", {}).get("cognitive_state", {}).get("state_label", "Unknown")
                    }

                    st.session_state.latest_analysis = r
                    st.session_state.latest_meal_summary = meal_summary
                    st.rerun()

                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Cannot reach the backend engine at `{API_URL}`. Make sure the FastAPI backend is running: `uvicorn backend:app --port 8000`")
                except requests.exceptions.Timeout:
                    st.error(f"⏱️ Analysis timed out after {REQUEST_TIMEOUT}s. Try again or use a simpler image.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    import traceback; st.code(traceback.format_exc())

# ─── RENDERING RESULTS ───────────────────────────────────────────────────────
if "latest_analysis" in st.session_state:
    r = st.session_state.latest_analysis
    ga = r["glucose_architect"]
    ih = r["inflammation_hunter"]
    pg = r["performance_ghost"]
    mb = r["macro_breakdown"]

    st.success("✅ **Your metabolic forecast is ready**")

    # ── YOUR NEXT 3 HOURS (The Moment of Truth) ──────────────────────────────
    curve = ga.get("glucose_curve", [])
    spike_time = ga.get("spike_time_mins", 45)
    dw_mins = pg.get("deep_work_window_mins", 60)
    cs = pg.get("cognitive_state", {}) or {}
    
    # Build timeline nodes from curve (0, 30, 60, 90, 120, 180)
    def get_glucose_at(t):
        for pt in curve:
            if pt.get("time_mins") == t:
                return pt.get("glucose_mg_dl", 85)
        return 85
    
    def get_state_at(t):
        if t == 0: return "Digesting"
        if t < spike_time: return "Glucose rising"
        if t == spike_time: return "Peak glucose"
        if t <= spike_time + 20: return "Post-spike"
        if spike_time + 20 < t <= spike_time + 20 + dw_mins: return "Deep focus"
        return "Recovering"
    
    def get_node_class(t):
        if t == 0: return "now"
        if t == spike_time: return "peak"
        if "Deep focus" in get_state_at(t): return "focus"
        return ""
    
    timeline_nodes = [
        (0, get_glucose_at(0), "Now", "now"),
        (30, get_glucose_at(30), get_state_at(30), get_node_class(30)),
        (60, get_glucose_at(60), get_state_at(60), get_node_class(60)),
        (90, get_glucose_at(90), get_state_at(90), get_node_class(90)),
        (120, get_glucose_at(120), get_state_at(120), get_node_class(120)),
        (180, get_glucose_at(180), "Baseline", ""),
    ]
    
    state_label = cs.get("state_label", "Steady Focus")
    if dw_mins >= 45:
        moment_text = f"Peak focus in ~{spike_time} min. You'll have a {dw_mins}-min deep work window — schedule your hardest task now."
    elif dw_mins > 0:
        moment_text = f"{state_label} for ~{dw_mins} min. Your brain will thank you."
    else:
        moment_text = f"Blood sugar peaks at {spike_time} min. {state_label} ahead."
    
    nodes_html = "".join(f"""
    <div class="timeline-node {n[3]}">
        <div class="t-time">{n[0]} min</div>
        <div class="t-value">{n[1]} mg/dL</div>
        <div class="t-state">{n[2]}</div>
    </div>
    """ for n in timeline_nodes)
    
    st.markdown(f"""
    <div class="timeline-hero">
        <h2>Your Next 3 Hours</h2>
        <div class="moment">{moment_text}</div>
        <div class="timeline-strip">{nodes_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── MEAL NAME & INGREDIENTS ──────────────────────────────────────────────
    st.markdown(f"<h3 style='color:#e2e8f0;margin:0 0 8px'>🍽️ {r.get('meal_name', 'Unknown Meal')}</h3>", unsafe_allow_html=True)
    ingredients = r.get("ingredients", [])
    if ingredients:
        pills_html = "".join(f'<span class="ingredient-pill">{ing}</span>' for ing in ingredients)
        st.markdown(f"<div style='margin-bottom:16px;'>{pills_html}</div>", unsafe_allow_html=True)

    # ── STAT STRIP ─────────────────────────────────────────────
    gl   = float(r.get("estimated_glycemic_load", 0))
    nd   = r.get("micro_nutrient_density", "—")
    peak = ga.get("peak_glucose", 0)
    ss   = ih.get("stress_score", 0)
    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-chip cyan"> <div class="label">Glycemic Load</div><div class="value">{gl:.1f}</div></div>
        <div class="stat-chip violet"><div class="label">Nutrient Density</div><div class="value">{nd}</div></div>
        <div class="stat-chip amber"> <div class="label">Peak Glucose</div><div class="value">{peak} mg/dL</div></div>
        <div class="stat-chip rose">  <div class="label">Stress Score</div><div class="value">{ss}/10</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── MAKE IT BETTER (Optimization Suggestions) ────────────────────────────
    opts = r.get("optimization_suggestions", []) or []
    if opts:
        opts_html = "".join(f"<li>{o}</li>" for o in opts[:3])
        st.markdown(f"""
        <div class="optimize-card">
            <h3>✨ Make It Better</h3>
            <ul>{opts_html}</ul>
        </div>
        """, unsafe_allow_html=True)

    # ── YOUR TWIN IS LEARNING (Personal Trends) ────────────────────────────────
    if st.session_state.username and len(st.session_state.meal_history) >= 3:
        hist = st.session_state.meal_history[-10:]
        stress_vals = [h.get("Stress Score (1-10)", h.get("stress_score", 0)) for h in hist if isinstance(h, dict)]
        avg_stress = sum(stress_vals) / len(stress_vals) if stress_vals else 5
        current_ss = ih.get("stress_score", 0)
        trend = "better than your average" if current_ss < avg_stress - 0.5 else "typical for you" if abs(current_ss - avg_stress) < 1 else "higher than your average"
        twin_msg = f"Based on your {len(hist)} logged meals, your average stress score is {avg_stress:.1f}. This meal is {trend} for you."
        st.markdown(f"""
        <div class="twin-card">
            <h3>🔮 Your Twin Is Learning You</h3>
            <p>{twin_msg} The more you log, the smarter your predictions become.</p>
        </div>
        """, unsafe_allow_html=True)

    # ── HOLISTIC HEALTH INSIGHT ────────────────────────────────
    st.markdown('<div class="section-header">🩺 Holistic Health Synthesis</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="holistic-card"><p>{r.get('holistic_health_insight', '')}</p></div>
    """, unsafe_allow_html=True)

    # ── CHARTS ROW ─────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Data Visualizations</div>', unsafe_allow_html=True)
    chart_col, pyramid_col = st.columns(2, gap="medium")

    # 1. Blood Glucose Curve
    with chart_col:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        curve_data = pd.DataFrame([
            {"Time (min)": pt.get("time_mins", 0), "Glucose (mg/dL)": pt.get("glucose_mg_dl", 85)}
            for pt in ga.get("glucose_curve", [])
        ])
        
        # Base Area Chart
        base = alt.Chart(curve_data).encode(
            x=alt.X("Time (min):Q", axis=alt.Axis(grid=False, labelColor="#475569", titleColor="#475569")),
            y=alt.Y("Glucose (mg/dL):Q",
                    scale=alt.Scale(domain=[60, max(200, peak + 20)]),
                    axis=alt.Axis(grid=True, gridColor="#1e2d45", labelColor="#475569", titleColor="#475569")),
            tooltip=[alt.Tooltip("Time (min):Q", title="Time"), alt.Tooltip("Glucose (mg/dL):Q", title="Glucose")]
        )
        area = base.mark_area(
            line={"color": "#38bdf8", "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear", stops=[
                    alt.GradientStop(color="rgba(56,189,248,0.35)", offset=0),
                    alt.GradientStop(color="rgba(56,189,248,0.0)", offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0,
            ),
        )
        
        # Fasting Baseline
        normal_line = alt.Chart(pd.DataFrame({"y": [85]})).mark_rule(
            color="#4ade80", strokeDash=[5, 5], strokeWidth=1.5
        ).encode(y="y:Q")
        
        # Peak Marker & Annotation
        spike_time = ga.get("spike_time_mins", 45)
        peak_pt = pd.DataFrame([{"Time (min)": spike_time, "Glucose (mg/dL)": peak}])
        peak_mark = alt.Chart(peak_pt).mark_point(color="#fb7185", size=80, filled=True).encode(
            x="Time (min):Q", y="Glucose (mg/dL):Q", tooltip=[alt.Tooltip("Glucose (mg/dL):Q", title="Peak")]
        )
        peak_text = alt.Chart(peak_pt).mark_text(
            align='left', baseline='bottom', dx=8, dy=-8, color="#fb7185", fontSize=11, fontWeight="bold"
        ).encode(
            x="Time (min):Q", y="Glucose (mg/dL):Q", text=alt.value(f"Peak: {peak}")
        )
        
        chart = (area + normal_line + peak_mark + peak_text).properties(
            title=alt.TitleParams("📈 180-Min Blood Glucose Curve", color="#94a3b8", fontSize=13),
            height=220,
            background="#0d1424",
        ).configure_view(strokeOpacity=0)
        st.altair_chart(chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Food Pyramid Pie Chart
    with pyramid_col:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        pyramid_data = pd.DataFrame({
            "Category": ["Carbs", "Protein", "Fat", "Fiber", "Fruits & Veg"],
            "Amount (g)": [
                mb.get("carbs_g", 0), mb.get("protein_g", 0), mb.get("fat_g", 0),
                mb.get("fiber_g", 0), mb.get("fruits_veg_g", 0)
            ]
        })
        
        # Filter out 0g items so they don't crowd the pie chart legend
        pyramid_data = pyramid_data[pyramid_data["Amount (g)"] > 0]
        
        if pyramid_data.empty:
            st.info("Macro breakdown not available for this meal.")
        else:
            pie = alt.Chart(pyramid_data).mark_arc(innerRadius=45, cornerRadius=4, padAngle=0.03).encode(
                theta=alt.Theta(field="Amount (g)", type="quantitative"),
                color=alt.Color(field="Category", type="nominal", scale=alt.Scale(
                    domain=["Carbs", "Protein", "Fat", "Fiber", "Fruits & Veg"],
                    range=["#f59e0b", "#38bdf8", "#fb7185", "#4ade80", "#a78bfa"]
                ), legend=alt.Legend(title=None, labelColor="#94a3b8", orient="right")),
                tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Amount (g):Q")]
            ).properties(
                title=alt.TitleParams("⚖️ Food Pyramid Breakdown", color="#94a3b8", fontSize=13),
                height=220,
                background="#0d1424",
            ).configure_view(strokeOpacity=0)
            st.altair_chart(pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── PERSONA CARDS ──────────────────────────────────────────
    st.markdown('<div class="section-header">👤 Shadow Personas</div>', unsafe_allow_html=True)

    # 1. Glucose Architect
    st.markdown(f"""
    <div class="persona-card glucose">
        <div class="p-title">🏗️ The Glucose Architect</div>
        <span style="color:#94a3b8;font-size:.85rem;">Peak </span>
        <strong style="color:#38bdf8;font-size:1.2rem;">{ga.get('peak_glucose', 0)} mg/dL</strong>
        <span style="color:#64748b;font-size:.85rem;"> at {ga.get('spike_time_mins', 45)} min</span>
        <div class="p-insight">{ga.get('architect_insight', '')}</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Inflammation Hunter
    disruptors = ih.get("hidden_disruptors", []) or []
    disruptors_html = "".join(f'<span class="disruptor-tag">⚠ {d}</span>' for d in disruptors)
    badge_html = (
        '<span class="inflam-alert">🚨 Disruptors Detected</span>'
        if ih.get("disruptors_detected") else
        '<span class="inflam-safe">🌿 No Disruptors Found</span>'
    )
    st.markdown(f"""
    <div class="persona-card inflam">
        <div class="p-title">🔥 The Inflammation Hunter</div>
        {badge_html} &nbsp;
        <span style="color:#94a3b8;font-size:.85rem;">Stress: </span>
        <strong style="color:#fb7185;">{ih.get('stress_score', 0)}/10</strong>
        <div style="margin-top:8px;">{disruptors_html}</div>
        <div class="p-insight">{ih.get('hunter_insight', '')}</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Performance Ghost – Cognitive State
    cs = pg.get("cognitive_state", {}) or {}
    label_lower = (cs.get("state_label") or "").lower()
    cog_cls = (
        "cog-peak"  if "peak" in label_lower  else
        "cog-focus" if "focus" in label_lower or "steady" in label_lower else
        "cog-dip"   if "dip" in label_lower   else "cog-fog"
    )
    bf_risk = pg.get("brain_fog_risk", "Low")
    bf_color = "#4ade80" if bf_risk == "Low" else "#fbbf24" if bf_risk == "Medium" else "#f87171"
    st.markdown(f"""
    <div class="persona-card perf">
        <div class="p-title">👻 The Performance Ghost</div>
        <span class="cog-state {cog_cls}">{cs.get('state_emoji', '')} {cs.get('state_label', '')}</span>
        &nbsp;
        <span style="color:#94a3b8;font-size:.85rem;">for&nbsp;</span>
        <strong style="color:#a78bfa;">{cs.get('duration_mins', 0)} min</strong>
        &nbsp;&nbsp;
        <span style="color:#64748b;font-size:.82rem;">Deep Work: </span>
        <strong style="color:#a78bfa;">{pg.get('deep_work_window_mins', 0)} min</strong>
        &nbsp;
        <span style="color:#64748b;font-size:.82rem;"> · Brain Fog Risk: </span>
        <strong style="color:{bf_color};">{bf_risk}</strong>
        <div class="p-insight">{pg.get('ghost_insight', '')}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── NUTRITIONAL TRUTH (HF) ────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Nutritional Truth (Verified Component Matches)</div>', unsafe_allow_html=True)
    truth = r.get("nutritional_truth", {})
    st.caption(f"Source: {truth.get('source', 'Unknown API')}")
    matches = truth.get("dataset_matches", [])
    if matches:
        df_matches = pd.DataFrame(matches)
        if not df_matches.empty:
            col_map = {"name": "Ingredient", "calories": "Cal", "protein": "Protein (g)", "carbs": "Carbs (g)", "fat": "Fat (g)", "grams": "Serving (g)"}
            display_cols = [c for c in col_map if c in df_matches.columns]
            df_display = df_matches[display_cols].rename(columns=col_map)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No exact scientific matches found in the HuggingFace dataset for these ingredients.")

    # ── SHAREABLE METABOLIC REPORT ────────────────────────────────────────────
    st.markdown('<div class="section-header">📤 Metabolic Report Card</div>', unsafe_allow_html=True)
    report_html = f"""
    <div class="report-card">
        <div class="report-title">🧬 {r.get('meal_name', 'Meal')} · Oxia Report</div>
        <div class="report-meta">{datetime.now().strftime('%B %d, %Y')} · Metabolic Digital Twin</div>
        <div class="report-stats">
            <div class="report-stat"><div class="val" style="color:#38bdf8">{peak}</div><div class="lbl">Peak Glucose</div></div>
            <div class="report-stat"><div class="val" style="color:#818cf8">{gl:.0f}</div><div class="lbl">Glycemic Load</div></div>
            <div class="report-stat"><div class="val" style="color:#fb7185">{ss}</div><div class="lbl">Stress / 10</div></div>
            <div class="report-stat"><div class="val" style="color:#4ade80">{dw_mins}</div><div class="lbl">Focus (min)</div></div>
        </div>
        <p style="color:#64748b;font-size:0.85rem;margin-top:12px;">Project your future self before you eat. · oxia.app</p>
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)
    
    # Export report as HTML file
    full_report = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Oxia Report - {r.get('meal_name', 'Meal')}</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <style>body{{font-family:'Space Grotesk',sans-serif;background:#05070a;color:#e2e8f0;padding:40px;max-width:600px;margin:0 auto;}}
    h1{{font-size:1.8rem;background:linear-gradient(135deg,#38bdf8,#e879f9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
    .stat{{display:inline-block;margin:20px;text-align:center;}}
    .stat .v{{font-size:2rem;font-weight:700;font-family:'JetBrains Mono',monospace;}}
    .meta{{color:#64748b;font-size:0.9rem;margin-top:30px;}}</style></head><body>
    <h1>🧬 {r.get('meal_name', 'Meal')}</h1>
    <p style="color:#64748b;">Metabolic Digital Twin Report · {datetime.now().strftime('%B %d, %Y')}</p>
    <div style="margin:30px 0;">
        <span class="stat"><span class="v" style="color:#38bdf8">{peak}</span><br><small>Peak Glucose</small></span>
        <span class="stat"><span class="v" style="color:#818cf8">{gl:.0f}</span><br><small>Glycemic Load</small></span>
        <span class="stat"><span class="v" style="color:#fb7185">{ss}</span><br><small>Stress Score</small></span>
        <span class="stat"><span class="v" style="color:#4ade80">{dw_mins} min</span><br><small>Focus Window</small></span>
    </div>
    <p class="meta">Your body's operating system. See your future self — before you eat.</p>
    </body></html>"""
    
    st.download_button(
        label="📥 Download Report (HTML)",
        data=full_report,
        file_name=f"oxia_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
        mime="text/html",
        use_container_width=True,
    )
        
    st.markdown("---")
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col1:
        if st.session_state.username:
            if st.button("📓 Log to Tracker", type="primary", use_container_width=True):
                st.session_state.meal_history.append(st.session_state.latest_meal_summary)
                users_db = load_data()
                users_db[st.session_state.username] = st.session_state.meal_history
                save_data(users_db)
                del st.session_state.latest_analysis
                del st.session_state.latest_meal_summary
                st.success("Meal logged!")
                st.rerun()
        else:
            st.caption("Log in to save")
    with btn_col2:
        if st.button("📷 Analyze Another Meal", use_container_width=True):
            del st.session_state.latest_analysis
            del st.session_state.latest_meal_summary
            st.rerun()
    with btn_col3:
        if st.button("Discard", use_container_width=True):
            del st.session_state.latest_analysis
            del st.session_state.latest_meal_summary
            st.rerun()
