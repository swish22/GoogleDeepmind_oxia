import streamlit as st
import requests
import pandas as pd
import altair as alt
import json
import os

API_URL = "http://localhost:8000/analyze_meal"
DATA_FILE = "users_data.json"

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

# CSS from oxia-adilogic
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background: #08090e !important;
    color: #d4d9e8;
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2rem 4rem 2rem; max-width: 1280px; }

/* Hero */
.oxia-hero {
    background: linear-gradient(135deg, #0f1624 0%, #111827 60%, #0a1623 100%);
    border: 1px solid #1e2d45;
    border-radius: 20px;
    padding: 32px 40px 28px 40px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.oxia-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.oxia-hero h1 {
    font-size: 2.6rem; font-weight: 800;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #e879f9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; line-height: 1.1;
}
.oxia-hero p {
    color: #64748b; font-size: 1rem; margin: 8px 0 0 0; font-weight: 400;
}

/* Stat chips */
.stat-strip { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }
.stat-chip {
    background: #0f1624;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 14px 20px;
    flex: 1; min-width: 140px;
    text-align: center;
}
.stat-chip .label { font-size: 0.72rem; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.stat-chip .value { font-size: 1.55rem; font-weight: 700; margin-top: 4px; }
.stat-chip.cyan .value  { color: #38bdf8; }
.stat-chip.violet .value { color: #818cf8; }
.stat-chip.amber .value  { color: #f59e0b; }
.stat-chip.rose .value   { color: #fb7185; }

/* Section headers */
.section-header {
    font-size: 0.78rem; font-weight: 700; color: #334155;
    text-transform: uppercase; letter-spacing: 0.12em;
    margin: 28px 0 12px 0;
    display: flex; align-items: center; gap: 8px;
}
.section-header::after {
    content: ''; flex: 1; height: 1px; background: #1e2d45;
}

/* Persona cards */
.persona-card {
    background: #0d1424;
    border-radius: 16px;
    padding: 22px 24px;
    border-left: 4px solid;
    margin-bottom: 12px;
    position: relative;
}
.persona-card.glucose { border-color: #38bdf8; }
.persona-card.inflam  { border-color: #fb7185; }
.persona-card.perf    { border-color: #a78bfa; }

.persona-card .p-title {
    font-size: 0.85rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; margin-bottom: 6px;
}
.persona-card.glucose .p-title { color: #38bdf8; }
.persona-card.inflam  .p-title { color: #fb7185; }
.persona-card.perf    .p-title { color: #a78bfa; }

.persona-card .p-insight {
    font-size: 0.88rem; color: #94a3b8; line-height: 1.6; margin-top: 8px; font-style: italic;
}

/* Inflammation badge */
.inflam-safe  { display:inline-block; background:#052e16; color:#4ade80; border:1px solid #166534; border-radius:6px; padding:4px 12px; font-size:0.82rem; font-weight:600; }
.inflam-alert { display:inline-block; background:#450a0a; color:#f87171; border:1px solid #7f1d1d; border-radius:6px; padding:4px 12px; font-size:0.82rem; font-weight:600; }
.disruptor-tag { display:inline-block; background:#1c1917; color:#d97706; border:1px solid #44381f; border-radius:4px; padding:2px 8px; font-size:0.75rem; margin:3px; }

/* Cognitive state badge */
.cog-state {
    display: inline-block;
    border-radius: 10px;
    padding: 10px 20px;
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
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 12px;
}
.holistic-card p { font-size: 0.93rem; color: #94a3b8; line-height: 1.7; margin: 0; }

/* Buttons */
button[kind="primary"] {
    background: linear-gradient(90deg, #0ea5e9, #6366f1) !important;
    color: white !important; font-weight: 700 !important;
    border: none !important; border-radius: 12px !important;
    padding: 14px !important; font-size: 1rem !important;
    transition: opacity 0.2s !important;
}
button[kind="primary"]:hover { opacity: 0.85 !important; }

/* Camera */
.stCameraInput > div > div { border-radius: 14px !important; border: 1px solid #1e2d45 !important; }

/* Select / checkbox */
.stSelectbox label, .stCheckbox label { color: #64748b !important; font-size: 0.85rem !important; }

div[data-testid="stMetric"] { background: transparent !important; }

/* Chart container */
.chart-wrap {
    background: #0d1424;
    border: 1px solid #1e2d45;
    border-radius: 16px;
    padding: 18px 18px 8px 18px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR (Login & History) ───────────────────────────────────────────────
st.sidebar.title("👤 Login")
if not st.session_state.username:
    user_input = st.sidebar.text_input("Enter username to track meals:")
    if st.sidebar.button("Login"):
        if user_input:
            st.session_state.username = user_input
            users_db = load_data()
            st.session_state.meal_history = users_db.get(user_input, [])
            st.rerun()
else:
    st.sidebar.success(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.username = None
        st.session_state.meal_history = []
        if "latest_analysis" in st.session_state:
            del st.session_state.latest_analysis
        if "latest_meal_summary" in st.session_state:
            del st.session_state.latest_meal_summary
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("📓 Diet Log & Export")
if not st.session_state.username:
    st.sidebar.info("Log in to view your history.")
else:
    if st.session_state.meal_history:
        df_history = pd.DataFrame(st.session_state.meal_history)
        st.sidebar.dataframe(df_history, hide_index=True)
        
        csv = df_history.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="Download Meal History (CSV)",
            data=csv,
            file_name=f"oxia_{st.session_state.username}_history.csv",
            mime="text/csv",
        )
        
        if st.sidebar.button("Clear Tracker", type="primary"):
            st.session_state.meal_history = []
            users_db = load_data()
            users_db[st.session_state.username] = []
            save_data(users_db)
            st.rerun()
    else:
        st.sidebar.info("No meals tracked yet. Take a photo to get started!")

# ─── HERO ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="oxia-hero">
  <h1>🧬 Oxia</h1>
  <p>The Metabolic Digital Twin &nbsp;·&nbsp; Project your future-self before you eat.</p>
</div>
""", unsafe_allow_html=True)

# ─── SETTINGS ────────────────────────────────────────────────────────────────
with st.expander("⚙️ AI Engine Settings"):
    model_choice = st.selectbox(
        "Reasoning Model",
        ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"],
        index=0,
        help="Falls back to the next model automatically if one is unavailable.",
    )

# ─── CAMERA / UPLOAD ─────────────────────────────────────────────────────────
if "latest_analysis" not in st.session_state:
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
            with st.spinner("🔬 Running metabolic analysis..."):
                try:
                    files = {"file": ("meal.jpg", img_file_buffer.getvalue(), "image/jpeg")}
                    data  = {"model_name": model_choice}
                    resp  = requests.post(API_URL, files=files, data=data)

                    if resp.status_code != 200:
                        st.error(f"Engine error {resp.status_code}: {resp.text}")
                        st.stop()

                    r = resp.json()
                    
                    meal_summary = {
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
                    st.error("❌ Cannot reach the backend engine. Make sure `uvicorn backend:app --port 8000` is running.")
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

    st.success("Analysis Complete!")

    # ── MEAL NAME ──────────────────────────────────────────────
    st.markdown(f"<h3 style='color:#e2e8f0;margin:0 0 4px'>🍽️ {r['meal_name']}</h3>", unsafe_allow_html=True)

    # ── STAT STRIP ─────────────────────────────────────────────
    gl   = r["estimated_glycemic_load"]
    nd   = r["micro_nutrient_density"]
    peak = ga["peak_glucose"]
    ss   = ih["stress_score"]
    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-chip cyan"> <div class="label">Glycemic Load</div><div class="value">{gl:.1f}</div></div>
        <div class="stat-chip violet"><div class="label">Nutrient Density</div><div class="value">{nd}</div></div>
        <div class="stat-chip amber"> <div class="label">Peak Glucose</div><div class="value">{peak} mg/dL</div></div>
        <div class="stat-chip rose">  <div class="label">Stress Score</div><div class="value">{ss}/10</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── HOLISTIC HEALTH INSIGHT ────────────────────────────────
    st.markdown('<div class="section-header">🩺 Holistic Health Synthesis</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="holistic-card"><p>{r['holistic_health_insight']}</p></div>
    """, unsafe_allow_html=True)

    # ── CHARTS ROW ─────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Data Visualizations</div>', unsafe_allow_html=True)
    chart_col, pyramid_col = st.columns(2, gap="medium")

    # 1. Blood Glucose Curve
    with chart_col:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        curve_data = pd.DataFrame([
            {"Time (min)": pt["time_mins"], "Glucose (mg/dL)": pt["glucose_mg_dl"]}
            for pt in ga["glucose_curve"]
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
        peak_pt = pd.DataFrame([{"Time (min)": ga["spike_time_mins"], "Glucose (mg/dL)": peak}])
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
                mb["carbs_g"], mb["protein_g"], mb["fat_g"],
                mb["fiber_g"], mb["fruits_veg_g"]
            ]
        })
        
        # Filter out 0g items so they don't crowd the pie chart legend
        pyramid_data = pyramid_data[pyramid_data["Amount (g)"] > 0]
        
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
        <strong style="color:#38bdf8;font-size:1.2rem;">{ga['peak_glucose']} mg/dL</strong>
        <span style="color:#64748b;font-size:.85rem;"> at {ga['spike_time_mins']} min</span>
        <div class="p-insight">{ga['architect_insight']}</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Inflammation Hunter
    disruptors_html = "".join(
        f'<span class="disruptor-tag">⚠ {d}</span>'
        for d in ih["hidden_disruptors"]
    ) or ""
    badge_html = (
        '<span class="inflam-alert">🚨 Disruptors Detected</span>'
        if ih["disruptors_detected"] else
        '<span class="inflam-safe">🌿 No Disruptors Found</span>'
    )
    st.markdown(f"""
    <div class="persona-card inflam">
        <div class="p-title">🔥 The Inflammation Hunter</div>
        {badge_html} &nbsp;
        <span style="color:#94a3b8;font-size:.85rem;">Stress: </span>
        <strong style="color:#fb7185;">{ih['stress_score']}/10</strong>
        <div style="margin-top:8px;">{disruptors_html}</div>
        <div class="p-insight">{ih['hunter_insight']}</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Performance Ghost – Cognitive State
    cs = pg["cognitive_state"]
    label_lower = cs["state_label"].lower()
    cog_cls = (
        "cog-peak"  if "peak" in label_lower  else
        "cog-focus" if "focus" in label_lower or "steady" in label_lower else
        "cog-dip"   if "dip" in label_lower   else "cog-fog"
    )
    st.markdown(f"""
    <div class="persona-card perf">
        <div class="p-title">👻 The Performance Ghost</div>
        <span class="cog-state {cog_cls}">{cs['state_emoji']} {cs['state_label']}</span>
        &nbsp;
        <span style="color:#94a3b8;font-size:.85rem;">for&nbsp;</span>
        <strong style="color:#a78bfa;">{cs['duration_mins']} min</strong>
        &nbsp;&nbsp;
        <span style="color:#64748b;font-size:.82rem;">Deep Work: </span>
        <strong style="color:#a78bfa;">{pg['deep_work_window_mins']} min</strong>
        &nbsp;
        <span style="color:#64748b;font-size:.82rem;"> · Brain Fog Risk: </span>
        <strong style="color:{'#4ade80' if pg['brain_fog_risk']=='Low' else '#fbbf24' if pg['brain_fog_risk']=='Medium' else '#f87171'};">{pg['brain_fog_risk']}</strong>
        <div class="p-insight">{pg['ghost_insight']}</div>
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
            df_matches = df_matches[["name", "calories", "protein", "carbs", "fat", "grams"]]
            df_matches.columns = ["Ingredient Match", "Calories", "Protein (g)", "Carbs (g)", "Fat (g)", "Serving (g)"]
            st.dataframe(df_matches, use_container_width=True, hide_index=True)
    else:
        st.info("No exact scientific matches found in the HuggingFace dataset for these ingredients.")
        
    st.markdown("---")
    if st.session_state.username:
        if st.button("📓 Log this entry to my tracker", type="primary", use_container_width=True):
            st.session_state.meal_history.append(st.session_state.latest_meal_summary)
            users_db = load_data()
            users_db[st.session_state.username] = st.session_state.meal_history
            save_data(users_db)
            del st.session_state.latest_analysis
            del st.session_state.latest_meal_summary
            st.success("Meal logged successfully!")
            st.rerun()
        
        if st.button("Discard", use_container_width=True):
            del st.session_state.latest_analysis
            del st.session_state.latest_meal_summary
            st.rerun()
    else:
        st.warning("⚠️ Please log in from the sidebar to save this meal to your tracker.")
        if st.button("Discard", use_container_width=True):
            del st.session_state.latest_analysis
            del st.session_state.latest_meal_summary
            st.rerun()
