"""Dashboard Utilities — shared helpers for all pages."""
import os, sys, logging
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    GOLD_DIR, GOLD_VITALS_SUMMARY_PATH, GOLD_RISK_SCORES_PATH,
    GOLD_ALERT_RESPONSE_PATH, GOLD_ICU_CAPACITY_PATH, GOLD_HIGH_RISK_PATH,
    RISK_THRESHOLD,
)

log = logging.getLogger(__name__)

# ── Palette (dark theme) ──────────────────────────────────────────────────────
C = {
    "bg":       "#0f1117",
    "surface":  "#151821",
    "border":   "#1e2230",
    "blue":     "#3b82f6",
    "blue_dim": "#1a3a5c",
    "text":     "#e8eaf0",
    "muted":    "#8892a4",
    "red":      "#ef4444",
    "orange":   "#f59e0b",
    "yellow":   "#eab308",
    "green":    "#22c55e",
}

RISK_COLORS = {
    "Low":      C["green"],
    "Medium":   C["yellow"],
    "High":     C["orange"],
    "Critical": C["red"],
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#151821",
    font=dict(family="Inter, sans-serif", color=C["muted"], size=12),
    margin=dict(l=40, r=20, t=44, b=36),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C["border"]),
    xaxis=dict(gridcolor=C["border"], linecolor=C["border"], zerolinecolor=C["border"]),
    yaxis=dict(gridcolor=C["border"], linecolor=C["border"], zerolinecolor=C["border"]),
)

TABLE_MAP = {
    "hourly_vitals_summary":     GOLD_VITALS_SUMMARY_PATH,
    "deterioration_risk_scores": GOLD_RISK_SCORES_PATH,
    "alert_response_times":      GOLD_ALERT_RESPONSE_PATH,
    "icu_capacity":              GOLD_ICU_CAPACITY_PATH,
    "high_risk_patients":        GOLD_HIGH_RISK_PATH,
}

# ── Page CSS injected on every page ──────────────────────────────────────────
PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{ font-family:'Inter',sans-serif; }
.stApp{ background:#0f1117; color:#e8eaf0; }
[data-testid="stSidebar"]{ background:#151821 !important; border-right:1px solid #1e2230; }
[data-testid="stSidebar"] *{ color:#c8ccd8 !important; }
[data-testid="stSidebarNav"] a{ border-radius:8px; margin:2px 0; padding:8px 12px !important; transition:background 0.15s; }
[data-testid="stSidebarNav"] a:hover{ background:#1e2230 !important; }
[data-testid="stSidebarNav"] a[aria-selected="true"]{ background:linear-gradient(90deg,#1a3a5c,#0e2440) !important; border-left:3px solid #3b82f6; }
[data-testid="stMetric"]{ background:#151821; border:1px solid #1e2230; border-radius:12px; padding:16px 20px; }
[data-testid="stMetricLabel"]{ color:#8892a4 !important; font-size:0.75rem !important; letter-spacing:0.06em; text-transform:uppercase; }
[data-testid="stMetricValue"]{ color:#e8eaf0 !important; font-size:1.6rem !important; font-weight:600 !important; }
hr{ border-color:#1e2230 !important; margin:1.2rem 0 !important; }
[data-testid="stDataFrame"]{ border-radius:10px; overflow:hidden; }
.stDownloadButton button{ background:#1a3a5c !important; color:#e8eaf0 !important; border:1px solid #3b82f6 !important; border-radius:8px !important; font-size:0.82rem !important; }
[data-testid="stExpander"]{ background:#151821 !important; border:1px solid #1e2230 !important; border-radius:10px !important; }
.stTabs [data-baseweb="tab-list"]{ background:#151821; border-radius:10px; padding:4px; }
.stTabs [data-baseweb="tab"]{ color:#8892a4; border-radius:8px; }
.stTabs [aria-selected="true"]{ background:#1a3a5c !important; color:#e8eaf0 !important; }
.page-header{ font-size:1.45rem; font-weight:700; color:#f0f4ff; margin-bottom:0.2rem; }
.page-sub{ font-size:0.85rem; color:#8892a4; margin-bottom:1.2rem; }
.kpi-row{ display:flex; gap:1rem; margin-bottom:1.2rem; }
.risk-pill{ display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.risk-Low     { background:#052e16; color:#22c55e; }
.risk-Medium  { background:#2d2000; color:#eab308; }
.risk-High    { background:#3d1f00; color:#f59e0b; }
.risk-Critical{ background:#2d0606; color:#ef4444; }
.section-label{ font-size:0.78rem; font-weight:600; color:#8892a4; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem; }
</style>
"""

def inject_css():
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str):
    st.markdown(f'<div class="page-header">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_gold_table(name: str) -> Optional[pd.DataFrame]:
    path = TABLE_MAP.get(name)
    if path and os.path.exists(path):
        try:
            return pd.read_parquet(path)
        except Exception:
            pass
    if path:
        csv = path.replace(".parquet",".csv")
        if os.path.exists(csv):
            try: return pd.read_csv(csv)
            except: pass
    return None

def require_table(name: str) -> pd.DataFrame:
    df = load_gold_table(name)
    if df is None:
        st.error(f"Gold table **{name}** not found. Run the pipeline:\n```\npython orchestration/pipeline_runner.py\n```")
        st.stop()
    return df

# ── Chart helpers ─────────────────────────────────────────────────────────────
def apply_theme(fig: go.Figure, height=320) -> go.Figure:
    fig.update_layout(height=height, **PLOTLY_LAYOUT)
    fig.update_xaxes(showgrid=True, gridwidth=1)
    fig.update_yaxes(showgrid=True, gridwidth=1)
    return fig

def gauge_chart(value: float, patient_id: str) -> go.Figure:
    if value >= 0.75:   color, band = C["red"],    "Critical"
    elif value >= 0.55: color, band = C["orange"],  "High"
    elif value >= 0.40: color, band = C["yellow"],  "Medium"
    else:               color, band = C["green"],   "Low"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value * 100, 1),
        number={"suffix":"%","font":{"size":22,"color":C["text"]}},
        title={"text": f"<b>{patient_id}</b><br><span style='font-size:11px;color:{color}'>{band}</span>",
               "font":{"size":13,"color":C["muted"]}},
        gauge={
            "axis": {"range":[0,100],"tickcolor":C["muted"],"tickwidth":1},
            "bar":  {"color": color, "thickness":0.25},
            "bgcolor": C["surface"],
            "bordercolor": C["border"],
            "steps":[
                {"range":[0,40],  "color":"#052e16"},
                {"range":[40,55], "color":"#2d2000"},
                {"range":[55,75], "color":"#3d1f00"},
                {"range":[75,100],"color":"#2d0606"},
            ],
            "threshold":{"line":{"color":color,"width":3},"thickness":0.8,"value":value*100},
        },
    ))
    fig.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=16,r=16,t=52,b=8),
                      font=dict(family="Inter"))
    return fig

def risk_distribution_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df["risk_score"], nbinsx=40,
        marker_color=C["blue"], opacity=0.85,
        name="Patients",
    ))
    fig.add_vline(x=RISK_THRESHOLD, line_dash="dash",
                  line_color=C["red"], line_width=1.5,
                  annotation_text=f"Alert threshold ({int(RISK_THRESHOLD*100)}%)",
                  annotation_font_color=C["red"],
                  annotation_position="top right")
    fig.update_layout(title="Risk Score Distribution",
                      xaxis_title="Deterioration Risk Score",
                      yaxis_title="Patients", **PLOTLY_LAYOUT, height=300)
    return fig

def risk_band_donut(df: pd.DataFrame) -> go.Figure:
    if "risk_band" not in df.columns:
        return go.Figure()
    counts = df["risk_band"].value_counts()
    order = [b for b in ["Critical","High","Medium","Low"] if b in counts.index]
    fig = go.Figure(go.Pie(
        labels=order,
        values=[counts[b] for b in order],
        hole=0.62,
        marker=dict(colors=[RISK_COLORS[b] for b in order],
                    line=dict(color=C["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=11, color=C["text"]),
        hovertemplate="%{label}: %{value} patients<extra></extra>",
    ))
    fig.update_layout(title="Risk Band Split", showlegend=False,
                      paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=20,r=20,t=44,b=20), height=300,
                      font=dict(family="Inter",color=C["muted"]))
    return fig

def vitals_trend_line(df: pd.DataFrame, patient_id: str, vital: str) -> go.Figure:
    pt = df[df["patient_id"]==patient_id].sort_values("hour_bucket")
    col_map = {
        "heart_rate":       ("avg_heart_rate",      "Heart Rate (bpm)",   C["red"]),
        "spo2":             ("avg_spo2",             "SpO₂ (%)",           C["blue"]),
        "respiratory_rate": ("avg_respiratory_rate", "Resp. Rate (br/min)",C["green"]),
        "systolic_bp":      ("avg_systolic_bp",      "Systolic BP (mmHg)", "#a855f7"),
        "temperature":      ("avg_temperature_c",    "Temperature (°C)",   C["orange"]),
    }
    col, label, color = col_map.get(vital, ("avg_heart_rate","Heart Rate",C["red"]))
    if col not in pt.columns:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pt["hour_bucket"], y=pt[col],
        mode="lines+markers", name=label,
        line=dict(color=color, width=2),
        marker=dict(size=4, color=color),
        fill="tozeroy", fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
    ))
    fig.update_layout(title=f"{label} — {patient_id}",
                      xaxis_title="Hour", yaxis_title=label,
                      **PLOTLY_LAYOUT, height=280)
    return fig

def icu_bar_chart(df: pd.DataFrame) -> go.Figure:
    latest = df.groupby("unit_id").last().reset_index()
    colors = [C["red"] if u>=95 else C["orange"] if u>=80 else C["green"]
              for u in latest["avg_util_pct"]]
    fig = go.Figure(go.Bar(
        x=latest["unit_id"], y=latest["avg_util_pct"],
        marker_color=colors,
        text=latest["avg_util_pct"].apply(lambda x: f"{x:.0f}%"),
        textposition="outside", textfont=dict(color=C["text"], size=12),
        width=0.5,
    ))
    fig.add_hline(y=80, line_dash="dot", line_color=C["orange"], line_width=1.2,
                  annotation_text="80%", annotation_font_color=C["orange"])
    fig.add_hline(y=95, line_dash="dot", line_color=C["red"], line_width=1.2,
                  annotation_text="95%", annotation_font_color=C["red"])
    fig.update_layout(title="Current ICU Utilisation by Unit",
                      yaxis_title="Utilisation %", yaxis_range=[0,115],
                      xaxis_title=None, **PLOTLY_LAYOUT, height=310)
    return fig

def sla_bar_chart(df: pd.DataFrame) -> go.Figure:
    if "sla_met_pct" not in df.columns:
        return go.Figure()
    sev_order = ["Critical","High","Medium","Low"]
    sev_colors = {s: RISK_COLORS[s] for s in sev_order}
    grp = df.groupby("severity")["sla_met_pct"].mean().reset_index()
    grp["severity"] = pd.Categorical(grp["severity"], categories=sev_order, ordered=True)
    grp = grp.sort_values("severity")
    fig = go.Figure(go.Bar(
        x=grp["severity"], y=grp["sla_met_pct"],
        marker_color=[sev_colors.get(s, C["blue"]) for s in grp["severity"]],
        text=grp["sla_met_pct"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside", textfont=dict(color=C["text"]),
        width=0.45,
    ))
    fig.add_hline(y=90, line_dash="dot", line_color=C["muted"], line_width=1,
                  annotation_text="90% SLA target", annotation_font_color=C["muted"])
    fig.update_layout(title="SLA Compliance by Severity",
                      yaxis_title="SLA Met (%)", yaxis_range=[0,115],
                      xaxis_title=None, **PLOTLY_LAYOUT, height=310)
    return fig
