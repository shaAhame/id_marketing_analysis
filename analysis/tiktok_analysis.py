import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PINK  = '#D4537E'
AMBER = '#BA7517'
TEAL  = '#1D9E75'

def watch_score(s):
    if s >= 10:  return ('Excellent', '#1D9E75')
    elif s >= 6: return ('Good',      '#639922')
    elif s >= 3: return ('Weak',      '#BA7517')
    else:        return ('Very Weak', '#E24B4A')

def run_tiktok_analysis(df):
    st.markdown('<div class="section-header">TikTok Ads — Performance Overview</div>', unsafe_allow_html=True)

    total_spend   = df['Cost'].sum()
    total_views   = int(df['Video views'].sum())
    avg_watch     = df['Average play time per video view'].mean()
    avg_comp      = df['100% video view rate'].mean() * 100
    total_dest    = int(df['Clicks (destination)'].sum())
    avg_freq      = df['Frequency'].mean()

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Spend",       f"${total_spend:,.2f} USD")
    c2.metric("Video Views",       f"{total_views:,}")
    c3.metric("Avg Watch Time",    f"{avg_watch:.1f}s",
              delta="Good" if avg_watch >= 6 else "Needs work",
              delta_color="normal" if avg_watch >= 6 else "inverse")
    c4.metric("Completion Rate",   f"{avg_comp:.1f}%",
              delta="Low" if avg_comp < 15 else None, delta_color="inverse")
    c5.metric("Destination Clicks",f"{total_dest:,}",
              delta="Critical: 0" if total_dest == 0 else None, delta_color="inverse")
    c6.metric("Avg Frequency",     f"{avg_freq:.2f}")

    if total_dest == 0:
        st.markdown('<div class="alert-red">🔴 <b>CRITICAL: Destination CTR = 0%</b> — No clicks to website/WhatsApp from any TikTok ad. Check destination URLs and add CTA in first 5 seconds of each video.</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Campaign comparison
    st.markdown('<div class="section-header">Campaign Comparison</div>', unsafe_allow_html=True)

    camp = df.groupby('Campaign name').agg(
        Spend=('Cost',                           'sum'),
        Impressions=('Impressions',              'sum'),
        Reach=('Reach',                          'sum'),
        Avg_Frequency=('Frequency',              'mean'),
        Video_Views=('Video views',              'sum'),
        Avg_Watch_Time=('Average play time per video view', 'mean'),
        Avg_Completion=('100% video view rate',  'mean'),
        Dest_Clicks=('Clicks (destination)',     'sum'),
    ).round(2).reset_index()
    camp['Completion_%'] = (camp['Avg_Completion'] * 100).round(1)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(camp, x='Campaign name', y='Spend',
                     title='Spend by Campaign (USD)',
                     color='Campaign name', text='Spend',
                     color_discrete_sequence=[PINK, AMBER, TEAL])
        fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
        fig.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(camp, x='Campaign name', y='Avg_Watch_Time',
                     title='Avg Watch Time by Campaign (seconds)',
                     color='Campaign name', text='Avg_Watch_Time',
                     color_discrete_sequence=[PINK, AMBER, TEAL])
        fig.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
        fig.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(camp[['Campaign name','Spend','Video_Views','Avg_Watch_Time','Completion_%','Dest_Clicks']].style.format({
        'Spend': '${:,.2f}',
        'Video_Views': '{:,}',
        'Avg_Watch_Time': '{:.1f}s',
        'Completion_%': '{:.1f}%',
    }), use_container_width=True)

    st.markdown("---")

    # Video completion audit
    st.markdown('<div class="section-header">Video Completion Rate Audit</div>', unsafe_allow_html=True)

    df['completion_%'] = (df['100% video view rate'] * 100).round(1)
    df['2sec_%']       = (df['2-second video views'] / df['Video views'].replace(0,1) * 100).round(1)
    df['6sec_%']       = (df['6-second video views'] / df['Video views'].replace(0,1) * 100).round(1)
    df['watch_label']  = df['Average play time per video view'].apply(lambda x: watch_score(x)[0])
    df['watch_color']  = df['Average play time per video view'].apply(lambda x: watch_score(x)[1])

    fig = px.bar(df.sort_values('completion_%', ascending=False),
                 x='Ad name', y='completion_%',
                 color='completion_%',
                 color_continuous_scale=['#E24B4A','#BA7517','#639922','#1D9E75'],
                 title='Video Completion Rate per Ad (%)',
                 text='completion_%')
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(height=380, xaxis_tickangle=-30, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Completion rate benchmarks:** 🔴 < 10% Very weak  |  🟡 10–25% Below avg  |  🟢 25%+ Good")

    st.markdown("---")

    # Watch time analysis
    st.markdown('<div class="section-header">Watch Time Analysis</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(df.sort_values('Average play time per video view', ascending=False),
                     x='Ad name', y='Average play time per video view',
                     title='Average Watch Time per Ad (seconds)',
                     color='Average play time per video view',
                     color_continuous_scale=['#E24B4A','#BA7517','#1D9E75'],
                     text='Average play time per video view')
        fig.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
        fig.update_layout(height=360, xaxis_tickangle=-30, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Watch time scores per ad**")
        watch_table = df[['Ad name','Average play time per video view','watch_label','completion_%']].copy()
        watch_table.columns = ['Ad name','Watch time (s)','Score','Completion %']
        st.dataframe(watch_table.sort_values('Watch time (s)', ascending=False), use_container_width=True)

    st.markdown("**Benchmarks:** 0–3s Very weak  |  3–6s Needs work  |  6–10s Good  |  10s+ Excellent")

    st.markdown("---")

    # Video funnel
    st.markdown('<div class="section-header">Video Engagement Funnel</div>', unsafe_allow_html=True)

    total_imp   = int(df['Impressions'].sum())
    total_views2= int(df['Video views'].sum())
    sec2_views  = int(df['2-second video views'].sum())
    sec6_views  = int(df['6-second video views'].sum())
    full_views  = int((df['Video views'] * df['100% video view rate']).sum())
    dest_clicks = int(df['Clicks (destination)'].sum())

    funnel = pd.DataFrame({
        'Stage':['Impressions','Video Views','2-sec Views','6-sec Views','Full Views','Dest. Clicks'],
        'Count':[total_imp, total_views2, sec2_views, sec6_views, full_views, dest_clicks]
    })
    fig = go.Figure(go.Funnel(
        y=funnel['Stage'], x=funnel['Count'],
        textinfo="value+percent initial",
        marker_color=[PINK]*6
    ))
    fig.update_layout(title='Video Engagement Funnel', height=380)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 View raw TikTok data"):
        st.dataframe(df, use_container_width=True)
