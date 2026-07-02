"""Page 3 — Alert Response Time Report"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import plotly.graph_objects as go
from dashboard.utils import inject_css, page_header, require_table, sla_bar_chart, apply_theme, C

st.set_page_config(page_title="Alert Response · MedPulse", page_icon="⏱️", layout="wide")
inject_css()

with st.sidebar:
    st.markdown('<div style="font-size:1rem;font-weight:700;color:#f0f4ff;padding:0.8rem 0 1.2rem 0;border-bottom:1px solid #1e2230;margin-bottom:0.8rem;">🏥 MedPulse</div>', unsafe_allow_html=True)

page_header("⏱️ Alert Response Time", "Time from alert raised → clinical intervention. Tracks SLA compliance across severity levels.")

df = require_table("alert_response_times")

# ── KPIs ───────────────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
if "total_alerts" in df.columns:
    c1.metric("Total Alerts", f"{int(df['total_alerts'].sum()):,}")
if "avg_response_min" in df.columns:
    c2.metric("Avg Response", f"{df['avg_response_min'].mean():.1f} min")
if "sla_met_pct" in df.columns:
    overall = df["sla_met_pct"].mean()
    c3.metric("Overall SLA Met", f"{overall:.1f}%",
              delta=f"{'Above' if overall>=90 else 'Below'} 90% target",
              delta_color="normal" if overall>=90 else "inverse")
crit = df[df["severity"]=="Critical"] if "severity" in df.columns else df
if len(crit) and "avg_response_min" in crit.columns:
    c4.metric("Critical Avg", f"{crit['avg_response_min'].mean():.1f} min", delta="SLA: 5 min", delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# ── Two charts ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(sla_bar_chart(df), use_container_width=True)
with col2:
    if "alert_type" in df.columns and "total_alerts" in df.columns:
        at = df.groupby("alert_type")["total_alerts"].sum().reset_index().sort_values("total_alerts",ascending=True)
        fig = go.Figure(go.Bar(
            x=at["total_alerts"], y=at["alert_type"],
            orientation="h",
            marker_color=C["blue"], opacity=0.85,
            text=at["total_alerts"], textposition="outside",
            textfont=dict(color=C["text"]),
        ))
        fig = apply_theme(fig, height=310)
        fig.update_layout(title="Alerts by Type", xaxis_title="Count", yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

# ── Response time scatter by severity ─────────────────────────────────────────
if "avg_response_min" in df.columns and "median_response_min" in df.columns:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Avg vs Median Response Time by Severity × Alert Type</div>', unsafe_allow_html=True)
    RISK_C = {"Critical":C["red"],"High":C["orange"],"Medium":C["yellow"],"Low":C["green"]}
    fig2 = go.Figure()
    for sev in df["severity"].unique() if "severity" in df.columns else []:
        sub = df[df["severity"]==sev]
        fig2.add_trace(go.Scatter(
            x=sub["avg_response_min"], y=sub["median_response_min"],
            mode="markers+text",
            text=sub.get("alert_type", sub.index),
            textposition="top center", textfont=dict(size=9, color=C["muted"]),
            marker=dict(size=12, color=RISK_C.get(sev, C["blue"]), opacity=0.85),
            name=sev,
        ))
    fig2 = apply_theme(fig2, height=300)
    fig2.update_layout(xaxis_title="Avg Response (min)", yaxis_title="Median Response (min)",
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.markdown('<div class="section-label">Full Table</div>', unsafe_allow_html=True)
st.dataframe(df.sort_values("avg_response_min", ascending=False) if "avg_response_min" in df.columns else df,
             use_container_width=True, height=300)
st.download_button("⬇ Download CSV", df.to_csv(index=False).encode(), "alert_response.csv", "text/csv")
