import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BLUE  = '#378ADD'
PINK  = '#D4537E'
GREEN = '#639922'
AMBER = '#BA7517'

def run_meta_analysis(df):
    st.markdown('<div class="section-header">Meta Ads — Performance Overview</div>', unsafe_allow_html=True)

    # KPI row
    total_spend   = df['Amount spent (LKR)'].sum()
    total_results = int(df['Results'].sum())
    avg_cpr       = total_spend / total_results if total_results > 0 else 0
    avg_ctr       = df['CTR (link click-through rate)'].mean()
    avg_cpm       = df['CPM (cost per 1,000 impressions)'].mean()
    avg_freq      = df['Frequency'].mean()

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Spend",    f"Rs {total_spend:,.0f}")
    c2.metric("Total Results",  f"{total_results:,}")
    c3.metric("Cost / Result",  f"Rs {avg_cpr:,.2f}")
    c4.metric("Avg CTR",        f"{avg_ctr:.2f}%")
    c5.metric("Avg CPM",        f"Rs {avg_cpm:,.2f}")
    c6.metric("Avg Frequency",  f"{avg_freq:.2f}", delta="⚠️ High" if avg_freq > 3 else None, delta_color="inverse")

    st.markdown("---")

    # FB vs IG
    st.markdown('<div class="section-header">Platform Comparison — Facebook vs Instagram</div>', unsafe_allow_html=True)

    if 'Platform' in df.columns:
        plat = df.groupby('Platform').agg(
            Spend=('Amount spent (LKR)',            'sum'),
            Results=('Results',                      'sum'),
            Avg_CPM=('CPM (cost per 1,000 impressions)', 'mean'),
            Avg_CPC=('CPC (cost per link click)',    'mean'),
            Avg_CTR=('CTR (link click-through rate)','mean'),
            Impressions=('Impressions',              'sum'),
            Reach=('Reach',                          'sum'),
        ).round(2).reset_index()
        plat['Cost_per_result'] = (plat['Spend'] / plat['Results'].replace(0,1)).round(2)

        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(plat, x='Platform', y='Results',
                         color='Platform', text='Results',
                         title='Results by Platform',
                         color_discrete_map={'Facebook': BLUE, 'Instagram': PINK})
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, height=320)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = px.bar(plat, x='Platform', y='Cost_per_result',
                         color='Platform', text='Cost_per_result',
                         title='Cost Per Result by Platform (lower = better)',
                         color_discrete_map={'Facebook': BLUE, 'Instagram': PINK})
            fig.update_traces(texttemplate='Rs %{text:.0f}', textposition='outside')
            fig.update_layout(showlegend=False, height=320)
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(plat.style.format({
            'Spend': 'Rs {:,.0f}',
            'Avg_CPM': 'Rs {:,.2f}',
            'Avg_CPC': 'Rs {:,.2f}',
            'Avg_CTR': '{:.2f}%',
            'Cost_per_result': 'Rs {:,.2f}'
        }), use_container_width=True)

    st.markdown("---")

    # Ad set analysis
    st.markdown('<div class="section-header">Ad Set Analysis — CPM · CPC · CTR</div>', unsafe_allow_html=True)

    if 'Ad set name' in df.columns:
        adset = df.groupby('Ad set name').agg(
            Spend=('Amount spent (LKR)',             'sum'),
            Results=('Results',                       'sum'),
            Avg_CPM=('CPM (cost per 1,000 impressions)', 'mean'),
            Avg_CPC=('CPC (cost per link click)',     'mean'),
            Avg_CTR=('CTR (link click-through rate)', 'mean'),
            Avg_Frequency=('Frequency',               'mean'),
        ).round(2).reset_index()
        adset['Cost_per_result'] = (adset['Spend'] / adset['Results'].replace(0,1)).round(2)

        metric = st.selectbox("Chart metric", ['Avg_CPM','Avg_CPC','Avg_CTR','Results','Cost_per_result'])
        fig = px.bar(adset.sort_values(metric, ascending=False),
                     x='Ad set name', y=metric,
                     title=f'{metric} by Ad Set',
                     color=metric, color_continuous_scale='Blues')
        fig.update_layout(height=360, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Top vs bottom ads
    st.markdown('<div class="section-header">Top & Bottom Performing Ads</div>', unsafe_allow_html=True)

    active = df[df['Results'] > 0].copy()
    if len(active) > 0:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("✅ **Top 10 ads — lowest cost per result**")
            best = active.sort_values('Cost per result').head(10)[
                ['Ad name','Platform','Results','Cost per result','Amount spent (LKR)','CTR (link click-through rate)']
            ]
            st.dataframe(best.style.format({
                'Cost per result': 'Rs {:,.2f}',
                'Amount spent (LKR)': 'Rs {:,.0f}',
                'CTR (link click-through rate)': '{:.2f}%'
            }), use_container_width=True)

        with c2:
            st.markdown("❌ **Bottom 10 ads — highest cost per result**")
            worst = active.sort_values('Cost per result', ascending=False).head(10)[
                ['Ad name','Platform','Results','Cost per result','Amount spent (LKR)','CTR (link click-through rate)']
            ]
            st.dataframe(worst.style.format({
                'Cost per result': 'Rs {:,.2f}',
                'Amount spent (LKR)': 'Rs {:,.0f}',
                'CTR (link click-through rate)': '{:.2f}%'
            }), use_container_width=True)

    st.markdown("---")

    # Frequency fatigue
    st.markdown('<div class="section-header">Frequency & Fatigue Check</div>', unsafe_allow_html=True)

    fatigued = df[df['Frequency'] > 3].sort_values('Frequency', ascending=False)
    if len(fatigued) > 0:
        st.markdown(f'<div class="alert-red">🔴 <b>{len(fatigued)} fatigued ads</b> — frequency above 3.0. These audiences need refreshing or expanding.</div>', unsafe_allow_html=True)
        st.dataframe(fatigued[['Ad name','Platform','Frequency','Amount spent (LKR)','Results']].style.format({
            'Frequency': '{:.2f}',
            'Amount spent (LKR)': 'Rs {:,.0f}'
        }), use_container_width=True)
    else:
        st.markdown('<div class="alert-green">🟢 No fatigued audiences — all frequency below 3.0</div>', unsafe_allow_html=True)

    # Zero result ads
    zero = df[(df['Results'] == 0) & (df['Amount spent (LKR)'] > 100)]
    if len(zero) > 0:
        st.markdown(f'<div class="alert-red">🔴 <b>{len(zero)} zero-result ads</b> spending budget with no results — consider pausing.</div>', unsafe_allow_html=True)
        st.dataframe(zero[['Ad name','Platform','Amount spent (LKR)','Impressions']].style.format({
            'Amount spent (LKR)': 'Rs {:,.0f}',
            'Impressions': '{:,}'
        }), use_container_width=True)

    st.markdown("---")

    # Placement breakdown
    if 'Placement' in df.columns:
        st.markdown('<div class="section-header">Placement Breakdown</div>', unsafe_allow_html=True)
        place = df.groupby('Placement').agg(
            Spend=('Amount spent (LKR)', 'sum'),
            Results=('Results', 'sum'),
            Avg_CTR=('CTR (link click-through rate)', 'mean'),
            Avg_CPM=('CPM (cost per 1,000 impressions)', 'mean'),
        ).round(2).reset_index()

        fig = px.pie(place, values='Spend', names='Placement',
                     title='Spend distribution by Placement',
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

    # Raw data
    with st.expander("📋 View raw Meta data"):
        st.dataframe(df, use_container_width=True)
