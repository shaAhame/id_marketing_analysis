import pandas as pd
import streamlit as st
import io

def _clean_numeric(df):
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def _read_ga4_csv(file):
    """
    GA4 exports have ~9 header rows before actual data.
    Auto-detects the real header row by finding the first row
    with 3+ non-empty cells that looks like a data header.
    """
    try:
        raw = file.read().decode('utf-8')
        file.seek(0)
    except Exception:
        file.seek(0)
        raw = io.StringIO(file.read().decode('utf-8', errors='ignore')).read()

    lines = raw.split('\n')
    skip = 0
    keywords = ['session','first user','page path','event name',
                'direct','organic','referral','unassigned','channel']
    for i, line in enumerate(lines):
        cells = [c.strip().lower() for c in line.split(',')]
        non_empty = [c for c in cells if c]
        if len(non_empty) >= 2:
            if any(any(kw in c for kw in keywords) for c in non_empty):
                skip = i
                break

    try:
        df = pd.read_csv(io.StringIO(raw), skiprows=skip)
    except Exception:
        df = pd.read_csv(file, skiprows=skip)

    df.columns = df.columns.str.strip()
    # Remove GA4 footer/total rows
    df = df[~df.iloc[:,0].astype(str).str.lower().str.contains(
        'total|report date|currency|property|filters applied', na=False)]
    df = df[df.iloc[:,0].astype(str).str.strip() != '']
    df = df.dropna(how='all')
    return _clean_numeric(df)

# ─────────────────────────────────────────
# META
# ─────────────────────────────────────────
def load_meta(file):
    """Loads Meta Ads Manager XLSX or CSV export."""
    try:
        fname = getattr(file, 'name', '')
        if fname.endswith('.xlsx') or fname.endswith('.xls'):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

        df.columns = df.columns.str.strip()
        # Drop summary/blank rows (first row is often a totals row)
        df = df[df['Ad name'].notna() & (df['Ad name'].astype(str).str.strip() != '')]

        numeric_cols = [
            'Results', 'Cost per result', 'Amount spent (LKR)',
            'Impressions', 'Reach', 'Frequency', 'Link clicks',
            'CPM (cost per 1,000 impressions)',
            'CPC (cost per link click)',
            'CTR (link click-through rate)'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading Meta file: {e}")
        return None

# ─────────────────────────────────────────
# TIKTOK
# ─────────────────────────────────────────
def load_tiktok(file):
    """Loads TikTok Ads Manager XLSX export."""
    try:
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        df = df[~df['Campaign name'].astype(str).str.contains('Total', na=False)]
        df = df[df['Campaign name'].astype(str).str.strip() != '']

        numeric_cols = [
            'Impressions', 'Reach', 'Frequency', 'Cost',
            'Clicks (all)', 'CPC (destination)', 'Clicks (destination)',
            'CPM', 'CTR (destination)', 'Video views',
            '2-second video views', '6-second video views',
            '100% video view rate', 'Average play time per video view',
            'Conversions', 'Cost per conversion', 'Result rate'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading TikTok file: {e}")
        return None

# ─────────────────────────────────────────
# GA4 — all 5 report types
# ─────────────────────────────────────────
def load_ga4_traffic_channel(file):
    """GA4 Traffic Acquisition — Session primary channel group"""
    try:
        return _read_ga4_csv(file)
    except Exception as e:
        st.error(f"Error loading GA4 Traffic Channel file: {e}")
        return None

def load_ga4_traffic_source(file):
    """GA4 Traffic Acquisition — Session source / medium"""
    try:
        return _read_ga4_csv(file)
    except Exception as e:
        st.error(f"Error loading GA4 Source/Medium file: {e}")
        return None

def load_ga4_user_acquisition(file):
    """GA4 User Acquisition — First user channel group"""
    try:
        return _read_ga4_csv(file)
    except Exception as e:
        st.error(f"Error loading GA4 User Acquisition file: {e}")
        return None

def load_ga4_pages(file):
    """GA4 Pages and Screens"""
    try:
        return _read_ga4_csv(file)
    except Exception as e:
        st.error(f"Error loading GA4 Pages file: {e}")
        return None

def load_ga4_events(file):
    """GA4 Events"""
    try:
        return _read_ga4_csv(file)
    except Exception as e:
        st.error(f"Error loading GA4 Events file: {e}")
        return None

# ─────────────────────────────────────────
# Smart auto-detect — figures out file type
# from filename automatically
# ─────────────────────────────────────────
def auto_detect_file(file):
    """
    Given any uploaded file, auto-detects what type it is
    and returns (file_type, dataframe).
    """
    name = getattr(file, 'name', '').lower()

    if 'traffic_acquisition_session_primary' in name or \
       ('traffic' in name and 'channel' in name):
        return 'ga4_traffic_channel', load_ga4_traffic_channel(file)

    elif 'traffic_acquisition_session_source' in name or \
         ('traffic' in name and 'source' in name):
        return 'ga4_traffic_source', load_ga4_traffic_source(file)

    elif 'user_acquisition' in name or 'first_user' in name:
        return 'ga4_user_acquisition', load_ga4_user_acquisition(file)

    elif 'pages_and_screens' in name or 'page_path' in name:
        return 'ga4_pages', load_ga4_pages(file)

    elif 'events_event' in name or 'event_name' in name:
        return 'ga4_events', load_ga4_events(file)

    elif 'tiktok' in name or ('ads_report' in name and name.endswith('.xlsx')):
        return 'tiktok', load_tiktok(file)

    elif name.endswith('.xlsx') or name.endswith('.xls'):
        # Likely Meta report (xlsx)
        return 'meta', load_meta(file)

    elif name.endswith('.csv'):
        # Try GA4 traffic channel as default for unknown CSVs
        return 'ga4_traffic_channel', load_ga4_traffic_channel(file)

    return 'unknown', None

def load_ga4_generic(file):
    """Load any GA4 CSV export — funnel exploration, landing pages etc."""
    try:
        return _read_ga4_csv(file)
    except Exception as e:
        import streamlit as st
        st.error(f"Error loading GA4 file: {e}")
        return None

def load_gsc(file):
    """Load Google Search Console CSV export."""
    try:
        raw = file.read().decode('utf-8')
        file.seek(0)
        import io
        lines = raw.split('\n')
        skip = 0
        for i, line in enumerate(lines):
            cells = [c.strip().lower() for c in line.split(',')]
            if any(kw in cells for kw in ['query','page','clicks','impressions','ctr','position']):
                skip = i
                break
        df = pd.read_csv(io.StringIO(raw), skiprows=skip)
        df.columns = df.columns.str.strip()
        df = df[df.iloc[:,0].astype(str).str.strip() != ''].dropna(how='all')
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        import streamlit as st
        st.error(f"Error loading Search Console file: {e}")
        return None
