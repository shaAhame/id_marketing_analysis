def get_all_alerts(meta_df, tiktok_df, ga4_df):
    alerts = []

    if meta_df is not None:
        freq_col = 'Frequency'
        if freq_col in meta_df.columns:
            fatigued = meta_df[meta_df[freq_col] > 3]
            if len(fatigued) > 0:
                alerts.append({
                    "level": "red",
                    "icon": "🔴",
                    "title": "Meta: Audience Fatigue",
                    "msg": f"{len(fatigued)} ads have frequency > 3.0 — audience needs refreshing"
                })

        zero_result = meta_df[
            (meta_df['Results'] == 0) &
            (meta_df['Amount spent (LKR)'] > 100)
        ] if 'Results' in meta_df.columns else []
        if len(zero_result) > 0:
            alerts.append({
                "level": "red",
                "icon": "🔴",
                "title": "Meta: Zero Result Ads",
                "msg": f"{len(zero_result)} ads spending money with 0 results — consider pausing"
            })

        ctr_col = 'CTR (link click-through rate)'
        if ctr_col in meta_df.columns:
            low_ctr = meta_df[meta_df[ctr_col] < 1.0]
            if len(low_ctr) > 0:
                alerts.append({
                    "level": "yellow",
                    "icon": "🟡",
                    "title": "Meta: Low CTR",
                    "msg": f"{len(low_ctr)} ads have CTR below 1% — creative may need refreshing"
                })

    if tiktok_df is not None:
        dest_col = 'Clicks (destination)'
        if dest_col in tiktok_df.columns:
            if tiktok_df[dest_col].sum() == 0:
                alerts.append({
                    "level": "red",
                    "icon": "🔴",
                    "title": "TikTok: Zero Destination Clicks",
                    "msg": "No clicks to website/WhatsApp from any TikTok ad — check destination URLs and CTA"
                })

        comp_col = '100% video view rate'
        if comp_col in tiktok_df.columns:
            avg_comp = tiktok_df[comp_col].mean() * 100
            if avg_comp < 10:
                alerts.append({
                    "level": "yellow",
                    "icon": "🟡",
                    "title": "TikTok: Low Completion Rate",
                    "msg": f"Avg video completion rate is {avg_comp:.1f}% — videos need stronger hooks"
                })

        watch_col = 'Average play time per video view'
        if watch_col in tiktok_df.columns:
            weak = tiktok_df[tiktok_df[watch_col] < 3]
            if len(weak) > 0:
                alerts.append({
                    "level": "yellow",
                    "icon": "🟡",
                    "title": "TikTok: Very Low Watch Time",
                    "msg": f"{len(weak)} ads average under 3 seconds watch time — opening scene needs work"
                })

    if ga4_df is not None:
        col0 = ga4_df.columns[0]
        channels = ga4_df[col0].astype(str).str.lower().tolist()
        if not any('paid' in c for c in channels):
            alerts.append({
                "level": "red",
                "icon": "🔴",
                "title": "Website: No Paid Social Traffic",
                "msg": "Meta and TikTok ad spend not tracked in GA4 — UTM parameters missing from ads"
            })

        sess_cols = [c for c in ga4_df.columns if 'session' in c.lower() and ga4_df[c].dtype in ['float64','int64']]
        if sess_cols:
            total = ga4_df[sess_cols[0]].sum()
            if total > 0:
                alerts.append({
                    "level": "green",
                    "icon": "🟢",
                    "title": "Website: Traffic Active",
                    "msg": f"{int(total):,} total sessions this week — site is receiving traffic"
                })

    return alerts
