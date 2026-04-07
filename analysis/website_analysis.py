import streamlit as st
import pandas as pd
import plotly.express as px

RED   = '#E24B4A'
AMBER = '#BA7517'
GREEN = '#639922'

def run_website_analysis(ga4_bundle):
    traffic_ch  = ga4_bundle.get('traffic_channel')
    traffic_src = ga4_bundle.get('traffic_source')
    users_df    = ga4_bundle.get('users')
    pages_df    = ga4_bundle.get('pages')
    events_df   = ga4_bundle.get('events')

    st.markdown('<div class="section-header">Website (GA4) — Traffic Overview</div>', unsafe_allow_html=True)

    if traffic_ch is not None:
        col0 = traffic_ch.columns[0]
        total_sess   = int(traffic_ch['Sessions'].sum())
        engaged_sess = int(traffic_ch['Engaged sessions'].sum()) if 'Engaged sessions' in traffic_ch.columns else 0
        eng_rate     = traffic_ch['Engagement rate'].mean()*100 if 'Engagement rate' in traffic_ch.columns else 0
        avg_dur      = traffic_ch['Average engagement time per session'].mean() if 'Average engagement time per session' in traffic_ch.columns else 0

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Sessions",   f"{total_sess:,}")
        c2.metric("Engaged Sessions", f"{engaged_sess:,}")
        c3.metric("Engagement Rate",  f"{eng_rate:.1f}%",
                  delta="Good" if eng_rate>50 else "Low", delta_color="normal" if eng_rate>50 else "inverse")
        c4.metric("Avg Duration",     f"{avg_dur:.0f}s",
                  delta="Good" if avg_dur>45 else "Low", delta_color="normal" if avg_dur>45 else "inverse")

        if not any('paid' in c.lower() for c in traffic_ch[col0].astype(str).tolist()):
            st.markdown('<div class="alert-red">🔴 <b>No Paid Social traffic in GA4</b> — Meta & TikTok spend not tracked. Add UTM tags to all ads.</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-header">Sessions by Channel</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            fig = px.bar(traffic_ch.sort_values('Sessions',ascending=False),
                         x=col0, y='Sessions', color=col0, text='Sessions',
                         title='Sessions by Channel', color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False,height=340,xaxis_tickangle=-15)
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            fig = px.pie(traffic_ch, values='Sessions', names=col0,
                         title='Session Share', color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=340)
            st.plotly_chart(fig,use_container_width=True)

        if 'Engagement rate' in traffic_ch.columns:
            traffic_ch['Eng %'] = (traffic_ch['Engagement rate']*100).round(1)
            fig = px.bar(traffic_ch.sort_values('Eng %',ascending=False),
                         x=col0, y='Eng %', text='Eng %', title='Engagement Rate by Channel (%)',
                         color='Eng %', color_continuous_scale=[RED,AMBER,GREEN])
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(height=300, coloraxis_showscale=False)
            st.plotly_chart(fig,use_container_width=True)

        st.markdown("**Benchmark:** 🔴 <40% Low  |  🟡 40–60% Average  |  🟢 60%+ Good")
        st.dataframe(traffic_ch, use_container_width=True)

    if traffic_src is not None:
        st.markdown("---")
        st.markdown('<div class="section-header">Traffic Sources — Source / Medium</div>', unsafe_allow_html=True)
        src_col = traffic_src.columns[0]

        fb   = int(traffic_src[traffic_src[src_col].str.contains('facebook',case=False,na=False)]['Sessions'].sum())
        ig   = int(traffic_src[traffic_src[src_col].str.contains(r'ig |instagram',case=False,na=False)]['Sessions'].sum())
        tt   = int(traffic_src[traffic_src[src_col].str.contains('tiktok',case=False,na=False)]['Sessions'].sum())
        goog = int(traffic_src[traffic_src[src_col].str.contains('google',case=False,na=False)]['Sessions'].sum())

        s1,s2,s3,s4 = st.columns(4)
        s1.metric("Google",    f"{goog:,}", "✅ Strong SEO")
        s2.metric("Facebook",  f"{fb:,}",   "Organic/Referral only")
        s3.metric("Instagram", f"{ig:,}",   "Organic only")
        s4.metric("TikTok",    f"{tt:,}",   "❌ Near zero" if tt<10 else "OK")

        top15 = traffic_src.sort_values('Sessions',ascending=False).head(15)
        fig = px.bar(top15, x='Sessions', y=src_col, orientation='h',
                     title='Top 15 Traffic Sources', color='Sessions',
                     color_continuous_scale='Blues', text='Sessions')
        fig.update_traces(textposition='outside')
        fig.update_layout(height=480, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Fix UTM tracking — add to all Meta & TikTok ads"):
            st.code("Meta:   https://idealz.lk/?utm_source=facebook&utm_medium=cpc&utm_campaign=idealz_engagement")
            st.code("TikTok: https://idealz.lk/?utm_source=tiktok&utm_medium=cpc&utm_campaign=idealz_awareness")
            st.caption("Once added, paid traffic appears in GA4 within 24–48 hours.")

        with st.expander("View all sources"):
            st.dataframe(traffic_src, use_container_width=True)

    if users_df is not None:
        st.markdown("---")
        st.markdown('<div class="section-header">User Acquisition — New vs Returning</div>', unsafe_allow_html=True)
        usr_col = users_df.columns[0]
        total_u = int(users_df['Total users'].sum())    if 'Total users'     in users_df.columns else 0
        new_u   = int(users_df['New users'].sum())      if 'New users'       in users_df.columns else 0
        ret_u   = int(users_df['Returning users'].sum())if 'Returning users' in users_df.columns else 0

        u1,u2,u3 = st.columns(3)
        u1.metric("Total Users",     f"{total_u:,}")
        u2.metric("New Users",       f"{new_u:,}", delta=f"{new_u/total_u*100:.0f}% of total" if total_u>0 else None)
        u3.metric("Returning Users", f"{ret_u:,}", delta=f"{ret_u/total_u*100:.0f}% returning" if total_u>0 else None)

        if 'New users' in users_df.columns:
            c1,c2 = st.columns(2)
            with c1:
                fig = px.bar(users_df, x=usr_col, y='New users', color=usr_col,
                             text='New users', title='New Users by Channel',
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False,height=320,xaxis_tickangle=-15)
                st.plotly_chart(fig,use_container_width=True)
            with c2:
                if 'Returning users' in users_df.columns:
                    fig = px.bar(users_df, x=usr_col, y='Returning users', color=usr_col,
                                 text='Returning users', title='Returning Users by Channel',
                                 color_discrete_sequence=px.colors.qualitative.Set3)
                    fig.update_traces(textposition='outside')
                    fig.update_layout(showlegend=False,height=320,xaxis_tickangle=-15)
                    st.plotly_chart(fig,use_container_width=True)
        st.dataframe(users_df, use_container_width=True)

    if pages_df is not None:
        st.markdown("---")
        st.markdown('<div class="section-header">Top Pages — What Visitors Are Viewing</div>', unsafe_allow_html=True)
        pg_col = pages_df.columns[0]
        total_views = int(pages_df['Views'].sum()) if 'Views' in pages_df.columns else 0
        st.markdown(f"**Total page views:** {total_views:,}  |  **Unique pages tracked:** {len(pages_df):,}")

        top15 = pages_df.head(15)
        fig = px.bar(top15, x='Views', y=pg_col, orientation='h',
                     title='Top 15 Pages by Views', color='Views',
                     color_continuous_scale='Greens', text='Views')
        fig.update_traces(textposition='outside')
        fig.update_layout(height=480, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        if 'Average engagement time per active user' in pages_df.columns:
            top_eng = pages_df.nlargest(10,'Average engagement time per active user')
            fig = px.bar(top_eng, x='Average engagement time per active user', y=pg_col,
                         orientation='h', title='Avg Engagement Time by Page (seconds)',
                         color='Average engagement time per active user',
                         color_continuous_scale='Blues',
                         text='Average engagement time per active user')
            fig.update_traces(texttemplate='%{text:.0f}s', textposition='outside')
            fig.update_layout(height=380, yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with st.expander(f"View all {len(pages_df)} pages"):
            st.dataframe(pages_df, use_container_width=True)

    if events_df is not None:
        st.markdown("---")
        st.markdown('<div class="section-header">Events Tracked</div>', unsafe_allow_html=True)
        evt_col = events_df.columns[0]
        total_e = int(events_df['Event count'].sum()) if 'Event count' in events_df.columns else 0
        st.markdown(f"**Total events:** {total_e:,}  |  **Event types:** {len(events_df)}")
        if len(events_df) <= 4:
            st.markdown('<div class="alert-yellow">🟡 Only basic events tracked. No WhatsApp clicks or purchase events yet. Set these up in GA4 to measure actual conversions from ads.</div>', unsafe_allow_html=True)
        fig = px.pie(events_df, values='Event count', names=evt_col,
                     title='Event Distribution', color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(events_df, use_container_width=True)

        with st.expander("📋 How to track WhatsApp clicks in GA4"):
            st.code("""// Add to website when WhatsApp button is clicked:
gtag('event', 'whatsapp_click', {
  event_category: 'engagement',
  event_label: 'WhatsApp Contact'
});""", language='javascript')
            st.caption("Then in GA4: Admin → Events → Mark as Key Event → whatsapp_click")
