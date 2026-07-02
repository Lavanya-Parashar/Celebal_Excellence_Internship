"""Page 4 — ICU Capacity Utilisation"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import plotly.graph_objects as go
from dashboard.utils import inject_css, page_header, require_table, icu_bar_chart, apply_theme, C

st.set_page_config(page_title="ICU Capacity · MedPulse", page_icon="🏥", layout="wide")
inject_css()

with st.sidebar:
    st.markdown('<div style="font-size:1rem;font-weight:700;color:#f0f4ff;padding:0.8rem 0 1.2rem 0;border-bottom:1px solid #1e2230;margin-bottom:0.8rem;">🏥 MedPulse</div>', unsafe_allow_html=True)

page_header("🏥 ICU Capacity Utilisation", "Bed occupancy by unit and floor — proactive admission and discharge planning.")

df = require_table("icu_capacity")
latest = df.groupby("unit_id").last().reset_index()

# ── KPIs ───────────────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
c1.metric("Units Monitored", f"{df['unit_id'].nunique()}")
if "total_beds" in latest.columns:
    total_beds = int(latest["total_beds"].sum())
    total_occ  = int(latest["avg_occupied"].sum()) if "avg_occupied" in latest.columns else 0
    util_pct   = total_occ/total_beds*100 if total_beds else 0
    c2.metric("Total Beds",    f"{total_beds}")
    c3.metric("Occupied",      f"{total_occ}")
    c4.metric("Overall Util.", f"{util_pct:.1f}%",
              delta="Critical" if util_pct>=95 else "High" if util_pct>=80 else "Normal",
              delta_color="inverse" if util_pct>=80 else "normal")

st.markdown("<br>", unsafe_allow_html=True)

# ── Bar + trend ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2,3])
with col1:
    st.plotly_chart(icu_bar_chart(df), use_container_width=True)
with col2:
    if "hour_bucket" in df.columns:
        st.markdown('<div class="section-label">Utilisation Trend by Unit</div>', unsafe_allow_html=True)
        trend = df.groupby(["hour_bucket","unit_id"])["avg_util_pct"].mean().reset_index()
        UNIT_COLORS = {"ICU-A":C["red"],"ICU-B":C["orange"],"CCU":"#a855f7","HDU":C["blue"]}
        fig = go.Figure()
        for uid in trend["unit_id"].unique():
            sub = trend[trend["unit_id"]==uid].sort_values("hour_bucket")
            fig.add_trace(go.Scatter(
                x=sub["hour_bucket"], y=sub["avg_util_pct"],
                mode="lines", name=uid,
                line=dict(color=UNIT_COLORS.get(uid, C["blue"]), width=2),
            ))
        fig.add_hline(y=80, line_dash="dot", line_color=C["orange"], line_width=1)
        fig.add_hline(y=95, line_dash="dot", line_color=C["red"], line_width=1)
        fig = apply_theme(fig, height=310)
        fig.update_layout(yaxis_title="Utilisation %", xaxis_title="Hour",
                          legend=dict(orientation="h",yanchor="bottom",y=1.02))
        st.plotly_chart(fig, use_container_width=True)

# ── Status cards ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-label">Unit Status</div>', unsafe_allow_html=True)
ucols = st.columns(len(latest))
for i, (_, row) in enumerate(latest.iterrows()):
    util = row.get("avg_util_pct", 0)
    status = "🔴 Critical" if util>=95 else "🟡 High" if util>=80 else "🟢 Normal"
    color  = C["red"] if util>=95 else C["orange"] if util>=80 else C["green"]
    with ucols[i]:
        st.markdown(f"""
        <div style="background:#151821;border:1px solid {color}30;border-radius:12px;
                    padding:1rem;text-align:center;border-top:3px solid {color};">
            <div style="font-size:1.1rem;font-weight:700;color:#f0f4ff;">{row['unit_id']}</div>
            <div style="font-size:0.7rem;color:#8892a4;margin:2px 0;">Floor {int(row.get('floor',0))}</div>
            <div style="font-size:1.8rem;font-weight:700;color:{color};margin:0.5rem 0;">{util:.0f}%</div>
            <div style="font-size:0.75rem;color:#8892a4;">{int(row.get('avg_occupied',0))} / {int(row.get('total_beds',0))} beds</div>
            <div style="font-size:0.75rem;margin-top:0.4rem;">{status}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.markdown('<div class="section-label">Raw Data</div>', unsafe_allow_html=True)
st.dataframe(df.sort_values(["unit_id","hour_bucket"]), use_container_width=True, height=280)
st.download_button("⬇ Download CSV", df.to_csv(index=False).encode(), "icu_capacity.csv", "text/csv")
