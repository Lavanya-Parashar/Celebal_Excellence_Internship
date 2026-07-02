"""Page 1 — Hourly Patient Vitals Summary"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from dashboard.utils import inject_css, page_header, require_table, vitals_trend_line, apply_theme, C

st.set_page_config(page_title="Vitals Summary · MedPulse", page_icon="📈", layout="wide")
inject_css()

with st.sidebar:
    st.markdown('<div style="font-size:1rem;font-weight:700;color:#f0f4ff;padding:0.8rem 0 1.2rem 0;border-bottom:1px solid #1e2230;margin-bottom:0.8rem;">🏥 MedPulse</div>', unsafe_allow_html=True)

page_header("📈 Hourly Vitals Summary", "Aggregated vital signs per patient per hour — trend analysis and historical review.")

df = require_table("hourly_vitals_summary")

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">Filters</div>', unsafe_allow_html=True)
    patients = sorted(df["patient_id"].unique().tolist())
    sel_pt   = st.selectbox("Patient", patients, index=0)
    vital_choice = st.selectbox("Vital", ["heart_rate","spo2","respiratory_rate","systolic_bp","temperature"],
        format_func=lambda x: {"heart_rate":"Heart Rate","spo2":"SpO₂","respiratory_rate":"Resp. Rate","systolic_bp":"Systolic BP","temperature":"Temperature"}[x])
    if "ward" in df.columns:
        wards = ["All"] + sorted(df["ward"].dropna().unique().tolist())
        sel_ward = st.selectbox("Ward", wards)
    else:
        sel_ward = "All"

fdf = df.copy()
if sel_ward != "All" and "ward" in fdf.columns:
    fdf = fdf[fdf["ward"] == sel_ward]

# ── KPI strip ──────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Patients",        f"{fdf['patient_id'].nunique():,}")
c2.metric("Total Readings",  f"{len(fdf):,}")
c3.metric("Avg Heart Rate",  f"{fdf['avg_heart_rate'].mean():.0f} bpm")
c4.metric("Avg SpO₂",        f"{fdf['avg_spo2'].mean():.1f}%")
c5.metric("Avg Temp",        f"{fdf['avg_temperature_c'].mean():.1f}°C")

st.markdown("<br>", unsafe_allow_html=True)

# ── Two charts side by side ────────────────────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown('<div class="section-label">Vital Trend — Selected Patient</div>', unsafe_allow_html=True)
    fig = vitals_trend_line(fdf, sel_pt, vital_choice)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown('<div class="section-label">Population SpO₂ Over Time</div>', unsafe_allow_html=True)
    if "hour_bucket" in fdf.columns:
        time_df = fdf.groupby("hour_bucket")["avg_spo2"].mean().reset_index()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=time_df["hour_bucket"], y=time_df["avg_spo2"],
            mode="lines", line=dict(color=C["blue"], width=2),
            fill="tozeroy", fillcolor="rgba(59,130,246,0.07)",
        ))
        fig2.add_hline(y=94, line_dash="dot", line_color=C["red"], line_width=1.2,
                       annotation_text="Alert < 94%", annotation_font_color=C["red"])
        fig2 = apply_theme(fig2, height=280)
        fig2.update_layout(xaxis_title="Hour", yaxis_title="Avg SpO₂ (%)")
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Heatmap ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Abnormal Reading Flags — All Patients (by Hour)</div>', unsafe_allow_html=True)
if "vital_flag_count" in fdf.columns and "hour_bucket" in fdf.columns:
    pivot = fdf.pivot_table(index="patient_id", columns="hour_bucket",
                             values="vital_flag_count", aggfunc="sum", fill_value=0)
    pivot = pivot.iloc[:, -48:]  # last 48h
    fig3 = go.Figure(go.Heatmap(
        z=pivot.values, x=[str(c)[:13] for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0,"#151821"],[0.3,"#1a3a5c"],[0.6,"#f59e0b"],[1.0,"#ef4444"]],
        showscale=True, colorbar=dict(title="Flags", tickfont=dict(color=C["muted"])),
        hovertemplate="Patient: %{y}<br>Hour: %{x}<br>Flags: %{z}<extra></extra>",
    ))
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#151821",
                       font=dict(family="Inter",color=C["muted"],size=10),
                       height=min(60 + len(pivot)*18, 500),
                       margin=dict(l=80,r=40,t=20,b=60),
                       xaxis=dict(showgrid=False, tickangle=-45),
                       yaxis=dict(showgrid=False))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.markdown('<div class="section-label">Raw Data</div>', unsafe_allow_html=True)
disp = [c for c in ["patient_id","hour_bucket","avg_heart_rate","avg_spo2",
                      "avg_respiratory_rate","avg_systolic_bp","avg_temperature_c",
                      "avg_sepsis_risk","vital_flag_count","ward"] if c in fdf.columns]
st.dataframe(fdf[disp].sort_values(["patient_id","hour_bucket"]), use_container_width=True, height=300)
csv = fdf[disp].to_csv(index=False).encode()
st.download_button("⬇ Download CSV", csv, "hourly_vitals.csv", "text/csv")
