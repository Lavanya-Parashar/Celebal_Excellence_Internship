"""Page 5 — High-Risk Patient Detection"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import plotly.graph_objects as go
from dashboard.utils import inject_css, page_header, require_table, apply_theme, C, RISK_COLORS, RISK_THRESHOLD

st.set_page_config(page_title="High-Risk · MedPulse", page_icon="🚨", layout="wide")
inject_css()

with st.sidebar:
    st.markdown('<div style="font-size:1rem;font-weight:700;color:#f0f4ff;padding:0.8rem 0 1.2rem 0;border-bottom:1px solid #1e2230;margin-bottom:0.8rem;">🏥 MedPulse</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Filters</div>', unsafe_allow_html=True)

page_header("🚨 High-Risk Patient Detection", "Daily flagged patients with supporting vital evidence and recommended clinical actions.")

df = require_table("high_risk_patients")

# Sidebar filters
with st.sidebar:
    if "risk_band" in df.columns:
        bands = sorted(df["risk_band"].unique().tolist())
        sel_bands = st.multiselect("Risk Band", bands, default=bands)
        df = df[df["risk_band"].isin(sel_bands)]
    if "ward" in df.columns:
        wards = ["All"] + sorted(df["ward"].dropna().unique().tolist())
        sw = st.selectbox("Ward", wards)
        if sw != "All": df = df[df["ward"]==sw]

# ── KPIs ───────────────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
c1.metric("High-Risk Patients", f"{len(df):,}")
if "risk_score" in df.columns:
    c2.metric("Avg Risk Score",  f"{df['risk_score'].mean():.1%}")
    c3.metric("Max Risk Score",  f"{df['risk_score'].max():.1%}")
imm = (df["recommended_action"]=="Immediate ICU Review").sum() if "recommended_action" in df.columns else 0
c4.metric("🚑 Immediate ICU", f"{imm:,}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Action summary + ward bubble ───────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    if "recommended_action" in df.columns:
        ac = df["recommended_action"].value_counts().reset_index()
        ac.columns = ["action","count"]
        ACTION_COLORS = {"Immediate ICU Review":C["red"],"Urgent Ward Review":C["orange"],
                         "Increase Monitoring Frequency":C["yellow"]}
        fig = go.Figure(go.Bar(
            x=ac["count"], y=ac["action"], orientation="h",
            marker_color=[ACTION_COLORS.get(a, C["blue"]) for a in ac["action"]],
            text=ac["count"], textposition="outside", textfont=dict(color=C["text"]),
            width=0.45,
        ))
        fig = apply_theme(fig, height=240)
        fig.update_layout(title="Actions Required", xaxis_title="Patients", yaxis_title=None,
                          yaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if "ward" in df.columns and "risk_score" in df.columns:
        wr = df.groupby("ward").agg(avg_risk=("risk_score","mean"),
                                     count=("patient_id","count")).reset_index()
        fig2 = go.Figure(go.Scatter(
            x=wr["ward"], y=wr["avg_risk"]*100,
            mode="markers+text",
            marker=dict(
                size=wr["count"]*10,
                color=wr["avg_risk"],
                colorscale=[[0,C["yellow"]],[1,C["red"]]],
                showscale=False, opacity=0.85,
                line=dict(color=C["border"], width=1),
            ),
            text=wr["count"].apply(lambda x: f"{x}pt"),
            textposition="top center", textfont=dict(color=C["text"],size=10),
            hovertemplate="<b>%{x}</b><br>Avg Risk: %{y:.1f}%<br>Patients: %{text}<extra></extra>",
        ))
        fig2 = apply_theme(fig2, height=240)
        fig2.update_layout(title="Risk Concentration by Ward",
                           yaxis_title="Avg Risk (%)", xaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-label">Patient Clinical Cards</div>', unsafe_allow_html=True)

# ── Patient cards ──────────────────────────────────────────────────────────────
top = df.nlargest(10, "risk_score") if "risk_score" in df.columns else df.head(10)

for _, row in top.iterrows():
    risk   = row.get("risk_score", 0)
    band   = str(row.get("risk_band", "Unknown"))
    action = row.get("recommended_action", "Review")
    color  = RISK_COLORS.get(band, C["blue"])
    icon   = "🔴" if risk>=0.75 else "🟠" if risk>=0.55 else "🟡"
    pid    = row.get("patient_id","?")
    name   = row.get("name", pid)

    with st.expander(f"{icon}  {pid}  —  {name}  ·  Risk {risk:.1%}  ·  {band}", expanded=False):
        ca, cb, cc = st.columns([1,1,1])
        with ca:
            st.markdown(f"""
            <div style="font-size:0.82rem;line-height:2;color:#c8ccd8;">
            <b style="color:#8892a4;">Ward</b><br>{row.get('ward','—')}<br>
            <b style="color:#8892a4;">Age</b><br>{row.get('age','—')}<br>
            <b style="color:#8892a4;">Condition</b><br>{row.get('primary_condition','—')}
            </div>""", unsafe_allow_html=True)
        with cb:
            hr  = row.get('heart_rate','—')
            spo = row.get('spo2_pct','—')
            rr  = row.get('respiratory_rate','—')
            sbp = row.get('systolic_bp','—')
            st.markdown(f"""
            <div style="font-size:0.82rem;line-height:2;color:#c8ccd8;">
            <b style="color:#8892a4;">Heart Rate</b><br><span style="color:{C['red'] if isinstance(hr,float) and hr>120 else C['text']}">{hr} bpm</span><br>
            <b style="color:#8892a4;">SpO₂</b><br><span style="color:{C['red'] if isinstance(spo,float) and spo<90 else C['text']}">{spo}%</span><br>
            <b style="color:#8892a4;">Resp. Rate</b><br>{rr} br/min<br>
            <b style="color:#8892a4;">Systolic BP</b><br>{sbp} mmHg
            </div>""", unsafe_allow_html=True)
        with cc:
            st.markdown(f"""
            <div style="background:{color}18;border:1px solid {color}40;border-radius:10px;
                        padding:1rem;text-align:center;height:100%;">
                <div style="font-size:0.7rem;color:#8892a4;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">Recommended Action</div>
                <div style="font-size:0.88rem;font-weight:600;color:{color};">{action}</div>
            </div>""", unsafe_allow_html=True)
            st.progress(min(float(risk),1.0))

st.divider()
st.markdown('<div class="section-label">Full Table</div>', unsafe_allow_html=True)
disp = [c for c in ["patient_id","name","age","ward","primary_condition",
                      "risk_score","risk_band","recommended_action",
                      "heart_rate","spo2_pct","sepsis_risk_score"] if c in df.columns]
st.dataframe(df[disp].sort_values("risk_score",ascending=False), use_container_width=True, height=350)
st.download_button("⬇ Download CSV", df[disp].to_csv(index=False).encode(), "high_risk.csv","text/csv")
