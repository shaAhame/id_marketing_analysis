import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

RED   = '#E24B4A'
AMBER = '#BA7517'
GREEN = '#639922'
TEAL  = '#1D9E75'
BLUE  = '#378ADD'
GRNDK = '#3B6D11'

def run_website_analysis(ga4_bundle, gsc_bundle=None):
    traffic_ch  = ga4_bundle.get('traffic_channel')
    traffic_src = ga4_bundle.get('traffic_source')
    users_df    = ga4_bundle.get('users')
    pages_df    = ga4_bundle.get('pages')
    events_df   = ga4_bundle.get('events')
    funnel_df   = ga4_bundle.get('funnel')
    landing_df  = ga4_bundle.get('landing')
    gsc_queries = gsc_bundle.get('queries') if gsc_bundle else None
    gsc_pages   = gsc_bundle.get('pages')   if gsc_bundle else None

    # ── OVERVIEW ──
    st.markdown('<div class="section-header">Website (GA4) — Traffic Overview</div>', unsafe_allow_html=True)
    if traffic_ch is not None:
        col0 = traffic_ch.columns[0]
        total_sess   = int(traffic_ch['Sessions'].sum())
        engaged_sess = int(traffic_ch['Engaged sessions'].sum()) if 'Engaged sessions' in traffic_ch.columns else 0
        eng_rate     = traffic_ch['Engagement rate'].mean()*100 if 'Engagement rate' in traffic_ch.columns else 0
        avg_dur      = traffic_ch['Average engagement time per session'].mean() if 'Average engagement time per session' in traffic_ch.columns else 0
        total_ev     = int(traffic_ch['Event count'].sum()) if 'Event count' in traffic_ch.columns else 0

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Total Sessions",   f"{total_sess:,}")
        c2.metric("Engaged Sessions", f"{engaged_sess:,}")
        c3.metric("Engagement Rate",  f"{eng_rate:.1f}%",
                  delta="Good" if eng_rate>50 else "Low",
                  delta_color="normal" if eng_rate>50 else "inverse")
        c4.metric("Avg Duration",     f"{avg_dur:.0f}s",
                  delta="Good" if avg_dur>45 else "Low",
                  delta_color="normal" if avg_dur>45 else "inverse")
        c5.metric("Total Events",     f"{total_ev:,}")

        channels = traffic_ch[col0].astype(str).str.lower().tolist()
        if not any('paid' in c for c in channels):
            st.markdown('<div class="alert-red">🔴 <b>No Paid Social in GA4</b> — Meta & TikTok spend not tracked. Add UTM tags: <code>?utm_source=facebook&utm_medium=cpc</code></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Sessions + engagement by channel
        st.markdown('<div class="section-header">Traffic by Channel</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            fig = px.bar(traffic_ch.sort_values('Sessions',ascending=False),
                         x=col0, y='Sessions', color=col0, text='Sessions',
                         title='Sessions by Channel', color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, height=340, xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.pie(traffic_ch, values='Sessions', names=col0,
                         title='Session Share', color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=340)
            st.plotly_chart(fig, use_container_width=True)

        if 'Engagement rate' in traffic_ch.columns:
            traffic_ch['Eng %'] = (traffic_ch['Engagement rate']*100).round(1)
            fig = px.bar(traffic_ch.sort_values('Eng %',ascending=False),
                         x=col0, y='Eng %', text='Eng %',
                         title='Engagement Rate by Channel (%)',
                         color='Eng %', color_continuous_scale=[RED,AMBER,GREEN])
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(height=300, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("**Benchmark:** 🔴 <40% Low  |  🟡 40–60% Average  |  🟢 60%+ Good")
        st.dataframe(traffic_ch, use_container_width=True)

    st.markdown("---")

    # ── ENGAGEMENT & BOUNCE by Landing Page ──
    st.markdown('<div class="section-header">Engagement & Bounce Rate by Landing Page</div>', unsafe_allow_html=True)
    if pages_df is not None:
        pg_col = pages_df.columns[0]
        total_views = int(pages_df['Views'].sum()) if 'Views' in pages_df.columns else 0
        st.markdown(f"**Total page views:** {total_views:,}  |  **Unique pages:** {len(pages_df):,}")

        top15 = pages_df.head(15)
        c1,c2 = st.columns(2)
        with c1:
            fig = px.bar(top15, x='Views', y=pg_col, orientation='h',
                         title='Top 15 Pages by Views',
                         color='Views', color_continuous_scale='Greens', text='Views')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=480, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if 'Average engagement time per active user' in pages_df.columns:
                top_eng = pages_df.nlargest(15,'Average engagement time per active user')
                fig = px.bar(top_eng, x='Average engagement time per active user', y=pg_col,
                             orientation='h', title='Avg Engagement Time by Page (seconds)',
                             color='Average engagement time per active user',
                             color_continuous_scale='Blues', text='Average engagement time per active user')
                fig.update_traces(texttemplate='%{text:.0f}s', textposition='outside')
                fig.update_layout(height=480, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

        # Low engagement pages alert
        if 'Average engagement time per active user' in pages_df.columns:
            low_eng = pages_df[pages_df['Average engagement time per active user']<20].head(5)
            if len(low_eng)>0:
                st.markdown(f'<div class="alert-yellow">🟡 <b>{len(low_eng)} pages</b> have very low engagement time (<20s) — check if ad traffic is landing on the wrong page.</div>', unsafe_allow_html=True)
                st.dataframe(low_eng[[pg_col,'Views','Average engagement time per active user']], use_container_width=True)

        with st.expander(f"View all {len(pages_df)} pages"):
            st.dataframe(pages_df, use_container_width=True)
    else:
        st.info("Upload GA4 Pages & Screens CSV to see landing page analysis.")

    st.markdown("---")

    # ── SOURCE / MEDIUM ──
    st.markdown('<div class="section-header">Traffic Sources — Source / Medium</div>', unsafe_allow_html=True)
    if traffic_src is not None:
        src_col = traffic_src.columns[0]
        fb   = int(traffic_src[traffic_src[src_col].str.contains('facebook',case=False,na=False)]['Sessions'].sum())
        ig   = int(traffic_src[traffic_src[src_col].str.contains(r'ig |instagram',case=False,na=False)]['Sessions'].sum())
        tt   = int(traffic_src[traffic_src[src_col].str.contains('tiktok',case=False,na=False)]['Sessions'].sum())
        goog = int(traffic_src[traffic_src[src_col].str.contains('google',case=False,na=False)]['Sessions'].sum())
        s1,s2,s3,s4 = st.columns(4)
        s1.metric("Google Organic", f"{goog:,}",    "✅ Strong SEO")
        s2.metric("Facebook",       f"{fb:,}",       "Organic/referral only" if fb>0 else "Not tracked")
        s3.metric("Instagram",      f"{ig:,}",       "Organic only")
        s4.metric("TikTok",         f"{tt:,}",       "❌ Near zero" if tt<10 else "OK")

        top15 = traffic_src.sort_values('Sessions',ascending=False).head(15)
        fig = px.bar(top15, x='Sessions', y=src_col, orientation='h',
                     title='Top 15 Traffic Sources', color='Sessions',
                     color_continuous_scale='Blues', text='Sessions')
        fig.update_traces(textposition='outside')
        fig.update_layout(height=480, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Fix UTM tracking — copy these URLs into your ads"):
            st.code("Meta Facebook: https://idealz.lk/?utm_source=facebook&utm_medium=cpc&utm_campaign=idealz_engagement")
            st.code("Meta Instagram: https://idealz.lk/?utm_source=instagram&utm_medium=cpc&utm_campaign=idealz_engagement")
            st.code("TikTok: https://idealz.lk/?utm_source=tiktok&utm_medium=cpc&utm_campaign=idealz_awareness")
        with st.expander("View all sources"):
            st.dataframe(traffic_src, use_container_width=True)
    else:
        st.info("Upload GA4 Traffic Source/Medium CSV to see detailed source analysis.")

    st.markdown("---")

    # ── CONVERSION FUNNEL ──
    st.markdown('<div class="section-header">Conversion Funnel — Drop-off Points</div>', unsafe_allow_html=True)
    if funnel_df is not None:
        st.dataframe(funnel_df, use_container_width=True)
        if 'Step' in funnel_df.columns and 'Users' in funnel_df.columns:
            fig = go.Figure(go.Funnel(y=funnel_df['Step'], x=funnel_df['Users'],
                                       textinfo='value+percent initial',
                                       marker_color=[BLUE]*len(funnel_df)))
            fig.update_layout(title='Conversion Funnel', height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload GA4 Funnel Exploration CSV to see conversion drop-off analysis.")
        st.markdown("""
**How to export from GA4:**
1. GA4 → Explore → Funnel Exploration
2. Build funnel steps: Homepage → Product Page → WhatsApp Click
3. Top right → Export → CSV
        """)
        # Show event-based proxy funnel
        if events_df is not None and traffic_ch is not None:
            total_sess = int(traffic_ch['Sessions'].sum()) if traffic_ch is not None else 0
            total_pv   = int(events_df[events_df.iloc[:,0]=='page_view']['Event count'].sum()) if 'page_view' in events_df.iloc[:,0].values else 0
            total_eng  = int(events_df[events_df.iloc[:,0]=='user_engagement']['Event count'].sum()) if 'user_engagement' in events_df.iloc[:,0].values else 0
            if total_sess > 0:
                st.markdown("**Proxy funnel from available events:**")
                prx = pd.DataFrame({
                    'Stage':['Sessions','Page Views','Engaged Users','WhatsApp Clicks (not tracked)'],
                    'Count':[total_sess, total_pv, total_eng, 0]
                })
                fig = go.Figure(go.Funnel(y=prx['Stage'], x=prx['Count'],
                                           textinfo='value+percent initial',
                                           marker_color=[BLUE]*4))
                fig.update_layout(title='Event-based Proxy Funnel', height=360)
                st.plotly_chart(fig, use_container_width=True)
                st.caption("⚠ WhatsApp click tracking not set up yet. See Events tab for setup guide.")

    st.markdown("---")

    # ── USER ACQUISITION ──
    st.markdown('<div class="section-header">User Acquisition — New vs Returning</div>', unsafe_allow_html=True)
    if users_df is not None:
        usr_col = users_df.columns[0]
        total_u = int(users_df['Total users'].sum())    if 'Total users'     in users_df.columns else 0
        new_u   = int(users_df['New users'].sum())      if 'New users'       in users_df.columns else 0
        ret_u   = int(users_df['Returning users'].sum())if 'Returning users' in users_df.columns else 0
        u1,u2,u3 = st.columns(3)
        u1.metric("Total Users",     f"{total_u:,}")
        u2.metric("New Users",       f"{new_u:,}",  delta=f"{new_u/total_u*100:.0f}% of total" if total_u>0 else None)
        u3.metric("Returning Users", f"{ret_u:,}",  delta=f"{ret_u/total_u*100:.0f}% returning" if total_u>0 else None)
        if 'New users' in users_df.columns:
            c1,c2 = st.columns(2)
            with c1:
                fig = px.bar(users_df, x=usr_col, y='New users', color=usr_col,
                             text='New users', title='New Users by Channel',
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False, height=300, xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                if 'Returning users' in users_df.columns:
                    fig = px.bar(users_df, x=usr_col, y='Returning users', color=usr_col,
                                 text='Returning users', title='Returning Users by Channel',
                                 color_discrete_sequence=px.colors.qualitative.Set3)
                    fig.update_traces(textposition='outside')
                    fig.update_layout(showlegend=False, height=300, xaxis_tickangle=-15)
                    st.plotly_chart(fig, use_container_width=True)
        st.dataframe(users_df, use_container_width=True)
    else:
        st.info("Upload GA4 User Acquisition CSV.")

    st.markdown("---")

    # ── SEO PERFORMANCE ──
    st.markdown('<div class="section-header">SEO Performance — Search Console</div>', unsafe_allow_html=True)
    if gsc_queries is not None:
        q_col = gsc_queries.columns[0]
        st.markdown("**Top search queries driving traffic to idealz.lk:**")
        c1,c2 = st.columns(2)
        with c1:
            top_q = gsc_queries.sort_values('Clicks',ascending=False).head(15) if 'Clicks' in gsc_queries.columns else gsc_queries.head(15)
            click_col = 'Clicks' if 'Clicks' in gsc_queries.columns else gsc_queries.columns[1]
            fig = px.bar(top_q, x=click_col, y=q_col, orientation='h',
                         title='Top 15 Search Queries by Clicks',
                         color=click_col, color_continuous_scale='Greens', text=click_col)
            fig.update_traces(textposition='outside')
            fig.update_layout(height=480, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if 'Position' in gsc_queries.columns:
                fig = px.scatter(gsc_queries.head(30), x='Clicks', y='Position',
                                 hover_name=q_col, title='Clicks vs Avg Position (lower=better)',
                                 color='Position', color_continuous_scale='RdYlGn_r')
                fig.update_yaxes(autorange='reversed')
                fig.add_hline(y=10, line_dash='dash', line_color=AMBER, annotation_text='Page 1 boundary')
                fig.update_layout(height=480)
                st.plotly_chart(fig, use_container_width=True)
        with st.expander("View all queries"):
            st.dataframe(gsc_queries, use_container_width=True)
    else:
        st.info("Upload Google Search Console Queries CSV to see keyword performance.")
        st.markdown("""
**How to export:**
1. Google Search Console → Performance → Search Results
2. Set date range → Last 28 days
3. Click Export → CSV
        """)
        # Show GA4 organic proxy
        if traffic_src is not None:
            src_col = traffic_src.columns[0]
            organic = traffic_src[traffic_src[src_col].str.contains('organic',case=False,na=False)]
            if len(organic)>0:
                st.markdown("**Organic search engines from GA4 (proxy):**")
                st.dataframe(organic, use_container_width=True)

    if gsc_pages is not None:
        st.markdown("**Top pages in search results:**")
        st.dataframe(gsc_pages, use_container_width=True)

    st.markdown("---")

    # ── UTM AUDIT ──
    st.markdown('<div class="section-header">UTM Tracking Audit — Active Campaign Links</div>', unsafe_allow_html=True)
    if traffic_src is not None:
        src_col = traffic_src.columns[0]
        paid = traffic_src[traffic_src[src_col].str.contains('cpc|paid|facebook|tiktok',case=False,na=False)]
        no_utm = traffic_src[traffic_src[src_col].str.contains('not set|none|direct',case=False,na=False)]

        if len(paid)>0:
            st.markdown('<div class="alert-green">🟢 Paid traffic with UTMs detected:</div>', unsafe_allow_html=True)
            st.dataframe(paid, use_container_width=True)
        else:
            st.markdown('<div class="alert-red">🔴 <b>No UTM-tagged paid traffic found.</b> All Meta and TikTok ad spend is invisible in GA4.</div>', unsafe_allow_html=True)

        if len(no_utm)>0:
            untagged_sess = int(no_utm['Sessions'].sum())
            st.markdown(f'<div class="alert-yellow">🟡 <b>{untagged_sess:,} untagged sessions</b> — source unknown. Some of these may be from your ads without UTMs.</div>', unsafe_allow_html=True)

        st.markdown("**UTM templates — add to all ad destination URLs:**")
        col1,col2 = st.columns(2)
        with col1:
            st.code("Facebook Feed:\nhttps://idealz.lk/?utm_source=facebook&utm_medium=cpc&utm_campaign=CAMPAIGN_NAME&utm_content=AD_NAME")
            st.code("Instagram Reels:\nhttps://idealz.lk/?utm_source=instagram&utm_medium=cpc&utm_campaign=CAMPAIGN_NAME&utm_content=AD_NAME")
        with col2:
            st.code("TikTok:\nhttps://idealz.lk/?utm_source=tiktok&utm_medium=cpc&utm_campaign=CAMPAIGN_NAME&utm_content=AD_NAME")
            st.code("Google Ads (if running):\nhttps://idealz.lk/?utm_source=google&utm_medium=cpc&utm_campaign=CAMPAIGN_NAME")
    else:
        st.info("Upload GA4 Traffic Source/Medium CSV to audit UTM tags.")

    st.markdown("---")

    # ── LEAD GEN LANDING PAGES ──
    st.markdown('<div class="section-header">Lead Gen Landing Pages Performance</div>', unsafe_allow_html=True)
    if landing_df is not None:
        st.dataframe(landing_df, use_container_width=True)
    elif pages_df is not None:
        pg_col = pages_df.columns[0]
        product_pages = pages_df[pages_df[pg_col].str.contains('/product',case=False,na=False)]
        if len(product_pages)>0:
            st.markdown("**Product pages (proxy for lead gen pages):**")
            fig = px.bar(product_pages.head(15), x='Views', y=pg_col, orientation='h',
                         title='Product Page Views (potential lead gen pages)',
                         color='Views', color_continuous_scale='Greens', text='Views')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            if 'Average engagement time per active user' in product_pages.columns:
                low = product_pages[product_pages['Average engagement time per active user']<15]
                if len(low)>0:
                    st.markdown(f'<div class="alert-yellow">🟡 <b>{len(low)} product pages</b> have engagement under 15s — ads may be sending traffic to wrong pages or pages need better content.</div>', unsafe_allow_html=True)
            st.dataframe(product_pages, use_container_width=True)
        else:
            st.info("No product pages found. Upload GA4 Landing Pages report (GA4 → Advertising → Landing pages) for dedicated lead gen analysis.")
    else:
        st.info("Upload GA4 Landing Pages CSV (GA4 → Advertising → Landing pages) for lead gen analysis.")

    st.markdown("---")

    # ── MONTHLY ORGANIC TRAFFIC ──
    st.markdown('<div class="section-header">Monthly Organic Traffic Report</div>', unsafe_allow_html=True)
    if traffic_ch is not None:
        col0 = traffic_ch.columns[0]
        organic_ch = traffic_ch[traffic_ch[col0].str.contains('organic|seo',case=False,na=False)]
        if len(organic_ch)>0:
            org_sess = int(organic_ch['Sessions'].sum())
            org_eng  = organic_ch['Engagement rate'].mean()*100 if 'Engagement rate' in organic_ch.columns else 0
            oo1,oo2 = st.columns(2)
            oo1.metric("Organic Sessions",  f"{org_sess:,}")
            oo2.metric("Organic Eng. Rate", f"{org_eng:.1f}%")
        st.dataframe(traffic_ch, use_container_width=True)
    if gsc_queries is not None:
        total_clicks_gsc = int(gsc_queries['Clicks'].sum()) if 'Clicks' in gsc_queries.columns else 0
        total_impr_gsc   = int(gsc_queries['Impressions'].sum()) if 'Impressions' in gsc_queries.columns else 0
        avg_pos          = gsc_queries['Position'].mean() if 'Position' in gsc_queries.columns else 0
        g1,g2,g3 = st.columns(3)
        g1.metric("Search Clicks",      f"{total_clicks_gsc:,}")
        g2.metric("Search Impressions", f"{total_impr_gsc:,}")
        g3.metric("Avg Position",       f"{avg_pos:.1f}",
                  delta="Good" if avg_pos<10 else "Needs work",
                  delta_color="normal" if avg_pos<10 else "inverse")
    else:
        st.info("Upload Google Search Console CSV for full SEO gains/losses tracking.")

    st.markdown("---")

    # ── EVENTS ──
    st.markdown('<div class="section-header">Events Tracked</div>', unsafe_allow_html=True)
    if events_df is not None:
        evt_col = events_df.columns[0]
        total_e = int(events_df['Event count'].sum()) if 'Event count' in events_df.columns else 0
        st.markdown(f"**Total events:** {total_e:,}  |  **Event types:** {len(events_df)}")
        if len(events_df)<=4:
            st.markdown('<div class="alert-yellow">🟡 Only basic events tracked. No WhatsApp clicks or purchase events configured yet.</div>', unsafe_allow_html=True)
        fig = px.pie(events_df, values='Event count', names=evt_col,
                     title='Event Distribution', color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(events_df, use_container_width=True)
        with st.expander("📋 Set up WhatsApp click tracking in GA4"):
            st.code("""// Add to website when WhatsApp button is clicked:
gtag('event', 'whatsapp_click', {
  event_category: 'engagement',
  event_label: 'WhatsApp Contact'
});""", language='javascript')
            st.caption("Then in GA4: Admin → Events → Mark as Key Event → whatsapp_click")
