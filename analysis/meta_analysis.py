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
    df = meta_curr.copy()

    # ── Safe column accessor — works with any Meta export format ──────────────
    def col(name, fallbacks=None):
        if name in df.columns: return df[name]
        if fallbacks:
            for fb in fallbacks:
                if fb in df.columns: return df[fb]
        return pd.Series([0] * len(df), index=df.index)

    # ── Standardise key column names once ────────────────────────────────────
    # CPM
    for src_col, tgt_col in [
        ('CPM (cost per 1,000 impressions) (LKR)', 'CPM (cost per 1,000 impressions)'),
        ('CPC (cost per link click) (LKR)',         'CPC (cost per link click)'),
        ('Cost per results',                        'Cost per result'),
        ('CPC (all) (LKR)',                         'CPC (all)'),
    ]:
        if src_col in df.columns and tgt_col not in df.columns:
            df = df.rename(columns={src_col: tgt_col})

    # Ensure Ad set name exists
    if 'Ad set name' not in df.columns:
        if 'Ad delivery' in df.columns:
            df['Ad set name'] = df['Ad delivery'].astype(str).str.split('(').str[0].str.strip()
        else:
            df['Ad set name'] = 'All Ads'

    # Ensure Cost per result exists
    if 'Cost per result' not in df.columns:
        df['Cost per result'] = (
            col('Amount spent (LKR)') /
            col('Results').replace(0, 1)
        ).round(2)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Meta Ads — Performance Overview</div>',
                unsafe_allow_html=True)

    total_spend   = col('Amount spent (LKR)').sum()
    total_results = int(col('Results').sum())
    avg_cpr       = total_spend / total_results if total_results > 0 else 0
    avg_ctr       = col('CTR (link click-through rate)').mean()
    avg_cpm       = col('CPM (cost per 1,000 impressions)').mean()
    avg_cpc       = col('CPC (cost per link click)').mean()
    avg_freq      = col('Frequency').mean()
    total_impr    = int(col('Impressions').sum())
    total_reach   = int(col('Reach').sum())
    total_clicks  = int(col('Link clicks').sum())

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Spend",    f"Rs {total_spend:,.0f}")
    c2.metric("Total Results",  f"{total_results:,}")
    c3.metric("Cost / Result",  f"Rs {avg_cpr:,.2f}",
              "⚠ High" if avg_cpr > 25 else "Good",
              delta_color="inverse" if avg_cpr > 25 else "normal")
    c4.metric("Avg CTR",        f"{avg_ctr:.2f}%",
              "Good" if avg_ctr >= 1.5 else "Low",
              delta_color="normal" if avg_ctr >= 1.5 else "inverse")
    c5.metric("Avg CPM",        f"Rs {avg_cpm:,.2f}")
    c6.metric("Avg Frequency",  f"{avg_freq:.2f}",
              "⚠ High" if avg_freq > 3 else "Healthy",
              delta_color="inverse" if avg_freq > 3 else "normal")

    st.markdown("---")

    # ── FB vs IG ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Platform — Facebook vs Instagram</div>',
                unsafe_allow_html=True)

    if 'Platform' in df.columns:
        plat = df.groupby('Platform').agg(
            Spend=('Amount spent (LKR)', 'sum'),
            Results=('Results', 'sum'),
            Impressions=('Impressions', 'sum'),
            Reach=('Reach', 'sum'),
        ).round(2).reset_index()
        plat['CPR'] = (plat['Spend'] / plat['Results'].replace(0, 1)).round(2)

        # Add CTR/CPM/CPC safely
        for metric_col, agg_name in [
            ('CTR (link click-through rate)', 'Avg_CTR'),
            ('CPM (cost per 1,000 impressions)', 'Avg_CPM'),
            ('CPC (cost per link click)', 'Avg_CPC'),
            ('Frequency', 'Avg_Freq'),
        ]:
            if metric_col in df.columns:
                plat = plat.merge(
                    df.groupby('Platform')[metric_col].mean().round(2).rename(agg_name),
                    on='Platform', how='left'
                )
            else:
                plat[agg_name] = 0

        cmap = {'facebook': BLUE, 'instagram': PINK,
                'Facebook': BLUE, 'Instagram': PINK}
        c1, c2, c3 = st.columns(3)
        for col_st, metric, title, fmt in [
            (c1, 'Results',   'Results by Platform',        '%{text}'),
            (c2, 'CPR',       'Cost Per Result (lower=better)', 'Rs %{text:.0f}'),
            (c3, 'Avg_CTR',   'Avg CTR by Platform',        '%{text:.2f}%'),
        ]:
            with col_st:
                fig = px.bar(plat, x='Platform', y=metric, color='Platform',
                             text=metric, title=title,
                             color_discrete_map=cmap)
                fig.update_traces(texttemplate=fmt, textposition='outside')
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)

        display_cols = ['Platform', 'Spend', 'Results', 'CPR']
        for c in ['Avg_CTR', 'Avg_CPM', 'Avg_CPC', 'Avg_Freq']:
            if c in plat.columns:
                display_cols.append(c)
        fmt_map = {'Spend': 'Rs {:,.0f}', 'CPR': 'Rs {:,.2f}',
                   'Avg_CPM': 'Rs {:,.2f}', 'Avg_CPC': 'Rs {:,.2f}',
                   'Avg_CTR': '{:.2f}%', 'Avg_Freq': '{:.2f}'}
        st.dataframe(plat[display_cols].style.format(
            {k: v for k, v in fmt_map.items() if k in plat.columns}),
            use_container_width=True)

    st.markdown("---")

    # ── AD SET DEEP DIVE ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Ad Set Deep Dive — CPM · CPC · CTR</div>',
                unsafe_allow_html=True)

    if 'Ad set name' in df.columns:
        agg_dict = {
            'Amount spent (LKR)': 'sum',
            'Results': 'sum',
            'Impressions': 'sum',
        }
        for c in ['CTR (link click-through rate)', 'CPM (cost per 1,000 impressions)',
                  'CPC (cost per link click)', 'Frequency']:
            if c in df.columns:
                agg_dict[c] = 'mean'

        adset = df.groupby('Ad set name').agg(agg_dict).round(2).reset_index()
        adset.columns = [c.replace('Amount spent (LKR)', 'Spend')
                          .replace('CTR (link click-through rate)', 'Avg_CTR')
                          .replace('CPM (cost per 1,000 impressions)', 'Avg_CPM')
                          .replace('CPC (cost per link click)', 'Avg_CPC')
                          .replace('Frequency', 'Avg_Freq')
                         for c in adset.columns]
        adset['CPR'] = (adset['Spend'] / adset['Results'].replace(0, 1)).round(2)

        c1, c2, c3 = st.columns(3)
        for col_plot, title, cscale, fmt in [
            ('Avg_CPM', 'CPM by Ad Set (Rs) — lower = better', 'Reds',   'Rs %{text:.0f}'),
            ('Avg_CPC', 'CPC by Ad Set (Rs) — lower = better', 'Oranges','Rs %{text:.0f}'),
            ('Avg_CTR', 'CTR by Ad Set (%) — higher = better', 'Greens', '%{text:.2f}%'),
        ]:
            if col_plot not in adset.columns:
                continue
            with [c1, c2, c3][['Avg_CPM','Avg_CPC','Avg_CTR'].index(col_plot)]:
                data = adset.sort_values(col_plot,
                    ascending=(col_plot != 'Avg_CTR'))
                fig = px.bar(data, x=col_plot, y='Ad set name',
                             orientation='h', title=title,
                             color=col_plot, color_continuous_scale=cscale,
                             text=col_plot)
                fig.update_traces(texttemplate=fmt, textposition='outside')
                fig.update_layout(height=max(300, len(adset) * 30),
                                  coloraxis_showscale=False,
                                  yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

        disp = ['Ad set name', 'Spend', 'Results', 'CPR']
        for c in ['Avg_CTR', 'Avg_CPM', 'Avg_CPC', 'Avg_Freq']:
            if c in adset.columns:
                disp.append(c)
        fmt_map2 = {'Spend': 'Rs {:,.0f}', 'CPR': 'Rs {:,.2f}',
                    'Avg_CPM': 'Rs {:,.2f}', 'Avg_CPC': 'Rs {:,.2f}',
                    'Avg_CTR': '{:.2f}%', 'Avg_Freq': '{:.2f}'}
        st.dataframe(adset[disp].style.format(
            {k: v for k, v in fmt_map2.items() if k in adset.columns}),
            use_container_width=True)

    st.markdown("---")

    # ── CAMPAIGN PACING ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Campaign Pacing vs Budget</div>',
                unsafe_allow_html=True)

    if 'Ad set name' in df.columns:
        pacing = df.groupby('Ad set name').agg(
            Spend=('Amount spent (LKR)', 'sum'),
            Results=('Results', 'sum')
        ).round(2).reset_index()
        avg_sp = pacing['Spend'].mean()
        pacing['vs_avg_%'] = ((pacing['Spend'] - avg_sp) / avg_sp * 100).round(1)
        pacing['Status'] = pacing['vs_avg_%'].apply(
            lambda x: '🔴 Overspending' if x > 30 else (
                      '🟡 Slightly over' if x > 10 else (
                      '🟢 On track'      if x > -10 else '⚠ Underspending')))

        fig = px.bar(pacing.sort_values('Spend', ascending=False),
                     x='Ad set name', y='Spend', color='vs_avg_%',
                     color_continuous_scale=[GREEN, AMBER, RED],
                     text='Spend',
                     title='Spend by Ad Set — over/under vs average')
        fig.update_traces(texttemplate='Rs %{text:,.0f}', textposition='outside')
        fig.update_layout(height=360, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pacing[['Ad set name', 'Spend', 'Results', 'vs_avg_%', 'Status']]
                     .style.format({'Spend': 'Rs {:,.0f}', 'vs_avg_%': '{:+.1f}%'}),
                     use_container_width=True)

    st.markdown("---")

    # ── TOP & BOTTOM ADS ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Creative Performance — Top & Bottom Ads</div>',
                unsafe_allow_html=True)

    active = df[col('Results') > 0].copy() if col('Results').sum() > 0 else df.copy()
    if len(active) > 0 and 'Cost per result' in active.columns:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("✅ **Top 10 — lowest cost per result**")
            best = active.sort_values('Cost per result').head(10)
            disp_cols = ['Ad name']
            if 'Platform' in best.columns: disp_cols.append('Platform')
            disp_cols += ['Results', 'Cost per result', 'Amount spent (LKR)']
            if 'CTR (link click-through rate)' in best.columns:
                disp_cols.append('CTR (link click-through rate)')
            st.dataframe(best[disp_cols].style.format({
                'Cost per result': 'Rs {:,.2f}',
                'Amount spent (LKR)': 'Rs {:,.0f}',
                'CTR (link click-through rate)': '{:.2f}%',
            }), use_container_width=True)

        with c2:
            st.markdown("❌ **Bottom 10 — highest cost per result**")
            worst = active.sort_values('Cost per result', ascending=False).head(10)
            st.dataframe(worst[disp_cols].style.format({
                'Cost per result': 'Rs {:,.2f}',
                'Amount spent (LKR)': 'Rs {:,.0f}',
                'CTR (link click-through rate)': '{:.2f}%',
            }), use_container_width=True)

        if 'CTR (link click-through rate)' in active.columns:
            pcolors = ['#378ADD' if 'face' in str(p).lower() else '#D4537E'
                       for p in active.get('Platform', ['facebook'] * len(active))]
            fig = px.scatter(active,
                             x='Amount spent (LKR)',
                             y='CTR (link click-through rate)',
                             color='Platform' if 'Platform' in active.columns else None,
                             size='Results',
                             hover_name='Ad name',
                             title='Spend vs CTR per Ad (bubble = results count)',
                             color_discrete_map={'facebook': BLUE, 'instagram': PINK,
                                                 'Facebook': BLUE, 'Instagram': PINK})
            fig.add_hline(y=1.5, line_dash='dash', line_color=AMBER,
                          annotation_text='1.5% benchmark')
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── FREQUENCY & FATIGUE ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">Frequency & Audience Fatigue Check</div>',
                unsafe_allow_html=True)

    fatigued = df[col('Frequency') > 3]
    if len(fatigued) > 0:
        st.markdown(
            f'<div class="alert-red">🔴 <b>{len(fatigued)} fatigued ads</b> — '
            f'frequency above 3.0. Refresh creative or expand audience.</div>',
            unsafe_allow_html=True)
        fa_cols = ['Ad name']
        if 'Platform' in df.columns: fa_cols.append('Platform')
        fa_cols += ['Frequency', 'Amount spent (LKR)', 'Results']
        st.dataframe(fatigued[fa_cols].style.format(
            {'Frequency': '{:.2f}', 'Amount spent (LKR)': 'Rs {:,.0f}'}),
            use_container_width=True)
    else:
        st.markdown(
            '<div class="alert-green">🟢 No fatigued audiences — all frequency below 3.0</div>',
            unsafe_allow_html=True)

    fig = px.histogram(df, x='Frequency', nbins=20,
                       title='Frequency Distribution',
                       color_discrete_sequence=[BLUE])
    fig.add_vline(x=3, line_dash='dash', line_color=RED,
                  annotation_text='Fatigue threshold 3.0')
    fig.update_layout(height=280)
    st.plotly_chart(fig, use_container_width=True)

    zero_spend = df[(col('Results') == 0) & (col('Amount spent (LKR)') > 100)]
    if len(zero_spend) > 0:
        st.markdown(
            f'<div class="alert-red">🔴 <b>{len(zero_spend)} zero-result ads</b> '
            f'spending budget with no results — pause immediately.</div>',
            unsafe_allow_html=True)
        z_cols = ['Ad name']
        if 'Platform' in df.columns: z_cols.append('Platform')
        z_cols += ['Amount spent (LKR)', 'Impressions', 'Frequency']
        st.dataframe(zero_spend[z_cols].style.format(
            {'Amount spent (LKR)': 'Rs {:,.0f}',
             'Impressions': '{:,}', 'Frequency': '{:.2f}'}),
            use_container_width=True)

    st.markdown("---")

    # ── PLACEMENT ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Placement Breakdown</div>',
                unsafe_allow_html=True)

    if 'Placement' in df.columns:
        place = df.groupby('Placement').agg(
            Spend=('Amount spent (LKR)', 'sum'),
            Results=('Results', 'sum'),
            Impressions=('Impressions', 'sum'),
        ).round(2).reset_index()
        if 'CTR (link click-through rate)' in df.columns:
            place = place.merge(
                df.groupby('Placement')['CTR (link click-through rate)']
                  .mean().round(2).rename('Avg_CTR'),
                on='Placement', how='left')
        if 'CPM (cost per 1,000 impressions)' in df.columns:
            place = place.merge(
                df.groupby('Placement')['CPM (cost per 1,000 impressions)']
                  .mean().round(2).rename('Avg_CPM'),
                on='Placement', how='left')
        place['CPR'] = (place['Spend'] / place['Results'].replace(0, 1)).round(2)
        place = place.sort_values('Results', ascending=False)

        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(place, values='Spend', names='Placement',
                         title='Spend by Placement',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if 'Avg_CTR' in place.columns:
                fig = px.bar(place, x='Placement', y='Avg_CTR', text='Avg_CTR',
                             title='CTR by Placement (%)',
                             color='Avg_CTR', color_continuous_scale='Greens')
                fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                fig.update_layout(height=320, coloraxis_showscale=False,
                                  xaxis_tickangle=-20)
                st.plotly_chart(fig, use_container_width=True)

        pl_cols = ['Placement', 'Spend', 'Results', 'CPR']
        pl_fmt  = {'Spend': 'Rs {:,.0f}', 'CPR': 'Rs {:,.2f}'}
        if 'Avg_CTR' in place.columns:
            pl_cols.append('Avg_CTR'); pl_fmt['Avg_CTR'] = '{:.2f}%'
        if 'Avg_CPM' in place.columns:
            pl_cols.append('Avg_CPM'); pl_fmt['Avg_CPM'] = 'Rs {:,.2f}'
        st.dataframe(place[pl_cols].style.format(pl_fmt), use_container_width=True)

    st.markdown("---")

    # ── MONTHLY WRAP ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Monthly Performance Wrap</div>',
                unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Spend",       f"Rs {total_spend:,.0f}")
    m2.metric("Total Results",     f"{total_results:,}")
    m3.metric("Total Impressions", f"{total_impr:,}")
    m4.metric("Total Reach",       f"{total_reach:,}")
    m5.metric("Total Clicks",      f"{total_clicks:,}")

    if meta_prev is not None:
        pv_ts  = meta_prev['Amount spent (LKR)'].sum() if 'Amount spent (LKR)' in meta_prev.columns else 0
        pv_tr  = int(meta_prev['Results'].sum())       if 'Results'            in meta_prev.columns else 0
        pv_rch = int(meta_prev['Reach'].sum())         if 'Reach'              in meta_prev.columns else 0
        p1, p2, p3 = st.columns(3)
        p1.metric("Spend Change",
                  f"Rs {total_spend:,.0f}",
                  f"{(total_spend-pv_ts)/pv_ts*100:+.1f}%" if pv_ts > 0 else None)
        p2.metric("Results Change",
                  f"{total_results:,}",
                  f"{(total_results-pv_tr)/pv_tr*100:+.1f}%" if pv_tr > 0 else None)
        p3.metric("Reach Change",
                  f"{total_reach:,}",
                  f"{(total_reach-pv_rch)/pv_rch*100:+.1f}%" if pv_rch > 0 else None)
    else:
        st.info("💡 Upload previous period Meta export to see month-over-month comparison.")

    with st.expander("📋 View full raw Meta data"):
        st.dataframe(df, use_container_width=True)
