import streamlit as st
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from analysis.meta_analysis import run_meta_analysis
from analysis.tiktok_analysis import run_tiktok_analysis
from analysis.website_analysis import run_website_analysis
from analysis.report_generator import generate_pdf_report, generate_excel_report
from utils.data_loader import (
    load_meta, load_tiktok,
    load_ga4_traffic_channel, load_ga4_traffic_source,
    load_ga4_user_acquisition, load_ga4_pages, load_ga4_events
)
from utils.alerts import get_all_alerts

st.set_page_config(
    page_title="iDealz Marketing Analytics",
    page_icon="📊", layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.metric-card{background:#f8f9fa;border-radius:10px;padding:16px;border:1px solid #e9ecef;text-align:center;}
.metric-value{font-size:26px;font-weight:700;color:#1a1a2e;}
.metric-label{font-size:12px;color:#6c757d;margin-top:4px;}
.alert-red{background:#fff5f5;border-left:4px solid #e53e3e;padding:10px 14px;border-radius:6px;margin:6px 0;color:#742a2a;font-size:14px;}
.alert-yellow{background:#fffbeb;border-left:4px solid #d69e2e;padding:10px 14px;border-radius:6px;margin:6px 0;color:#744210;font-size:14px;}
.alert-green{background:#f0fff4;border-left:4px solid #38a169;padding:10px 14px;border-radius:6px;margin:6px 0;color:#1c4532;font-size:14px;}
.upload-done{background:#f0fff4;border:1px solid #86efac;border-radius:6px;padding:6px 10px;margin:3px 0;font-size:13px;}
.upload-card{background:#f0f4ff;border:1px dashed #93c5fd;border-radius:6px;padding:6px 10px;margin:3px 0;font-size:13px;}
.section-header{font-size:18px;font-weight:600;color:#1a1a2e;border-bottom:2px solid #e9ecef;padding-bottom:8px;margin:24px 0 16px 0;}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 📊 iDealz Analytics")
    st.markdown("---")
    st.markdown("### 📅 Report Period")
    c1,c2 = st.columns(2)
    with c1: start_date = st.date_input("From", value=datetime(2026,3,30))
    with c2: end_date   = st.date_input("To",   value=datetime(2026,4,5))
    st.markdown("---")
    st.markdown("### 📁 Upload Files")

    st.markdown("**Meta Ads**")
    meta_file = st.file_uploader("Meta export (.xlsx or .csv)", type=['xlsx','xls','csv'], key='meta')

    st.markdown("**TikTok Ads**")
    tiktok_file = st.file_uploader("TikTok export (.xlsx)", type=['xlsx','xls'], key='tiktok')

    st.markdown("**Website — GA4** *(upload all 5)*")
    ga4_ch  = st.file_uploader("Traffic — Channel Group .csv",  type=['csv'], key='ch')
    ga4_src = st.file_uploader("Traffic — Source/Medium .csv",  type=['csv'], key='src')
    ga4_usr = st.file_uploader("User Acquisition .csv",         type=['csv'], key='usr')
    ga4_pgs = st.file_uploader("Pages & Screens .csv",          type=['csv'], key='pgs')
    ga4_evt = st.file_uploader("Events .csv",                   type=['csv'], key='evt')

    st.markdown("---")
    uploads = {'Meta':meta_file,'TikTok':tiktok_file,
               'GA4 Channel':ga4_ch,'GA4 Source':ga4_src,
               'GA4 Users':ga4_usr,'GA4 Pages':ga4_pgs,'GA4 Events':ga4_evt}
    done = sum(1 for v in uploads.values() if v)
    st.markdown(f"**{done}/7 files uploaded**")
    st.progress(done/7)
    for nm,f in uploads.items():
        cls = "upload-done" if f else "upload-card"
        ico = "✅" if f else "⬜"
        st.markdown(f'<div class="{cls}">{ico} {nm}</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("iDealz Marketing Analytics v2.0")

# ── Load data ──
meta_df    = load_meta(meta_file)                      if meta_file else None
tiktok_df  = load_tiktok(tiktok_file)                 if tiktok_file else None
traffic_ch = load_ga4_traffic_channel(ga4_ch)         if ga4_ch else None
traffic_src= load_ga4_traffic_source(ga4_src)         if ga4_src else None
users_df   = load_ga4_user_acquisition(ga4_usr)       if ga4_usr else None
pages_df   = load_ga4_pages(ga4_pgs)                  if ga4_pgs else None
events_df  = load_ga4_events(ga4_evt)                 if ga4_evt else None
ga4_bundle = {'traffic_channel':traffic_ch,'traffic_source':traffic_src,
              'users':users_df,'pages':pages_df,'events':events_df}
any_ga4    = any(v is not None for v in ga4_bundle.values())
any_data   = meta_df is not None or tiktok_df is not None or any_ga4

# ── Header ──
st.title("📊 iDealz Marketing Analytics")
st.caption(f"Period: {start_date.strftime('%d %b %Y')} — {end_date.strftime('%d %b %Y')}  |  Analyst: Shakeeb  |  LK_DigiBrush_iDealz")

if not any_data:
    st.info("👈 Upload your files in the sidebar to begin analysis.")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("**Meta:** Ads Manager → Ads tab → Export XLSX")
    with c2:
        st.markdown("**TikTok:** Ads Manager → Reporting → Export XLSX")
    with c3:
        st.markdown("**GA4:** Reports → Download each CSV (5 files)")
    st.stop()

# ── KPI bar ──
st.markdown("### Weekly Overview")
k1,k2,k3,k4,k5,k6 = st.columns(6)
def kpi(col, val, label):
    col.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

kpi(k1, f"Rs {meta_df['Amount spent (LKR)'].sum():,.0f}" if meta_df is not None else "—", "Meta Spend")
kpi(k2, f"{int(meta_df['Results'].sum()):,}" if meta_df is not None else "—", "Meta Results")
kpi(k3, f"${tiktok_df['Cost'].sum():,.2f}" if tiktok_df is not None else "—", "TikTok Spend")
kpi(k4, f"{tiktok_df['Average play time per video view'].mean():.1f}s" if tiktok_df is not None else "—", "Avg Watch Time")
kpi(k5, f"{int(traffic_ch['Sessions'].sum()):,}" if traffic_ch is not None else "—", "Sessions")
kpi(k6, f"{int(pages_df['Views'].sum()):,}" if pages_df is not None and 'Views' in pages_df.columns else "—", "Page Views")
st.markdown("")

# ── Alerts ──
alerts = get_all_alerts(meta_df, tiktok_df, traffic_ch)
if alerts:
    with st.expander(f"⚠️  {len(alerts)} alert(s) — click to view", expanded=True):
        for a in alerts:
            st.markdown(f'<div class="alert-{a["level"]}">{a["icon"]} <b>{a["title"]}</b> — {a["msg"]}</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Tabs ──
tab1,tab2,tab3,tab4 = st.tabs(["📘 Meta Ads","🎵 TikTok Ads","🌐 Website (GA4)","📄 Weekly Report"])

with tab1:
    if meta_df is None:
        st.info("Upload your Meta Ads XLSX export in the sidebar to see analysis.")
    else:
        run_meta_analysis(meta_df)

with tab2:
    if tiktok_df is None:
        st.info("Upload your TikTok Ads XLSX export in the sidebar to see analysis.")
    else:
        run_tiktok_analysis(tiktok_df)

with tab3:
    if not any_ga4:
        st.info("Upload your GA4 CSV exports in the sidebar. You need up to 5 CSV files from GA4.")
        st.markdown("""
**What to download from GA4 (Reports section):**
| File | Where in GA4 |
|---|---|
| Traffic — Channel Group | Acquisition → Traffic Acquisition → Session primary channel group |
| Traffic — Source/Medium | Acquisition → Traffic Acquisition → Session source/medium |
| User Acquisition | Acquisition → User Acquisition |
| Pages & Screens | Engagement → Pages and screens |
| Events | Engagement → Events |
        """)
    else:
        run_website_analysis(ga4_bundle)

with tab4:
    st.markdown('<div class="section-header">Weekly Report Generator</div>', unsafe_allow_html=True)

    loaded = []
    if meta_df is not None:   loaded.append("Meta ✅")
    if tiktok_df is not None: loaded.append("TikTok ✅")
    if any_ga4:               loaded.append("Website ✅")
    st.markdown(f"**Files loaded:** {'  |  '.join(loaded) if loaded else 'None'}")

    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        analyst = st.text_input("Analyst name", value="Shakeeb")
        period  = st.text_input("Period label",
                    value=f"{start_date.strftime('%d %b')} – {end_date.strftime('%d %b %Y')}")
    with c2:
        recs = st.text_area("Recommendations (one per line)", height=140,
            value="Fix TikTok destination URLs — add WhatsApp link\nAdd UTM tags to Meta and TikTok ads\nShift 25% Instagram budget to Facebook Feed\nSet up GA4 WhatsApp click conversion event\nScale iStore iPhone 16 Pro ad — best CPR Rs 4.02")

    st.markdown("---")
    b1,b2 = st.columns(2)
    with b1:
        if st.button("📄 Download PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Building PDF..."):
                pdf = generate_pdf_report(
                    meta_df, tiktok_df, traffic_ch,
                    analyst, period,
                    recs.strip().split('\n'), alerts,
                    extra={'traffic_source':traffic_src,'users':users_df,'pages':pages_df,'events':events_df}
                )
            st.download_button("⬇️ Save PDF", data=pdf,
                file_name=f"iDealz_Report_{end_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf", use_container_width=True)
            st.success("✅ PDF ready!")
    with b2:
        if st.button("📊 Download Excel Report", use_container_width=True):
            with st.spinner("Building Excel..."):
                xl = generate_excel_report(
                    meta_df, tiktok_df, traffic_ch,
                    period, alerts,
                    extra={'traffic_source':traffic_src,'users':users_df,'pages':pages_df,'events':events_df}
                )
            st.download_button("⬇️ Save Excel", data=xl,
                file_name=f"iDealz_Analysis_{end_date.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
            st.success("✅ Excel ready!")
