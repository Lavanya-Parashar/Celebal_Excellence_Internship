"""
Medallion Healthcare Analytics Platform — Streamlit Dashboard
Run: streamlit run dashboard/app.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from dashboard.utils import load_gold_table

st.set_page_config(
    page_title="MedPulse Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Page background ── */
.stApp { background: #0f1117; color: #e8eaf0; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #151821 !important;
    border-right: 1px solid #1e2230;
}
[data-testid="stSidebar"] * { color: #c8ccd8 !important; }
[data-testid="stSidebarNav"] a {
    border-radius: 8px;
    margin: 2px 0;
    padding: 8px 12px !important;
    transition: background 0.15s;
}
[data-testid="stSidebarNav"] a:hover { background: #1e2230 !important; }
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: linear-gradient(90deg,#1a3a5c,#0e2440) !important;
    border-left: 3px solid #3b82f6;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #151821;
    border: 1px solid #1e2230;
    border-radius: 12px;
    padding: 16px 20px;
    transition: border-color 0.2s;
}
[data-testid="stMetric"]:hover { border-color: #3b82f6; }
[data-testid="stMetricLabel"] { color: #8892a4 !important; font-size:0.78rem !important; letter-spacing:0.06em; text-transform:uppercase; }
[data-testid="stMetricValue"] { color: #e8eaf0 !important; font-size:1.7rem !important; font-weight:600 !important; }
[data-testid="stMetricDelta"] { font-size:0.78rem !important; }

/* ── Divider ── */
hr { border-color: #1e2230 !important; margin: 1.5rem 0 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Buttons ── */
.stDownloadButton button {
    background: #1a3a5c !important; color: #e8eaf0 !important;
    border: 1px solid #3b82f6 !important; border-radius: 8px !important;
    font-size: 0.82rem !important;
}
.stDownloadButton button:hover { background: #3b82f6 !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #151821 !important;
    border: 1px solid #1e2230 !important;
    border-radius: 10px !important;
}

/* ── Tab ── */
.stTabs [data-baseweb="tab-list"] { background: #151821; border-radius:10px; padding:4px; }
.stTabs [data-baseweb="tab"] { color:#8892a4; border-radius:8px; }
.stTabs [aria-selected="true"] { background:#1a3a5c !important; color:#e8eaf0 !important; }

/* ── Home hero ── */
.hero-wrap {
    background: linear-gradient(135deg, #0e1520 0%, #0f2040 50%, #0e1520 100%);
    border: 1px solid #1e3a5c;
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content:"";
    position:absolute; top:-60px; right:-60px;
    width:220px; height:220px;
    background: radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 70%);
    border-radius:50%;
}
.hero-eyebrow {
    font-size:0.72rem; font-weight:600; letter-spacing:0.14em;
    color:#3b82f6; text-transform:uppercase; margin-bottom:0.6rem;
}
.hero-title {
    font-size:2.1rem; font-weight:700; color:#f0f4ff;
    line-height:1.2; margin-bottom:0.8rem;
}
.hero-title span { color:#3b82f6; }
.hero-sub {
    font-size:0.95rem; color:#8892a4; max-width:560px; line-height:1.65;
}
.tech-pill {
    display:inline-block;
    background:#1a2540; border:1px solid #1e3a5c;
    color:#7ca8e0; font-size:0.72rem; font-weight:500;
    padding:4px 12px; border-radius:20px; margin:3px 3px 3px 0;
    font-family: 'JetBrains Mono', monospace;
}
.layer-card {
    background:#151821; border:1px solid #1e2230;
    border-radius:12px; padding:1.2rem 1.4rem;
}
.layer-card h4 { color:#e8eaf0; font-size:0.95rem; font-weight:600; margin:0 0 0.5rem 0; }
.layer-card p  { color:#8892a4; font-size:0.83rem; line-height:1.6; margin:0; }
.layer-badge {
    display:inline-block; font-size:0.65rem; font-weight:700;
    padding:2px 8px; border-radius:4px; margin-bottom:0.5rem;
    letter-spacing:0.08em; text-transform:uppercase;
}
.badge-b { background:#3d1f00; color:#f59e0b; }
.badge-s { background:#001f3d; color:#60a5fa; }
.badge-g { background:#1a2e00; color:#86efac; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar brand ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 1.5rem 0; border-bottom:1px solid #1e2230; margin-bottom:1rem;">
        <div style="font-size:1.1rem;font-weight:700;color:#f0f4ff;">🏥 MedPulse</div>
        <div style="font-size:0.72rem;color:#8892a4;margin-top:2px;">Healthcare Analytics Platform</div>
    </div>
    <div style="font-size:0.7rem;color:#8892a4;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;padding-left:4px;">Reports</div>
    """, unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-eyebrow">Medallion Architecture · Bronze → Silver → Gold</div>
    <div class="hero-title">Real-Time Patient<br><span>Deterioration Detection</span></div>
    <div class="hero-sub">
        Continuous vital-sign monitoring across all wards. ML-powered risk scoring
        flags high-risk patients up to 12 hours before critical deterioration.
    </div>
    <div style="margin-top:1.2rem;">
        <span class="tech-pill">Apache Kafka</span>
        <span class="tech-pill">PySpark</span>
        <span class="tech-pill">Delta Lake</span>
        <span class="tech-pill">Databricks</span>
        <span class="tech-pill">Azure Data Factory</span>
        <span class="tech-pill">ADLS</span>
        <span class="tech-pill">Random Forest · AUC 0.94</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI strip ─────────────────────────────────────────────────────────────────
risk_df      = load_gold_table("deterioration_risk_scores")
high_risk_df = load_gold_table("high_risk_patients")
icu_df       = load_gold_table("icu_capacity")

c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    total = risk_df["patient_id"].nunique() if risk_df is not None else 0
    st.metric("Patients Monitored", f"{total:,}")
with c2:
    high = len(high_risk_df) if high_risk_df is not None else 0
    st.metric("🔴 High-Risk", f"{high}", delta=f"Need review" if high else None, delta_color="inverse")
with c3:
    if risk_df is not None:
        st.metric("Avg Risk Score", f"{risk_df['risk_score'].mean():.1%}")
    else:
        st.metric("Avg Risk Score", "—")
with c4:
    if icu_df is not None and "avg_util_pct" in icu_df.columns:
        st.metric("ICU Utilisation", f"{icu_df['avg_util_pct'].mean():.1f}%")
    else:
        st.metric("ICU Utilisation","—")
with c5:
    from config.settings import MODEL_DIR
    mp = os.path.join(MODEL_DIR,"model_metrics.json")
    if os.path.exists(mp):
        with open(mp) as f: m=json.load(f)
        st.metric("ML AUC-ROC", f"{m.get('auc_roc',0):.4f}")
    else:
        st.metric("ML AUC-ROC","Not trained")

st.markdown("<br>", unsafe_allow_html=True)

# ── Architecture cards ────────────────────────────────────────────────────────
col1,col2,col3 = st.columns(3)
with col1:
    st.markdown("""<div class="layer-card">
    <span class="layer-badge badge-b">Bronze</span>
    <h4>Raw Ingestion</h4>
    <p>Vitals land here exactly as received from Kafka streams. No transforms.
    Delta Lake ACID writes guarantee zero data loss. Full replay support.</p>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div class="layer-card">
    <span class="layer-badge badge-s">Silver</span>
    <h4>Cleaned & Enriched</h4>
    <p>Deduplication, outlier removal, null handling, type casting.
    Patient registry join adds ward, condition, demographics. EWS scoring applied.</p>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div class="layer-card">
    <span class="layer-badge badge-g">Gold</span>
    <h4>Clinical Intelligence</h4>
    <p>5 production reports. ML risk scores updated per patient.
    ICU utilisation, alert SLAs, and high-risk detection — ready for clinical action.</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Celebal Excellence Internship 2025 · Data Engineering Intern · Lavanya Prashar")
