"""Page 2 — Deterioration Risk Score Report"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from dashboard.utils import (
    inject_css, page_header, require_table,
    gauge_chart, risk_distribution_chart, risk_band_donut,
    apply_theme, C, RISK_COLORS, RISK_THRESHOLD,
)

st.set_page_config(page_title="Risk Scores · MedPulse", page_icon="🎯", layout="wide")
inject_css()

with st.sidebar:
    st.markdown('<div style="font-size:1rem;font-weight:700;color:#f0f4ff;padding:0.8rem 0 1.2rem 0;border-bottom:1px solid #1e2230;margin-bottom:0.8rem;">🏥 MedPulse</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Filters</div>', unsafe_allow_html=True)
    min_risk = st.slider("Min Risk Score", 0.0, 1.0, 0.0, 0.05)
    show_flagged = st.checkbox("High-risk only", False)

page_header("🎯 Deterioration Risk Scores", "ML-generated risk scores per patient. Patients above 40% are flagged for clinical review.")

df = require_table("deterioration_risk_scores")

fdf = df[df["risk_score"] >= min_risk].copy()
if show_flagged:
    fdf = fdf[fdf["risk_flag"] == 1]

# ── KPIs ───────────────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
c1.metric("Patients Scored",   f"{len(fdf):,}")
c2.metric("🔴 Flagged (≥40%)", f"{(fdf['risk_score']>=RISK_THRESHOLD).sum():,}")
c3.metric("Avg Risk",          f"{fdf['risk_score'].mean():.1%}")
c4.metric("Max Risk",          f"{fdf['risk_score'].max():.1%}")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-label">Top 5 Highest-Risk Patients</div>', unsafe_allow_html=True)

# ── Gauges ─────────────────────────────────────────────────────────────────────
top5 = fdf.nlargest(5, "risk_score")
gcols = st.columns(5)
for i, (_, row) in enumerate(top5.iterrows()):
    with gcols[i]:
        st.plotly_chart(gauge_chart(row["risk_score"], row["patient_id"]),
                        use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Distribution + donut ───────────────────────────────────────────────────────
col1, col2 = st.columns([3, 2])
with col1:
    st.plotly_chart(risk_distribution_chart(fdf), use_container_width=True)
with col2:
    st.plotly_chart(risk_band_donut(fdf), use_container_width=True)

# ── Risk by ward ───────────────────────────────────────────────────────────────
if "ward" in fdf.columns:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Risk by Ward</div>', unsafe_allow_html=True)
    ward_r = fdf.groupby("ward")["risk_score"].agg(["mean","count"]).reset_index()
    ward_r.columns = ["ward","avg_risk","patients"]
    fig = go.Figure(go.Bar(
        x=ward_r["ward"], y=ward_r["avg_risk"]*100,
        marker_color=[C["red"] if r>=0.55 else C["orange"] if r>=0.40 else C["green"]
                      for r in ward_r["avg_risk"]],
        text=[f"{r:.1%}" for r in ward_r["avg_risk"]],
        textposition="outside", textfont=dict(color=C["text"]),
        width=0.45,
    ))
    fig.add_hline(y=RISK_THRESHOLD*100, line_dash="dot",
                  line_color=C["red"], line_width=1.2,
                  annotation_text="Alert threshold",
                  annotation_font_color=C["red"])
    fig = apply_theme(fig, height=280)
    fig.update_layout(yaxis_title="Avg Risk Score (%)", xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.markdown('<div class="section-label">All Patients</div>', unsafe_allow_html=True)
disp = [c for c in ["patient_id","name","age","ward","primary_condition",
                      "risk_score","risk_band","risk_flag",
                      "heart_rate","spo2_pct","respiratory_rate"] if c in fdf.columns]
st.dataframe(
    fdf[disp].sort_values("risk_score", ascending=False).reset_index(drop=True)
    .style.background_gradient(subset=["risk_score"], cmap="RdYlGn_r"),
    use_container_width=True, height=380,
)
csv = fdf[disp].to_csv(index=False).encode()
st.download_button("⬇ Download CSV", csv, "risk_scores.csv", "text/csv")
