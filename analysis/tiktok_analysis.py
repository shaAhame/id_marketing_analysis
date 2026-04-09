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

def watch_score(s):
    if s>=10:  return ('Excellent ✅', GREEN)
    elif s>=6: return ('Good ✅',      TEAL)
    elif s>=3: return ('Weak ⚠',      AMBER)
    else:      return ('Very Weak ❌', RED)

def run_tiktok_analysis(df, tt_prev=None):
    st.markdown('<div class="section-header">TikTok Ads — Performance Overview</div>', unsafe_allow_html=True)

    total_spend  = df['Cost'].sum()
    total_views  = int(df['Video views'].sum())
    avg_watch    = df['Average play time per video view'].mean()
    avg_comp     = df['100% video view rate'].mean()*100
    total_dest   = int(df['Clicks (destination)'].sum())
    avg_freq     = df['Frequency'].mean()
    total_impr   = int(df['Impressions'].sum())
    total_reach  = int(df['Reach'].sum())

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Spend",       f"${total_spend:,.2f} USD")
    c2.metric("Video Views",       f"{total_views:,}")
    c3.metric("Avg Watch Time",    f"{avg_watch:.1f}s",
              delta="Good" if avg_watch>=6 else "Low",
              delta_color="normal" if avg_watch>=6 else "inverse")
    c4.metric("Completion Rate",   f"{avg_comp:.1f}%",
              delta="Low" if avg_comp<15 else "OK",
              delta_color="inverse" if avg_comp<15 else "normal")
    c5.metric("Destination Clicks",f"{total_dest}",
              delta="Critical" if total_dest==0 else "OK",
              delta_color="inverse" if total_dest==0 else "normal")
    c6.metric("Avg Frequency",     f"{avg_freq:.2f}")

    if total_dest==0:
        st.markdown('<div class="alert-red">🔴 <b>CRITICAL: Destination CTR = 0%</b> — No clicks to website or WhatsApp from any TikTok ad. Check destination URLs and add CTA button in ad settings. Move CTA to first 3 seconds of video.</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── CAMPAIGN COMPARISON ──
    st.markdown('<div class="section-header">Campaign Comparison</div>', unsafe_allow_html=True)
    camp = df.groupby('Campaign name').agg(
        Spend=('Cost','sum'), Impressions=('Impressions','sum'), Reach=('Reach','sum'),
        Avg_Freq=('Frequency','mean'), Video_Views=('Video views','sum'),
        Avg_Watch=('Average play time per video view','mean'),
        Avg_Comp=('100% video view rate','mean'),
        Dest_Clicks=('Clicks (destination)','sum'),
        All_Clicks=('Clicks (all)','sum'),
    ).round(2).reset_index()
    camp['Comp_%'] = (camp['Avg_Comp']*100).round(1)
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(camp, x='Campaign name', y='Spend', color='Campaign name', text='Spend',
                     title='Spend by Campaign (USD)', color_discrete_sequence=[PINK,AMBER,TEAL])
        fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(camp, x='Campaign name', y='Avg_Watch', color='Campaign name', text='Avg_Watch',
                     title='Avg Watch Time (seconds)', color_discrete_sequence=[PINK,AMBER,TEAL])
        fig.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(camp[['Campaign name','Spend','Video_Views','Avg_Watch','Comp_%','Dest_Clicks','Avg_Freq']].style.format(
        {'Spend':'${:,.2f}','Video_Views':'{:,}','Avg_Watch':'{:.1f}s','Comp_%':'{:.1f}%','Avg_Freq':'{:.2f}'}),
        use_container_width=True)

    st.markdown("---")

    # ── VIDEO METRICS AUDIT — completion + watch time ──
    st.markdown('<div class="section-header">Video Metrics Audit — Completion Rate & Watch Time</div>', unsafe_allow_html=True)
    df['comp_%']  = (df['100% video view rate']*100).round(1)
    df['2sec_%']  = (df['2-second video views']/df['Video views'].replace(0,1)*100).round(1)
    df['6sec_%']  = (df['6-second video views']/df['Video views'].replace(0,1)*100).round(1)
    df['w_label'] = df['Average play time per video view'].apply(lambda x: watch_score(x)[0])

    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(df.sort_values('comp_%',ascending=False),
                     x='Ad name', y='comp_%', color='comp_%', text='comp_%',
                     title='Completion Rate per Ad (%)',
                     color_continuous_scale=[RED,AMBER,GREEN,TEAL])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=360, xaxis_tickangle=-30, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(df.sort_values('Average play time per video view',ascending=False),
                     x='Ad name', y='Average play time per video view',
                     color='Average play time per video view', text='Average play time per video view',
                     title='Avg Watch Time per Ad (seconds)',
                     color_continuous_scale=[RED,AMBER,GREEN,TEAL])
        fig.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
        fig.update_layout(height=360, xaxis_tickangle=-30, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Drop-off summary
    avg_2s = df['2sec_%'].mean()
    avg_6s = df['6sec_%'].mean()
    avg_fl = df['comp_%'].mean()
    c1,c2,c3 = st.columns(3)
    c1.metric("Watched 2+ sec", f"{avg_2s:.1f}%", delta="Good" if avg_2s>50 else "Low",
              delta_color="normal" if avg_2s>50 else "inverse")
    c2.metric("Watched 6+ sec", f"{avg_6s:.1f}%", delta="Good" if avg_6s>30 else "Low",
              delta_color="normal" if avg_6s>30 else "inverse")
    c3.metric("Full Completion",f"{avg_fl:.1f}%", delta="Good" if avg_fl>25 else "Low",
              delta_color="normal" if avg_fl>25 else "inverse")
    st.markdown("**Benchmark:** 🔴 <10% Very weak  |  🟡 10–25% Below avg  |  🟢 25%+ Good")

    st.dataframe(df[['Ad name','Campaign name','comp_%','2sec_%','6sec_%',
                      'Average play time per video view','w_label']].rename(columns={
        'comp_%':'Completion %','2sec_%':'2-sec %','6sec_%':'6-sec %',
        'Average play time per video view':'Watch Time (s)','w_label':'Score'}),
        use_container_width=True)

    st.markdown("---")

    # ── DESTINATION CTR AUDIT ──
    st.markdown('<div class="section-header">Destination CTR Audit — Zero CTR Creatives</div>', unsafe_allow_html=True)
    ctr_df = df[['Ad name','Campaign name','CTR (destination)','Clicks (destination)','Impressions','Cost']].copy()
    if ctr_df['Clicks (destination)'].sum()==0:
        st.markdown('<div class="alert-red">🔴 <b>ALL ads have zero destination clicks.</b> Nobody is clicking through to WhatsApp or idealz.lk.<br><b>Fix:</b> (1) Set destination URL in every ad. (2) Add "Message Us" CTA button. (3) Move CTA text to first 3 seconds.</div>', unsafe_allow_html=True)
    else:
        zero_ctr = ctr_df[ctr_df['Clicks (destination)']==0]
        if len(zero_ctr)>0:
            st.markdown(f'<div class="alert-yellow">🟡 <b>{len(zero_ctr)} ads</b> have zero destination clicks — review these creatives.</div>', unsafe_allow_html=True)
        fig = px.bar(ctr_df.sort_values('CTR (destination)',ascending=False),
                     x='Ad name', y='CTR (destination)', title='Destination CTR per Ad',
                     color='CTR (destination)', color_continuous_scale=[RED,AMBER,GREEN])
        fig.add_hline(y=0.005, line_dash='dash', line_color=AMBER, annotation_text='0.5% benchmark')
        fig.update_layout(height=340, xaxis_tickangle=-30, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(ctr_df.style.format({'CTR (destination)':'{:.4f}','Cost':'${:,.2f}','Impressions':'{:,}'}),
        use_container_width=True)

    st.markdown("---")

    # ── VIDEO ENGAGEMENT FUNNEL ──
    st.markdown('<div class="section-header">Video Engagement Funnel — Drop-off Analysis</div>', unsafe_allow_html=True)
    sec2 = int(df['2-second video views'].sum())
    sec6 = int(df['6-second video views'].sum())
    full = int((df['Video views']*df['100% video view rate']).sum())
    funnel = pd.DataFrame({
        'Stage':['Impressions','Video Views','2-sec Views','6-sec Views','Full Views','Dest. Clicks'],
        'Count':[total_impr, total_views, sec2, sec6, full, total_dest]
    })
    fig = go.Figure(go.Funnel(y=funnel['Stage'], x=funnel['Count'],
                               textinfo='value+percent initial', marker_color=[PINK]*6))
    fig.update_layout(title='Full Video Engagement Funnel', height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── HASHTAG & ORGANIC REACH ──
    st.markdown('<div class="section-header">Reach & Organic Performance</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric("Total Impressions", f"{total_impr:,}")
    c2.metric("Total Reach",       f"{total_reach:,}")
    c3.metric("Avg Frequency",     f"{avg_freq:.2f}")
    reach_camp = df.groupby('Campaign name').agg(
        Impressions=('Impressions','sum'), Reach=('Reach','sum'),
        Freq=('Frequency','mean'), Clicks=('Clicks (all)','sum')).round(2).reset_index()
    fig = px.bar(reach_camp, x='Campaign name', y=['Impressions','Reach'], barmode='group',
                 title='Impressions vs Reach by Campaign',
                 color_discrete_map={'Impressions':PINK,'Reach':TEAL})
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    st.info("💡 **Hashtag analysis:** Go to ads.tiktok.com/creative-center → Trending Hashtags → filter Electronics / Sri Lanka to find top hashtags for your next campaign.")

    st.markdown("---")

    # ── TOP CONTENT BENCHMARKING ──
    st.markdown('<div class="section-header">Top Content — Best Performing Creatives</div>', unsafe_allow_html=True)
    top5 = df.sort_values('Average play time per video view',ascending=False).head(5)[
        ['Ad name','Campaign name','Average play time per video view','comp_%','Video views','Cost']]
    st.markdown("**Your top 5 creatives by watch time:**")
    st.dataframe(top5.style.format({'Average play time per video view':'{:.1f}s',
        'comp_%':'{:.1f}%','Video views':'{:,}','Cost':'${:,.2f}'}), use_container_width=True)
    st.info("💡 **Competitor benchmarking:** TikTok Creative Center → Top Ads → Industry: Electronics, Country: Sri Lanka. Compare hook style, video length, and CTA vs your top ads above.")

    st.markdown("---")

    # ── MONTHLY BENCHMARKS ──
    st.markdown('<div class="section-header">Monthly Benchmarks Summary</div>', unsafe_allow_html=True)
    b1,b2,b3,b4,b5 = st.columns(5)
    b1.metric("Total Spend",       f"${total_spend:,.2f}")
    b2.metric("Total Impressions", f"{total_impr:,}")
    b3.metric("Total Reach",       f"{total_reach:,}")
    b4.metric("Total Video Views", f"{total_views:,}")
    b5.metric("Dest. Clicks",      str(total_dest),
              delta="Critical" if total_dest==0 else "OK",
              delta_color="inverse" if total_dest==0 else "normal")

    if tt_prev is not None:
        st.markdown("**vs Previous Period:**")
        pp1,pp2,pp3 = st.columns(3)
        prev_sp = tt_prev['Cost'].sum()
        prev_vw = int(tt_prev['Video views'].sum())
        prev_rc = int(tt_prev['Reach'].sum())
        pp1.metric("Spend",  f"${total_spend:,.2f}", f"{(total_spend-prev_sp)/prev_sp*100:+.1f}%" if prev_sp>0 else None)
        pp2.metric("Views",  f"{total_views:,}",     f"{(total_views-prev_vw)/prev_vw*100:+.1f}%" if prev_vw>0 else None)
        pp3.metric("Reach",  f"{total_reach:,}",     f"{(total_reach-prev_rc)/prev_rc*100:+.1f}%" if prev_rc>0 else None)
    else:
        st.info("💡 Upload previous period TikTok export in the sidebar to compare month-over-month performance.")

    with st.expander("📋 View full raw TikTok data"):
        st.dataframe(df, use_container_width=True)
