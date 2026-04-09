import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BLUE  = '#378ADD'
PINK  = '#D4537E'
GREEN = '#639922'
AMBER = '#BA7517'
RED   = '#E24B4A'
TEAL  = '#1D9E75'

def run_meta_analysis(meta_curr, meta_prev=None):
    st.markdown('<div class="section-header">Meta Ads — Performance Overview</div>', unsafe_allow_html=True)
    df = meta_curr

    total_spend   = df['Amount spent (LKR)'].sum()
    total_results = int(df['Results'].sum())
    avg_cpr       = total_spend / total_results if total_results > 0 else 0
    avg_ctr       = df['CTR (link click-through rate)'].mean()
    avg_cpm       = df['CPM (cost per 1,000 impressions)'].mean()
    avg_cpc       = df['CPC (cost per link click)'].mean()
    avg_freq      = df['Frequency'].mean()
    total_impr    = int(df['Impressions'].sum())
    total_reach   = int(df['Reach'].sum())
    total_clicks  = int(df['Link clicks'].sum())

    # Deltas vs previous period
    def delta(curr, prev_df, col, agg='sum'):
        if prev_df is None: return None, 'off'
        pv = prev_df[col].sum() if agg=='sum' else prev_df[col].mean()
        if pv == 0: return None, 'off'
        pct = (curr - pv) / pv * 100
        return f"{pct:+.1f}%", 'normal' if pct > 0 else 'inverse'

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    d,dc = delta(total_spend, meta_prev, 'Amount spent (LKR)')
    c1.metric("Total Spend",    f"Rs {total_spend:,.0f}", d, delta_color=dc or 'off')
    d,dc = delta(total_results, meta_prev, 'Results')
    c2.metric("Total Results",  f"{total_results:,}",     d, delta_color=dc or 'off')
    c3.metric("Cost / Result",  f"Rs {avg_cpr:,.2f}", "⚠ High" if avg_cpr>25 else "Good",
              delta_color="inverse" if avg_cpr>25 else "normal")
    c4.metric("Avg CTR",        f"{avg_ctr:.2f}%", "Good" if avg_ctr>=1.5 else "Low",
              delta_color="normal" if avg_ctr>=1.5 else "inverse")
    c5.metric("Avg CPM",        f"Rs {avg_cpm:,.2f}")
    c6.metric("Avg Frequency",  f"{avg_freq:.2f}", "⚠ High" if avg_freq>3 else "Healthy",
              delta_color="inverse" if avg_freq>3 else "normal")

    st.markdown("---")

    # ── FB vs IG ──
    st.markdown('<div class="section-header">Platform — Facebook vs Instagram</div>', unsafe_allow_html=True)
    if 'Platform' in df.columns:
        plat = df.groupby('Platform').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum'),
            Impressions=('Impressions','sum'), Reach=('Reach','sum'),
            Avg_CPM=('CPM (cost per 1,000 impressions)','mean'),
            Avg_CPC=('CPC (cost per link click)','mean'),
            Avg_CTR=('CTR (link click-through rate)','mean'),
            Avg_Freq=('Frequency','mean'),
        ).round(2).reset_index()
        plat['CPR'] = (plat['Spend']/plat['Results'].replace(0,1)).round(2)
        cmap = {'facebook':BLUE,'instagram':PINK,'Facebook':BLUE,'Instagram':PINK}
        c1,c2,c3 = st.columns(3)
        for col_st, metric, title, fmt in [
            (c1,'Results','Results by Platform','{}'),
            (c2,'CPR','Cost Per Result (lower=better)','Rs {:.0f}'),
            (c3,'Avg_CTR','Avg CTR by Platform','{:.2f}%')]:
            with col_st:
                fig = px.bar(plat, x='Platform', y=metric, color='Platform',
                             text=metric, title=title, color_discrete_map=cmap)
                fig.update_traces(texttemplate=fmt.replace('{}','%{text}').replace('{:.0f}','Rs %{text:.0f}').replace('{:.2f}%','%{text:.2f}%'), textposition='outside')
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
        st.dataframe(plat.style.format({'Spend':'Rs {:,.0f}','Impressions':'{:,}','Reach':'{:,}',
            'Avg_CPM':'Rs {:,.2f}','Avg_CPC':'Rs {:,.2f}','Avg_CTR':'{:.2f}%','CPR':'Rs {:,.2f}','Avg_Freq':'{:.2f}'}),
            use_container_width=True)

    st.markdown("---")

    # ── AD SET — CPM CPC CTR ──
    st.markdown('<div class="section-header">Ad Set Deep Dive — CPM · CPC · CTR</div>', unsafe_allow_html=True)
    if 'Ad set name' in df.columns:
        adset = df.groupby('Ad set name').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum'),
            Avg_CPM=('CPM (cost per 1,000 impressions)','mean'),
            Avg_CPC=('CPC (cost per link click)','mean'),
            Avg_CTR=('CTR (link click-through rate)','mean'),
            Avg_Freq=('Frequency','mean'),
        ).round(2).reset_index()
        adset['CPR'] = (adset['Spend']/adset['Results'].replace(0,1)).round(2)

        c1,c2,c3 = st.columns(3)
        with c1:
            fig = px.bar(adset.sort_values('Avg_CPM'), x='Avg_CPM', y='Ad set name',
                         orientation='h', title='CPM (lowest = cheapest reach)',
                         color='Avg_CPM', color_continuous_scale='Reds', text='Avg_CPM')
            fig.update_traces(texttemplate='Rs %{text:.0f}', textposition='outside')
            fig.update_layout(height=max(300,len(adset)*30), coloraxis_showscale=False,
                              yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(adset.sort_values('Avg_CPC'), x='Avg_CPC', y='Ad set name',
                         orientation='h', title='CPC (lowest = cheapest click)',
                         color='Avg_CPC', color_continuous_scale='Oranges', text='Avg_CPC')
            fig.update_traces(texttemplate='Rs %{text:.0f}', textposition='outside')
            fig.update_layout(height=max(300,len(adset)*30), coloraxis_showscale=False,
                              yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        with c3:
            fig = px.bar(adset.sort_values('Avg_CTR',ascending=False),
                         x='Avg_CTR', y='Ad set name', orientation='h',
                         title='CTR (highest = best)',
                         color='Avg_CTR', color_continuous_scale='Greens', text='Avg_CTR')
            fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig.update_layout(height=max(300,len(adset)*30), coloraxis_showscale=False,
                              yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(adset.style.format({'Spend':'Rs {:,.0f}','Avg_CPM':'Rs {:,.2f}',
            'Avg_CPC':'Rs {:,.2f}','Avg_CTR':'{:.2f}%','CPR':'Rs {:,.2f}','Avg_Freq':'{:.2f}'}),
            use_container_width=True)

    st.markdown("---")

    # ── CAMPAIGN PACING ──
    st.markdown('<div class="section-header">Campaign Pacing vs Budget</div>', unsafe_allow_html=True)
    if 'Ad set name' in df.columns:
        pacing = df.groupby('Ad set name').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum')).round(2).reset_index()
        avg_sp = pacing['Spend'].mean()
        pacing['vs_avg_%'] = ((pacing['Spend']-avg_sp)/avg_sp*100).round(1)
        pacing['Status'] = pacing['vs_avg_%'].apply(
            lambda x: '🔴 Overspending' if x>30 else ('🟡 Slightly over' if x>10
                      else ('🟢 On track' if x>-10 else '⚠ Underspending')))
        fig = px.bar(pacing.sort_values('Spend',ascending=False),
                     x='Ad set name', y='Spend', color='vs_avg_%',
                     color_continuous_scale=[GREEN,AMBER,RED], text='Spend',
                     title='Spend by Ad Set — over/under vs average')
        fig.update_traces(texttemplate='Rs %{text:,.0f}', textposition='outside')
        fig.update_layout(height=360, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pacing[['Ad set name','Spend','Results','vs_avg_%','Status']].style.format(
            {'Spend':'Rs {:,.0f}','vs_avg_%':'{:+.1f}%'}), use_container_width=True)

    st.markdown("---")

    # ── TOP & BOTTOM ADS (Creative Review) ──
    st.markdown('<div class="section-header">Creative Performance — Top & Bottom Ads</div>', unsafe_allow_html=True)
    active = df[df['Results']>0].copy()
    if len(active)>0:
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("✅ **Top 10 — lowest cost per result**")
            best = active.sort_values('Cost per result').head(10)[
                ['Ad name','Platform','Results','Cost per result','Amount spent (LKR)','CTR (link click-through rate)']]
            st.dataframe(best.style.format({'Cost per result':'Rs {:,.2f}',
                'Amount spent (LKR)':'Rs {:,.0f}','CTR (link click-through rate)':'{:.2f}%'}),
                use_container_width=True)
        with c2:
            st.markdown("❌ **Bottom 10 — highest cost per result**")
            worst = active.sort_values('Cost per result',ascending=False).head(10)[
                ['Ad name','Platform','Results','Cost per result','Amount spent (LKR)','CTR (link click-through rate)']]
            st.dataframe(worst.style.format({'Cost per result':'Rs {:,.2f}',
                'Amount spent (LKR)':'Rs {:,.0f}','CTR (link click-through rate)':'{:.2f}%'}),
                use_container_width=True)
        fig = px.scatter(active, x='Amount spent (LKR)', y='CTR (link click-through rate)',
                         color='Platform', size='Results', hover_name='Ad name',
                         title='Spend vs CTR per Ad (bubble = results count)',
                         color_discrete_map={'facebook':BLUE,'instagram':PINK,'Facebook':BLUE,'Instagram':PINK})
        fig.add_hline(y=1.5, line_dash='dash', line_color=AMBER, annotation_text='1.5% benchmark')
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── AUDIENCE SEGMENT & OVERLAP ──
    st.markdown('<div class="section-header">Audience Segment & Overlap Analysis</div>', unsafe_allow_html=True)
    if 'Ad set name' in df.columns:
        df['Audience Type'] = df['Ad set name'].apply(
            lambda x: 'Retargeting' if any(k in str(x).lower()
                for k in ['retarget','remarketing','lookalike','custom','warm','existing'])
            else 'Prospecting')
        seg = df.groupby('Audience Type').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum'),
            Avg_CTR=('CTR (link click-through rate)','mean'),
            Avg_CPM=('CPM (cost per 1,000 impressions)','mean'),
            Avg_Freq=('Frequency','mean'),
        ).round(2).reset_index()
        seg['CPR'] = (seg['Spend']/seg['Results'].replace(0,1)).round(2)
        c1,c2 = st.columns(2)
        with c1:
            fig = px.pie(seg, values='Spend', names='Audience Type',
                         title='Spend: Retargeting vs Prospecting',
                         color_discrete_sequence=[BLUE,AMBER])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(seg, x='Audience Type', y='CPR', color='Audience Type',
                         text='CPR', title='Cost per Result by Audience Type',
                         color_discrete_sequence=[BLUE,AMBER])
            fig.update_traces(texttemplate='Rs %{text:.0f}', textposition='outside')
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(seg.style.format({'Spend':'Rs {:,.0f}','Avg_CTR':'{:.2f}%',
            'Avg_CPM':'Rs {:,.2f}','CPR':'Rs {:,.2f}','Avg_Freq':'{:.2f}'}), use_container_width=True)

    st.markdown("---")

    # ── FREQUENCY & FATIGUE ──
    st.markdown('<div class="section-header">Frequency & Audience Fatigue Check</div>', unsafe_allow_html=True)
    fatigued = df[df['Frequency']>3].sort_values('Frequency',ascending=False)
    if len(fatigued)>0:
        st.markdown(f'<div class="alert-red">🔴 <b>{len(fatigued)} fatigued ads</b> — frequency above 3.0. Refresh creative or expand audience.</div>', unsafe_allow_html=True)
        st.dataframe(fatigued[['Ad name','Platform','Ad set name','Frequency','Amount spent (LKR)','Results']].style.format(
            {'Frequency':'{:.2f}','Amount spent (LKR)':'Rs {:,.0f}'}), use_container_width=True)
    else:
        st.markdown('<div class="alert-green">🟢 No fatigued audiences — all frequency below 3.0</div>', unsafe_allow_html=True)
    fig = px.histogram(df, x='Frequency', nbins=20, title='Frequency Distribution',
                       color_discrete_sequence=[BLUE])
    fig.add_vline(x=3, line_dash='dash', line_color=RED, annotation_text='Fatigue threshold 3.0')
    fig.update_layout(height=280)
    st.plotly_chart(fig, use_container_width=True)

    zero = df[(df['Results']==0)&(df['Amount spent (LKR)']>100)]
    if len(zero)>0:
        st.markdown(f'<div class="alert-red">🔴 <b>{len(zero)} zero-result ads</b> spending budget with no results — pause immediately.</div>', unsafe_allow_html=True)
        st.dataframe(zero[['Ad name','Platform','Amount spent (LKR)','Impressions','Frequency']].style.format(
            {'Amount spent (LKR)':'Rs {:,.0f}','Impressions':'{:,}','Frequency':'{:.2f}'}), use_container_width=True)

    st.markdown("---")

    # ── PLACEMENT ──
    st.markdown('<div class="section-header">Placement Breakdown</div>', unsafe_allow_html=True)
    if 'Placement' in df.columns:
        place = df.groupby('Placement').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum'),
            Avg_CTR=('CTR (link click-through rate)','mean'),
            Avg_CPM=('CPM (cost per 1,000 impressions)','mean'),
        ).round(2).reset_index().sort_values('Results',ascending=False)
        place['CPR'] = (place['Spend']/place['Results'].replace(0,1)).round(2)
        c1,c2 = st.columns(2)
        with c1:
            fig = px.pie(place, values='Spend', names='Placement', title='Spend by Placement',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(place, x='Placement', y='Avg_CTR', text='Avg_CTR',
                         title='CTR by Placement (%)', color='Avg_CTR', color_continuous_scale='Greens')
            fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig.update_layout(height=320, coloraxis_showscale=False, xaxis_tickangle=-20)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(place.style.format({'Spend':'Rs {:,.0f}','Avg_CTR':'{:.2f}%',
            'Avg_CPM':'Rs {:,.2f}','CPR':'Rs {:,.2f}'}), use_container_width=True)

    st.markdown("---")

    # ── MONTHLY WRAP & GROWTH ──
    st.markdown('<div class="section-header">Monthly Performance Wrap & Audience Growth</div>', unsafe_allow_html=True)
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Total Spend",       f"Rs {total_spend:,.0f}")
    m2.metric("Total Results",     f"{total_results:,}")
    m3.metric("Total Impressions", f"{total_impr:,}")
    m4.metric("Total Reach",       f"{total_reach:,}")
    m5.metric("Total Clicks",      f"{total_clicks:,}")

    if meta_prev is not None:
        st.markdown("**vs Previous Period:**")
        prev_spend   = meta_prev['Amount spent (LKR)'].sum()
        prev_results = int(meta_prev['Results'].sum())
        prev_reach   = int(meta_prev['Reach'].sum())
        p1,p2,p3 = st.columns(3)
        p1.metric("Spend Change",   f"Rs {total_spend:,.0f}",
                  f"{(total_spend-prev_spend)/prev_spend*100:+.1f}%" if prev_spend>0 else None)
        p2.metric("Results Change", f"{total_results:,}",
                  f"{(total_results-prev_results)/prev_results*100:+.1f}%" if prev_results>0 else None)
        p3.metric("Reach Change",   f"{total_reach:,}",
                  f"{(total_reach-prev_reach)/prev_reach*100:+.1f}%" if prev_reach>0 else None)
    else:
        st.info("💡 Upload previous period Meta export in the sidebar to see month-over-month audience growth comparison.")

    if 'Ad set name' in df.columns:
        monthly = df.groupby('Ad set name').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum'),
            Reach=('Reach','sum')).round(0).reset_index().sort_values('Spend',ascending=False)
        fig = px.bar(monthly, x='Ad set name', y=['Spend','Results'], barmode='group',
                     title='Spend vs Results by Ad Set — Monthly View',
                     color_discrete_map={'Spend':BLUE,'Results':GREEN})
        fig.update_layout(height=360, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 View full raw Meta data"):
        st.dataframe(df, use_container_width=True)
