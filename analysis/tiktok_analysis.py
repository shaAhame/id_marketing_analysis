import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PINK  = '#D4537E'
AMBER = '#BA7517'
TEAL  = '#1D9E75'
GREEN = '#639922'
RED   = '#E24B4A'
BLUE  = '#378ADD'

def run_tiktok_analysis(df, tt_prev=None):
    df = df.copy()

    # ── Safe column accessor ──────────────────────────────────────────────────
    def col(name, fallbacks=None):
        if name in df.columns: return df[name]
        if fallbacks:
            for fb in fallbacks:
                if fb in df.columns: return df[fb]
        return pd.Series([0] * len(df), index=df.index)

    # ── Normalise column names for this export format ─────────────────────────
    # 'Video views at 100%' → '100% video view rate'
    for src_c, tgt_c in [
        ('Video views at 100%',                 '100% video view rate'),
        ('15-second focused views (paid views)', '6-second video views'),
    ]:
        if src_c in df.columns and tgt_c not in df.columns:
            df = df.rename(columns={src_c: tgt_c})

    # Ensure 2-second views exists (not in new export)
    if '2-second video views' not in df.columns:
        df['2-second video views'] = 0

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">TikTok Ads — Performance Overview</div>',
                unsafe_allow_html=True)

    total_spend  = col('Cost').sum()
    total_views  = int(col('Video views').sum())
    avg_watch    = col('Average play time per video view').mean()
    avg_comp     = col('100% video view rate').mean() * 100
    total_dest   = int(col('Clicks (destination)').sum())
    avg_freq     = col('Frequency').mean()
    total_impr   = int(col('Impressions').sum())
    total_reach  = int(col('Reach').sum())
    total_clicks = int(col('Clicks (all)').sum())

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Spend",      f"${total_spend:,.2f} USD")
    c2.metric("Video Views",      f"{total_views:,}")
    c3.metric("Avg Watch Time",   f"{avg_watch:.1f}s",
              delta="Good" if avg_watch >= 6 else "Low",
              delta_color="normal" if avg_watch >= 6 else "inverse")
    c4.metric("Completion Rate",  f"{avg_comp:.1f}%",
              delta="Low" if avg_comp < 15 else "OK",
              delta_color="inverse" if avg_comp < 15 else "normal")
    c5.metric("Destination Clicks", f"{total_dest}",
              delta="Critical" if total_dest == 0 else "OK",
              delta_color="inverse" if total_dest == 0 else "normal")
    c6.metric("Avg Frequency",    f"{avg_freq:.2f}")

    if total_dest == 0:
        st.markdown(
            '<div class="alert-red">🔴 <b>CRITICAL: Destination CTR = 0%</b> — '
            'No clicks to website or WhatsApp from any TikTok ad. '
            'Check destination URLs and add CTA button in ad settings. '
            'Move CTA to first 3 seconds of video.</div>',
            unsafe_allow_html=True)

    st.markdown("---")

    # ── CAMPAIGN COMPARISON ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">Campaign Comparison</div>',
                unsafe_allow_html=True)

    camp = df.groupby('Campaign name').agg(
        Spend=('Cost', 'sum'),
        Impressions=('Impressions', 'sum'),
        Reach=('Reach', 'sum'),
        Avg_Freq=('Frequency', 'mean'),
        Video_Views=('Video views', 'sum'),
        Avg_Watch=('Average play time per video view', 'mean'),
        Dest_Clicks=('Clicks (destination)', 'sum'),
    ).round(2).reset_index()

    if '100% video view rate' in df.columns:
        camp = camp.merge(
            df.groupby('Campaign name')['100% video view rate'].mean().round(4).rename('Avg_Comp'),
            on='Campaign name', how='left')
        camp['Comp_%'] = (camp['Avg_Comp'] * 100).round(1)
    else:
        camp['Comp_%'] = 0

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(camp, x='Campaign name', y='Spend', color='Campaign name',
                     text='Spend', title='Spend by Campaign (USD)',
                     color_discrete_sequence=[PINK, AMBER, TEAL])
        fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(camp, x='Campaign name', y='Avg_Watch', color='Campaign name',
                     text='Avg_Watch', title='Avg Watch Time (seconds)',
                     color_discrete_sequence=[PINK, AMBER, TEAL])
        fig.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)

    cr_cols = ['Campaign name', 'Spend', 'Impressions', 'Video_Views',
               'Avg_Watch', 'Comp_%', 'Dest_Clicks']
    st.dataframe(camp[cr_cols].style.format({
        'Spend': '${:,.2f}', 'Impressions': '{:,}', 'Video_Views': '{:,}',
        'Avg_Watch': '{:.1f}s', 'Comp_%': '{:.1f}%'
    }), use_container_width=True)

    st.markdown("---")

    # ── VIDEO METRICS AUDIT ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">Video Metrics Audit — Completion & Watch Time</div>',
                unsafe_allow_html=True)

    df['comp_%'] = (col('100% video view rate') * 100).round(1)
    df['2sec_%'] = (col('2-second video views') /
                    col('Video views').replace(0, 1) * 100).round(1)
    df['6sec_%'] = (col('6-second video views') /
                    col('Video views').replace(0, 1) * 100).round(1)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(df.sort_values('comp_%', ascending=False),
                     x='Ad name', y='comp_%', color='comp_%',
                     text='comp_%', title='Completion Rate per Ad (%)',
                     color_continuous_scale=[RED, AMBER, GREEN, TEAL])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=360, xaxis_tickangle=-30,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(df.sort_values('Average play time per video view', ascending=False),
                     x='Ad name', y='Average play time per video view',
                     color='Average play time per video view',
                     text='Average play time per video view',
                     title='Avg Watch Time per Ad (seconds)',
                     color_continuous_scale=[RED, AMBER, GREEN, TEAL])
        fig.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
        fig.update_layout(height=360, xaxis_tickangle=-30,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Drop-off summary
    avg_6s = df['6sec_%'].mean()
    avg_fl = df['comp_%'].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("Watched 6+ sec",   f"{avg_6s:.1f}%",
              delta="Good" if avg_6s > 30 else "Low",
              delta_color="normal" if avg_6s > 30 else "inverse")
    c2.metric("Full Completion",  f"{avg_fl:.1f}%",
              delta="Good" if avg_fl > 25 else "Low",
              delta_color="normal" if avg_fl > 25 else "inverse")
    c3.metric("Dest. Clicks",     str(total_dest),
              delta="Critical" if total_dest == 0 else "OK",
              delta_color="inverse" if total_dest == 0 else "normal")

    st.markdown("**Benchmark:** 🔴 <10% Very weak | 🟡 10–25% Below avg | 🟢 25%+ Good")

    vm_cols = ['Ad name', 'Campaign name', 'comp_%', '6sec_%',
               'Average play time per video view', 'Clicks (destination)']
    vm_fmt  = {'comp_%': '{:.1f}%', '6sec_%': '{:.1f}%',
               'Average play time per video view': '{:.1f}s'}
    st.dataframe(df[vm_cols].rename(columns={
        'comp_%': 'Completion %', '6sec_%': '6-sec %',
        'Average play time per video view': 'Watch Time (s)',
    }).style.format(vm_fmt), use_container_width=True)

    st.markdown("---")

    # ── DESTINATION CTR AUDIT ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">Destination CTR Audit — Zero CTR Creatives</div>',
                unsafe_allow_html=True)

    ctr_df = df[['Ad name', 'Campaign name', 'CTR (destination)',
                 'Clicks (destination)', 'Impressions', 'Cost']].copy()

    if ctr_df['Clicks (destination)'].sum() == 0:
        st.markdown(
            '<div class="alert-red">🔴 <b>ALL ads have zero destination clicks.</b> '
            'Nobody is clicking to WhatsApp or idealz.lk.<br>'
            '<b>Fix:</b> (1) Set destination URL in every ad. '
            '(2) Add "Message Us" CTA button. '
            '(3) Move CTA text to first 3 seconds.</div>',
            unsafe_allow_html=True)
    else:
        zero_ctr = ctr_df[ctr_df['Clicks (destination)'] == 0]
        if len(zero_ctr) > 0:
            st.markdown(
                f'<div class="alert-yellow">🟡 <b>{len(zero_ctr)} ads</b> '
                f'have zero destination clicks — review these creatives.</div>',
                unsafe_allow_html=True)
        fig = px.bar(ctr_df.sort_values('CTR (destination)', ascending=False),
                     x='Ad name', y='CTR (destination)',
                     title='Destination CTR per Ad',
                     color='CTR (destination)',
                     color_continuous_scale=[RED, AMBER, GREEN])
        fig.add_hline(y=0.005, line_dash='dash', line_color=AMBER,
                      annotation_text='0.5% benchmark')
        fig.update_layout(height=340, xaxis_tickangle=-30,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(ctr_df.style.format({
        'CTR (destination)': '{:.4f}', 'Cost': '${:,.2f}',
        'Impressions': '{:,}'
    }), use_container_width=True)

    st.markdown("---")

    # ── VIDEO ENGAGEMENT FUNNEL ───────────────────────────────────────────────
    st.markdown('<div class="section-header">Video Engagement Funnel — Drop-off Analysis</div>',
                unsafe_allow_html=True)

    sec6 = int(col('6-second video views').sum())
    full = int((col('Video views') * col('100% video view rate')).sum())

    funnel = pd.DataFrame({
        'Stage': ['Impressions', 'Video Views', '6-sec Views',
                  'Full Views', 'Dest. Clicks'],
        'Count': [total_impr, total_views, sec6, full, total_dest]
    })
    fig = go.Figure(go.Funnel(
        y=funnel['Stage'], x=funnel['Count'],
        textinfo='value+percent initial',
        marker_color=[PINK] * 5))
    fig.update_layout(title='Full Video Engagement Funnel', height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── REACH & ORGANIC PERFORMANCE ───────────────────────────────────────────
    st.markdown('<div class="section-header">Reach & Organic Performance</div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Impressions", f"{total_impr:,}")
    c2.metric("Total Reach",       f"{total_reach:,}")
    c3.metric("Avg Frequency",     f"{avg_freq:.2f}")

    reach_camp = df.groupby('Campaign name').agg(
        Impressions=('Impressions', 'sum'),
        Reach=('Reach', 'sum'),
        Clicks=('Clicks (all)', 'sum'),
    ).round(2).reset_index()
    fig = px.bar(reach_camp, x='Campaign name',
                 y=['Impressions', 'Reach'], barmode='group',
                 title='Impressions vs Reach by Campaign',
                 color_discrete_map={'Impressions': PINK, 'Reach': TEAL})
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    st.info("💡 **Hashtag analysis:** Go to ads.tiktok.com/creative-center → "
            "Trending Hashtags → filter Electronics / Sri Lanka to find top hashtags.")

    st.markdown("---")

    # ── MONTHLY BENCHMARKS ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Monthly Benchmarks Summary</div>',
                unsafe_allow_html=True)

    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric("Total Spend",       f"${total_spend:,.2f}")
    b2.metric("Total Impressions", f"{total_impr:,}")
    b3.metric("Total Reach",       f"{total_reach:,}")
    b4.metric("Total Video Views", f"{total_views:,}")
    b5.metric("Dest. Clicks",      str(total_dest),
              delta="Critical" if total_dest == 0 else "OK",
              delta_color="inverse" if total_dest == 0 else "normal")

    if tt_prev is not None:
        pp1, pp2, pp3 = st.columns(3)
        prev_spend = tt_prev['Cost'].sum() if 'Cost' in tt_prev.columns else 0
        prev_views = int(tt_prev['Video views'].sum()) if 'Video views' in tt_prev.columns else 0
        prev_reach = int(tt_prev['Reach'].sum()) if 'Reach' in tt_prev.columns else 0
        pp1.metric("Spend",  f"${total_spend:,.2f}",
                   f"{(total_spend-prev_spend)/prev_spend*100:+.1f}%" if prev_spend > 0 else None)
        pp2.metric("Views",  f"{total_views:,}",
                   f"{(total_views-prev_views)/prev_views*100:+.1f}%" if prev_views > 0 else None)
        pp3.metric("Reach",  f"{total_reach:,}",
                   f"{(total_reach-prev_reach)/prev_reach*100:+.1f}%" if prev_reach > 0 else None)
    else:
        st.info("💡 Upload previous period TikTok export to compare month-over-month.")

    with st.expander("📋 View full raw TikTok data"):
        st.dataframe(df, use_container_width=True)
