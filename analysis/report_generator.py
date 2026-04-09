import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY  = colors.HexColor('#1A1A2E')
BLUE  = colors.HexColor('#378ADD')
PINK  = colors.HexColor('#D4537E')
TEAL  = colors.HexColor('#1D9E75')
GREEN = colors.HexColor('#639922')
GRNDK = colors.HexColor('#3B6D11')
AMBER = colors.HexColor('#BA7517')
RED   = colors.HexColor('#E24B4A')
LGREY = colors.HexColor('#F8F9FA')
MGREY = colors.HexColor('#E9ECEF')
WHITE = colors.white

# ── Helpers ───────────────────────────────────────────────────────────────────
def PS(name, fs=10, bold=False, color=None, align=TA_LEFT, sp=4, lft=0, lead=None):
    return ParagraphStyle(name,
        fontName='Helvetica-Bold' if bold else 'Helvetica',
        fontSize=fs,
        textColor=color or colors.HexColor('#2C2C2A'),
        spaceAfter=sp, spaceBefore=0,
        leading=lead or (fs+4),
        alignment=align,
        leftIndent=lft)

def sp(n=8): return Spacer(1, n)

def mktbl(data, cw, hcol=BLUE, fontsize=8):
    ts = [
        ('BACKGROUND',    (0,0),(-1,0),  hcol),
        ('TEXTCOLOR',     (0,0),(-1,0),  WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,-1), fontsize),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('ALIGN',         (0,1),(0,-1),  'LEFT'),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
        ('GRID',          (0,0),(-1,-1), 0.3, MGREY),
    ]
    for i in range(1, len(data), 2):
        ts.append(('BACKGROUND',(0,i),(-1,i), LGREY))
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle(ts))
    return t

def banner(txt, col, W):
    t = Table([[Paragraph(txt, PS('bh', 12, True, WHITE))]], colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),col),
        ('TOPPADDING',(0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),12),
    ]))
    return t

def kpi_row(items, W):
    n  = len(items)
    cw = W / n
    cells = []
    for lbl, val, note, nc in items:
        inner = Table([
            [Paragraph(val,  PS('kv',14,True,NAVY,TA_CENTER,0))],
            [Paragraph(lbl,  PS('kl',8,False,colors.HexColor('#6B7280'),TA_CENTER,1))],
            [Paragraph(note, PS('kn',8,False,nc,TA_CENTER,0))],
        ], colWidths=[cw-4])
        inner.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),LGREY),
            ('BOX',(0,0),(-1,-1),0.5,MGREY),
            ('TOPPADDING',(0,0),(-1,-1),7),
            ('BOTTOMPADDING',(0,0),(-1,-1),7),
        ]))
        cells.append(inner)
    row = Table([cells], colWidths=[cw]*n)
    row.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2)]))
    return row

def chart_img(fig, W, h=200):
    """Convert plotly figure to inline Image for PDF."""
    try:
        buf = io.BytesIO()
        fig.update_layout(
            paper_bgcolor='white', plot_bgcolor='white',
            font=dict(family='Helvetica', size=9),
            margin=dict(l=40,r=20,t=30,b=40),
            height=h*3, width=int(W/cm*72*3)
        )
        img_bytes = pio.to_image(fig, format='png', scale=1)
        buf = io.BytesIO(img_bytes)
        return Image(buf, width=W, height=h*cm/cm*h/100*cm)
    except Exception:
        return Paragraph("(Chart — install kaleido: pip install kaleido)",
                         PS('nc',8,False,AMBER))

def footer_tbl(analyst, period, channel, W):
    t = Table([[Paragraph(
        f"iDealz {channel} Report  ·  {analyst}  ·  {period}  ·  Confidential",
        PS('ft',8,False,colors.HexColor('#9CA3AF'),TA_CENTER))]],colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),NAVY),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t

def header_tbl(title, subtitle, period, analyst, W):
    rows = [
        [Paragraph(title,    PS('ht',20,True,WHITE,TA_CENTER,2))],
        [Paragraph(subtitle, PS('hs',10,False,colors.HexColor('#9CA3AF'),TA_CENTER,2))],
        [Paragraph(f"Period: {period}  ·  Analyst: {analyst}  ·  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
                   PS('hd',9,False,colors.HexColor('#9CA3AF'),TA_CENTER,0))],
    ]
    t = Table(rows, colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),NAVY),
        ('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14),
        ('LEFTPADDING',(0,0),(-1,-1),10)]))
    return t

# ─────────────────────────────────────────────────────────────────────────────
# META PDF REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_meta_pdf(meta_df, analyst, period, alerts=None, meta_prev=None):
    buf = io.BytesIO()
    W   = A4[0] - 4*cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    story = []

    # Header
    story += [header_tbl("iDealz Meta Ads Report", "Facebook & Instagram Ad Performance Analysis", period, analyst, W), sp(12)]

    # Alerts
    if alerts:
        meta_alerts = [a for a in alerts if 'meta' in a.get('title','').lower() or 'facebook' in a.get('title','').lower() or 'instagram' in a.get('title','').lower()]
        if meta_alerts:
            story += [banner("⚠  Alerts", RED, W), sp(6)]
            al = [['#','Alert','Action']]
            for i,a in enumerate(meta_alerts,1): al.append([str(i), a['title'], a['msg']])
            story += [mktbl(al,[0.5*cm,5*cm,W-5.5*cm],RED), sp(12)]

    # ── KPIs ──
    story += [banner("📊  Performance Overview", BLUE, W), sp(8)]
    ts  = meta_df['Amount spent (LKR)'].sum()
    tr  = int(meta_df['Results'].sum())
    cpr = ts/tr if tr>0 else 0
    ctr = meta_df['CTR (link click-through rate)'].mean()
    cpm = meta_df['CPM (cost per 1,000 impressions)'].mean()
    cpc = meta_df['CPC (cost per link click)'].mean()
    frq = meta_df['Frequency'].mean()
    impr= int(meta_df['Impressions'].sum())
    rch = int(meta_df['Reach'].sum())
    clk = int(meta_df['Link clicks'].sum())

    story.append(kpi_row([
        ('Total Spend',    f"Rs {ts:,.0f}",   '—',              colors.HexColor('#6B7280')),
        ('Total Results',  f"{tr:,}",           '—',              colors.HexColor('#6B7280')),
        ('Cost/Result',    f"Rs {cpr:,.2f}",   '⚠ High' if cpr>25 else '✅ Good', RED if cpr>25 else GREEN),
        ('Avg CTR',        f"{ctr:.2f}%",       '✅ Good' if ctr>=1.5 else '⚠ Low', GREEN if ctr>=1.5 else AMBER),
        ('Avg CPM',        f"Rs {cpm:,.0f}",   '—',              colors.HexColor('#6B7280')),
        ('Avg Frequency',  f"{frq:.2f}",        '⚠ High' if frq>3 else '✅ OK', RED if frq>3 else GREEN),
    ], W))
    story.append(sp(10))

    kpi2 = [['Total Impressions','Total Reach','Total Clicks','Avg CPC']]
    kpi2.append([f"{impr:,}", f"{rch:,}", f"{clk:,}", f"Rs {cpc:,.2f}"])
    story += [mktbl(kpi2,[W/4]*4,BLUE), sp(12)]

    # vs previous
    if meta_prev is not None:
        story += [Paragraph("vs Previous Period:", PS('pph',10,True,NAVY,sp=4)), sp(4)]
        pv_ts = meta_prev['Amount spent (LKR)'].sum()
        pv_tr = int(meta_prev['Results'].sum())
        pv_rch= int(meta_prev['Reach'].sum())
        prev_data = [['Metric','This Period','Previous Period','Change']]
        for metric, curr, prev in [
            ('Spend (LKR)', f"Rs {ts:,.0f}", f"Rs {pv_ts:,.0f}", f"{(ts-pv_ts)/pv_ts*100:+.1f}%" if pv_ts>0 else '—'),
            ('Results',     str(tr),          str(pv_tr),          f"{(tr-pv_tr)/pv_tr*100:+.1f}%"  if pv_tr>0 else '—'),
            ('Reach',       f"{rch:,}",       f"{pv_rch:,}",       f"{(rch-pv_rch)/pv_rch*100:+.1f}%" if pv_rch>0 else '—'),
        ]:
            prev_data.append([metric, curr, prev, change])
        story += [mktbl(prev_data,[4*cm,4*cm,4*cm,W-12*cm],BLUE), sp(12)]

    # ── Platform FB vs IG ──
    story += [banner("📱  Facebook vs Instagram", BLUE, W), sp(8)]
    if 'Platform' in meta_df.columns:
        plat = meta_df.groupby('Platform').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum'),
            Avg_CPM=('CPM (cost per 1,000 impressions)','mean'),
            Avg_CPC=('CPC (cost per link click)','mean'),
            Avg_CTR=('CTR (link click-through rate)','mean'),
            Avg_Freq=('Frequency','mean'),
        ).round(2).reset_index()
        plat['CPR'] = (plat['Spend']/plat['Results'].replace(0,1)).round(2)

        try:
            fig = px.bar(plat, x='Platform', y=['Results','Spend'], barmode='group',
                         title='Results & Spend by Platform',
                         color_discrete_map={'Results':'#378ADD','Spend':'#D4537E'})
            fig.update_layout(height=300, paper_bgcolor='white', plot_bgcolor='white')
            story.append(chart_img(fig, W, 160))
        except Exception: pass

        pd_rows = [['Platform','Spend (LKR)','Results','CPR','CTR','CPM','CPC','Freq']]
        for _,r in plat.iterrows():
            pd_rows.append([r['Platform'].title(), f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                f"Rs {r['CPR']:,.2f}", f"{r['Avg_CTR']:.2f}%",
                f"Rs {r['Avg_CPM']:,.0f}", f"Rs {r['Avg_CPC']:,.0f}", f"{r['Avg_Freq']:.2f}"])
        story += [sp(6), mktbl(pd_rows,[3*cm,3*cm,2*cm,2.5*cm,2*cm,2.5*cm,2.5*cm,W-17.5*cm],BLUE), sp(12)]

    # ── Ad Set Deep Dive ──
    story += [banner("📂  Ad Set Analysis — CPM · CPC · CTR", BLUE, W), sp(8)]
    if 'Ad set name' in meta_df.columns:
        adset = meta_df.groupby('Ad set name').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum'),
            Avg_CPM=('CPM (cost per 1,000 impressions)','mean'),
            Avg_CPC=('CPC (cost per link click)','mean'),
            Avg_CTR=('CTR (link click-through rate)','mean'),
            Avg_Freq=('Frequency','mean'),
        ).round(2).reset_index()
        adset['CPR'] = (adset['Spend']/adset['Results'].replace(0,1)).round(2)

        try:
            fig = px.bar(adset.sort_values('Avg_CTR',ascending=False),
                         x='Ad set name', y='Avg_CTR', color='Avg_CTR',
                         color_continuous_scale='Greens', title='CTR by Ad Set (%)',
                         text='Avg_CTR')
            fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig.update_layout(height=300, paper_bgcolor='white', plot_bgcolor='white', showlegend=False)
            story.append(chart_img(fig, W, 160))
        except Exception: pass

        as_rows = [['Ad Set','Spend','Results','CPR','CTR','CPM','CPC','Freq']]
        for _,r in adset.sort_values('Results',ascending=False).iterrows():
            nm = str(r['Ad set name'])[:30]+'…' if len(str(r['Ad set name']))>30 else str(r['Ad set name'])
            as_rows.append([nm, f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                f"Rs {r['CPR']:,.2f}", f"{r['Avg_CTR']:.2f}%",
                f"Rs {r['Avg_CPM']:,.0f}", f"Rs {r['Avg_CPC']:,.0f}", f"{r['Avg_Freq']:.2f}"])
        story += [sp(6), mktbl(as_rows,[3.5*cm,2.5*cm,1.5*cm,2.5*cm,1.8*cm,2.5*cm,2.5*cm,W-16.8*cm],BLUE), sp(12)]

    # ── Campaign Pacing ──
    story += [banner("💰  Campaign Pacing vs Budget", BLUE, W), sp(8)]
    if 'Ad set name' in meta_df.columns:
        pacing = meta_df.groupby('Ad set name').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum')).round(2).reset_index()
        avg_sp = pacing['Spend'].mean()
        pacing['vs_avg_%'] = ((pacing['Spend']-avg_sp)/avg_sp*100).round(1)
        pacing['Status'] = pacing['vs_avg_%'].apply(
            lambda x: '🔴 Overspending' if x>30 else ('🟡 Slightly over' if x>10
                      else ('🟢 On track' if x>-10 else '⚠ Underspending')))
        pc_rows = [['Ad Set','Spend (LKR)','Results','vs Avg','Status']]
        for _,r in pacing.sort_values('Spend',ascending=False).iterrows():
            nm = str(r['Ad set name'])[:35]+'…' if len(str(r['Ad set name']))>35 else str(r['Ad set name'])
            pc_rows.append([nm, f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                            f"{r['vs_avg_%']:+.1f}%", r['Status']])
        story += [mktbl(pc_rows,[5*cm,3*cm,2*cm,2.5*cm,W-12.5*cm],BLUE), sp(12)]

    # ── Top & Bottom Ads ──
    story += [banner("🏆  Top & Bottom Performing Ads", BLUE, W), sp(8)]
    active = meta_df[meta_df['Results']>0].copy()
    if len(active)>0:
        story.append(Paragraph("Top 10 Ads — Lowest Cost per Result:", PS('h3',10,True,NAVY,sp=4)))
        t5r = [['Ad Name','Platform','Results','Cost/Result','Spend','CTR']]
        for _,r in active.sort_values('Cost per result').head(10).iterrows():
            nm = str(r['Ad name'])[:38]+'…' if len(str(r['Ad name']))>38 else str(r['Ad name'])
            t5r.append([nm, r['Platform'].title(), str(int(r['Results'])),
                f"Rs {r['Cost per result']:,.2f}", f"Rs {r['Amount spent (LKR)']:,.0f}",
                f"{r['CTR (link click-through rate)']:.2f}%"])
        story += [mktbl(t5r,[5*cm,2*cm,1.5*cm,3*cm,2.5*cm,W-14*cm],BLUE), sp(8)]

        story.append(Paragraph("Bottom 10 Ads — Highest Cost per Result (review for pausing):", PS('h3',10,True,RED,sp=4)))
        b5r = [['Ad Name','Platform','Results','Cost/Result','Spend','CTR']]
        for _,r in active.sort_values('Cost per result',ascending=False).head(10).iterrows():
            nm = str(r['Ad name'])[:38]+'…' if len(str(r['Ad name']))>38 else str(r['Ad name'])
            b5r.append([nm, r['Platform'].title(), str(int(r['Results'])),
                f"Rs {r['Cost per result']:,.2f}", f"Rs {r['Amount spent (LKR)']:,.0f}",
                f"{r['CTR (link click-through rate)']:.2f}%"])
        story += [mktbl(b5r,[5*cm,2*cm,1.5*cm,3*cm,2.5*cm,W-14*cm],colors.HexColor('#A03060')), sp(8)]

        try:
            fig = px.scatter(active, x='Amount spent (LKR)', y='CTR (link click-through rate)',
                             color='Platform', size='Results', hover_name='Ad name',
                             title='Spend vs CTR (bubble size = results)',
                             color_discrete_map={'facebook':'#378ADD','instagram':'#D4537E',
                                                 'Facebook':'#378ADD','Instagram':'#D4537E'})
            fig.add_hline(y=1.5, line_dash='dash', line_color='#BA7517')
            fig.update_layout(height=300, paper_bgcolor='white', plot_bgcolor='white')
            story += [sp(4), chart_img(fig, W, 160)]
        except Exception: pass
        story.append(sp(12))

    # ── Frequency Check ──
    story += [banner("🔄  Frequency & Audience Fatigue", BLUE, W), sp(8)]
    fatigued = meta_df[meta_df['Frequency']>3]
    if len(fatigued)>0:
        story.append(Paragraph(f"⚠ {len(fatigued)} ads with frequency above 3.0 — audience needs refreshing.", PS('fa',10,False,RED,sp=4)))
        fa_rows = [['Ad Name','Platform','Frequency','Spend','Results']]
        for _,r in fatigued.sort_values('Frequency',ascending=False).iterrows():
            nm = str(r['Ad name'])[:40]
            fa_rows.append([nm, r['Platform'].title(), f"{r['Frequency']:.2f}",
                f"Rs {r['Amount spent (LKR)']:,.0f}", str(int(r['Results']))])
        story += [mktbl(fa_rows,[5.5*cm,2*cm,2*cm,3*cm,W-12.5*cm],RED), sp(8)]
    else:
        story.append(Paragraph("✅ No fatigued audiences — all frequency below 3.0", PS('ok',10,False,GREEN,sp=4)))

    zero = meta_df[(meta_df['Results']==0)&(meta_df['Amount spent (LKR)']>100)]
    if len(zero)>0:
        story.append(Paragraph(f"⚠ {len(zero)} zero-result ads spending budget — consider pausing.", PS('zr',10,False,RED,sp=4)))
        zr_rows = [['Ad Name','Platform','Spend','Impressions']]
        for _,r in zero.iterrows():
            nm = str(r['Ad name'])[:45]
            zr_rows.append([nm, r['Platform'].title(),
                f"Rs {r['Amount spent (LKR)']:,.0f}", f"{int(r['Impressions']):,}"])
        story += [mktbl(zr_rows,[5.5*cm,2*cm,3.5*cm,W-11*cm],RED), sp(8)]

    # ── Placement ──
    if 'Placement' in meta_df.columns:
        story += [banner("📍  Placement Breakdown", BLUE, W), sp(8)]
        place = meta_df.groupby('Placement').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum'),
            Avg_CTR=('CTR (link click-through rate)','mean'),
            Avg_CPM=('CPM (cost per 1,000 impressions)','mean'),
        ).round(2).reset_index().sort_values('Results',ascending=False)
        place['CPR'] = (place['Spend']/place['Results'].replace(0,1)).round(2)
        pl_rows = [['Placement','Spend','Results','CPR','CTR','CPM']]
        for _,r in place.iterrows():
            pl_rows.append([str(r['Placement']), f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                f"Rs {r['CPR']:,.2f}", f"{r['Avg_CTR']:.2f}%", f"Rs {r['Avg_CPM']:,.0f}"])
        story += [mktbl(pl_rows,[4*cm,3*cm,2*cm,2.5*cm,2*cm,W-13.5*cm],BLUE), sp(12)]

    # ── Footer ──
    story.append(footer_tbl(analyst, period, "Meta Ads", W))
    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# TIKTOK PDF REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_tiktok_pdf(tiktok_df, analyst, period, alerts=None, tt_prev=None):
    buf = io.BytesIO()
    W   = A4[0] - 4*cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    story = []

    story += [header_tbl("iDealz TikTok Ads Report", "Video Performance & Engagement Analysis", period, analyst, W), sp(12)]

    if alerts:
        tt_alerts = [a for a in alerts if 'tiktok' in a.get('title','').lower()]
        if tt_alerts:
            story += [banner("⚠  Alerts", RED, W), sp(6)]
            al = [['#','Alert','Action']]
            for i,a in enumerate(tt_alerts,1): al.append([str(i), a['title'], a['msg']])
            story += [mktbl(al,[0.5*cm,5*cm,W-5.5*cm],RED), sp(12)]

    # ── KPIs ──
    story += [banner("📊  Performance Overview", PINK, W), sp(8)]
    ts   = tiktok_df['Cost'].sum()
    tv   = int(tiktok_df['Video views'].sum())
    aw   = tiktok_df['Average play time per video view'].mean()
    ac   = tiktok_df['100% video view rate'].mean()*100
    td   = int(tiktok_df['Clicks (destination)'].sum())
    ti   = int(tiktok_df['Impressions'].sum())
    tr   = int(tiktok_df['Reach'].sum())
    tf   = tiktok_df['Frequency'].mean()

    story.append(kpi_row([
        ('Total Spend',      f"${ts:,.2f}",  '—',              colors.HexColor('#6B7280')),
        ('Video Views',      f"{tv:,}",       '—',              colors.HexColor('#6B7280')),
        ('Avg Watch Time',   f"{aw:.1f}s",    '✅ Good' if aw>=6 else '⚠ Low', GREEN if aw>=6 else AMBER),
        ('Completion Rate',  f"{ac:.1f}%",    '⚠ Low' if ac<15 else '✅ OK',   RED   if ac<15 else GREEN),
        ('Dest. Clicks',     str(td),         '❌ Critical' if td==0 else '✅', RED   if td==0 else GREEN),
        ('Avg Frequency',    f"{tf:.2f}",     '—',              colors.HexColor('#6B7280')),
    ], W))
    story.append(sp(10))

    kpi2 = [['Total Impressions','Total Reach','Clicks (all)','Avg Frequency']]
    kpi2.append([f"{ti:,}", f"{tr:,}", f"{int(tiktok_df['Clicks (all)'].sum()):,}", f"{tf:.2f}"])
    story += [mktbl(kpi2,[W/4]*4,PINK), sp(12)]

    if td==0:
        story.append(Paragraph("❌ CRITICAL: Zero destination clicks — no one clicked to WhatsApp or idealz.lk from any TikTok ad. Add destination URL and CTA button in ad settings. Move CTA to first 3 seconds of video.", PS('crit',10,False,RED,sp=6)))

    # vs previous
    if tt_prev is not None:
        story += [Paragraph("vs Previous Period:", PS('pph',10,True,NAVY,sp=4)), sp(4)]
        pv_ts = tt_prev['Cost'].sum()
        pv_tv = int(tt_prev['Video views'].sum())
        pv_tr = int(tt_prev['Reach'].sum())
        prev_data = [['Metric','This Period','Previous Period','Change']]
        for metric, curr, prev, change in [
            ('Spend (USD)', f"${ts:,.2f}", f"${pv_ts:,.2f}", f"{(ts-pv_ts)/pv_ts*100:+.1f}%" if pv_ts>0 else '—'),
            ('Video Views', f"{tv:,}",     f"{pv_tv:,}",     f"{(tv-pv_tv)/pv_tv*100:+.1f}%" if pv_tv>0 else '—'),
            ('Reach',       f"{tr:,}",     f"{pv_tr:,}",     f"{(tr-pv_tr)/pv_tr*100:+.1f}%" if pv_tr>0 else '—'),
        ]:
            prev_data.append([metric, curr, prev, change])
        story += [mktbl(prev_data,[4*cm,4*cm,4*cm,W-12*cm],PINK), sp(12)]

    # ── Campaign Breakdown ──
    story += [banner("📂  Campaign Breakdown", PINK, W), sp(8)]
    camp = tiktok_df.groupby('Campaign name').agg(
        Spend=('Cost','sum'), Impressions=('Impressions','sum'), Reach=('Reach','sum'),
        Avg_Freq=('Frequency','mean'), Video_Views=('Video views','sum'),
        Avg_Watch=('Average play time per video view','mean'),
        Avg_Comp=('100% video view rate','mean'),
        Dest_Clicks=('Clicks (destination)','sum'),
    ).round(2).reset_index()
    camp['Comp_%'] = (camp['Avg_Comp']*100).round(1)

    try:
        fig = px.bar(camp, x='Campaign name', y=['Spend','Video_Views'],
                     barmode='group', title='Spend vs Video Views by Campaign',
                     color_discrete_map={'Spend':'#D4537E','Video_Views':'#1D9E75'})
        fig.update_layout(height=300, paper_bgcolor='white', plot_bgcolor='white')
        story.append(chart_img(fig, W, 160))
    except Exception: pass

    cr = [['Campaign','Spend (USD)','Impressions','Video Views','Avg Watch','Completion','Dest. Clicks']]
    for _,r in camp.iterrows():
        cr.append([str(r['Campaign name'])[:28], f"${r['Spend']:,.2f}", f"{int(r['Impressions']):,}",
            f"{int(r['Video_Views']):,}", f"{r['Avg_Watch']:.1f}s", f"{r['Comp_%']:.1f}%", str(int(r['Dest_Clicks']))])
    story += [sp(6), mktbl(cr,[4*cm,2.5*cm,2.5*cm,2.5*cm,2*cm,2.5*cm,W-16*cm],PINK), sp(12)]

    # ── Video Metrics Audit ──
    story += [banner("🎬  Video Metrics Audit — Completion & Watch Time", PINK, W), sp(8)]
    tiktok_df['comp_%'] = (tiktok_df['100% video view rate']*100).round(1)
    tiktok_df['2sec_%'] = (tiktok_df['2-second video views']/tiktok_df['Video views'].replace(0,1)*100).round(1)
    tiktok_df['6sec_%'] = (tiktok_df['6-second video views']/tiktok_df['Video views'].replace(0,1)*100).round(1)

    try:
        fig = px.bar(tiktok_df.sort_values('Average play time per video view',ascending=False),
                     x='Ad name', y='Average play time per video view',
                     color='Average play time per video view',
                     color_continuous_scale=['#E24B4A','#BA7517','#639922','#1D9E75'],
                     title='Avg Watch Time per Ad (seconds)', text='Average play time per video view')
        fig.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
        fig.update_layout(height=300, paper_bgcolor='white', plot_bgcolor='white', showlegend=False)
        story.append(chart_img(fig, W, 160))
    except Exception: pass

    vm_rows = [['Ad Name','Campaign','Watch Time','Completion','2-sec %','6-sec %','Dest. Clicks']]
    for _,r in tiktok_df.sort_values('Average play time per video view',ascending=False).iterrows():
        nm = str(r['Ad name'])[:28]+'…' if len(str(r['Ad name']))>28 else str(r['Ad name'])
        vm_rows.append([nm, str(r['Campaign name'])[:18],
            f"{r['Average play time per video view']:.1f}s", f"{r['comp_%']:.1f}%",
            f"{r['2sec_%']:.1f}%", f"{r['6sec_%']:.1f}%", str(int(r['Clicks (destination)']))])
    story += [sp(6), mktbl(vm_rows,[3.5*cm,2.5*cm,2.5*cm,2.5*cm,2*cm,2*cm,W-15*cm],PINK), sp(8)]

    story.append(Paragraph("Benchmark: 0–3s Very weak  |  3–6s Needs work  |  6–10s Good  |  10s+ Excellent  |  Completion: 25%+ Good", PS('bm',8,False,AMBER,sp=8)))

    # ── Video Funnel ──
    story += [banner("🔻  Video Engagement Funnel", PINK, W), sp(8)]
    sec2 = int(tiktok_df['2-second video views'].sum())
    sec6 = int(tiktok_df['6-second video views'].sum())
    full = int((tiktok_df['Video views']*tiktok_df['100% video view rate']).sum())
    fn_rows = [['Stage','Count','% of Impressions','Interpretation']]
    fn_rows += [
        ['Impressions',    f"{ti:,}",    '100%',                         '—'],
        ['Video Views',    f"{tv:,}",    f"{tv/ti*100:.1f}%" if ti>0 else '—', 'View-through rate'],
        ['2-sec Views',    f"{sec2:,}",  f"{sec2/ti*100:.1f}%" if ti>0 else '—', 'Initial hook strength'],
        ['6-sec Views',    f"{sec6:,}",  f"{sec6/ti*100:.1f}%" if ti>0 else '—', '⚠ Drop-off point — CTA too late' if sec6<sec2*0.5 else 'Decent retention'],
        ['Full Completion', f"{full:,}", f"{full/ti*100:.1f}%" if ti>0 else '—', '❌ Very low' if ac<10 else 'OK'],
        ['Dest. Clicks',   str(td),      f"{td/ti*100:.3f}%" if ti>0 else '—', '❌ Critical — fix URL' if td==0 else '✅'],
    ]
    story += [mktbl(fn_rows,[3*cm,3*cm,3.5*cm,W-9.5*cm],PINK), sp(12)]

    # ── Destination CTR ──
    story += [banner("🔗  Destination CTR Audit", PINK, W), sp(8)]
    ctr_rows = [['Ad Name','Campaign','Dest. CTR','Dest. Clicks','Impressions','Spend']]
    for _,r in tiktok_df.iterrows():
        nm = str(r['Ad name'])[:32]+'…' if len(str(r['Ad name']))>32 else str(r['Ad name'])
        ctr_rows.append([nm, str(r['Campaign name'])[:20],
            f"{r['CTR (destination)']:.4f}", str(int(r['Clicks (destination)'])),
            f"{int(r['Impressions']):,}", f"${r['Cost']:,.2f}"])
    story += [mktbl(ctr_rows,[4*cm,3*cm,2.5*cm,2.5*cm,2.5*cm,W-14.5*cm],PINK), sp(12)]

    # Footer
    story.append(footer_tbl(analyst, period, "TikTok Ads", W))
    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# WEBSITE PDF REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_website_pdf(ga4_bundle, analyst, period, alerts=None, gsc_bundle=None):
    buf = io.BytesIO()
    W   = A4[0] - 4*cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    story = []

    traffic_ch  = ga4_bundle.get('traffic_channel')
    traffic_src = ga4_bundle.get('traffic_source')
    users_df    = ga4_bundle.get('users')
    pages_df    = ga4_bundle.get('pages')
    events_df   = ga4_bundle.get('events')
    gsc_q       = gsc_bundle.get('queries') if gsc_bundle else None

    story += [header_tbl("iDealz Website Report", "GA4 Traffic, Engagement & SEO Analysis", period, analyst, W), sp(12)]

    if alerts:
        web_alerts = [a for a in alerts if 'website' in a.get('title','').lower() or 'ga4' in a.get('title','').lower() or 'utm' in a.get('title','').lower() or 'paid' in a.get('title','').lower()]
        if web_alerts:
            story += [banner("⚠  Alerts", RED, W), sp(6)]
            al = [['#','Alert','Action']]
            for i,a in enumerate(web_alerts,1): al.append([str(i), a['title'], a['msg']])
            story += [mktbl(al,[0.5*cm,5*cm,W-5.5*cm],RED), sp(12)]

    # ── KPIs ──
    if traffic_ch is not None:
        story += [banner("📊  Traffic Overview", GRNDK, W), sp(8)]
        col0 = traffic_ch.columns[0]
        ts   = int(traffic_ch['Sessions'].sum())
        es   = int(traffic_ch['Engaged sessions'].sum()) if 'Engaged sessions' in traffic_ch.columns else 0
        er   = traffic_ch['Engagement rate'].mean()*100   if 'Engagement rate' in traffic_ch.columns else 0
        ad   = traffic_ch['Average engagement time per session'].mean() if 'Average engagement time per session' in traffic_ch.columns else 0
        ev   = int(traffic_ch['Event count'].sum()) if 'Event count' in traffic_ch.columns else 0

        story.append(kpi_row([
            ('Total Sessions',   f"{ts:,}",  '—',                 colors.HexColor('#6B7280')),
            ('Engaged Sessions', f"{es:,}",  '—',                 colors.HexColor('#6B7280')),
            ('Engagement Rate',  f"{er:.1f}%", '✅ Good' if er>50 else '⚠ Low', GREEN if er>50 else AMBER),
            ('Avg Duration',     f"{ad:.0f}s",  '✅ Good' if ad>45 else '⚠ Low', GREEN if ad>45 else AMBER),
            ('Total Events',     f"{ev:,}",  '—',                 colors.HexColor('#6B7280')),
        ], W))
        story.append(sp(10))

        channels = traffic_ch[col0].astype(str).str.lower().tolist()
        if not any('paid' in c for c in channels):
            story.append(Paragraph("❌ No Paid Social traffic in GA4 — Meta & TikTok ads not tracked. Add UTM tags to all ad destination URLs.", PS('utm',10,False,RED,sp=6)))

        try:
            fig = px.bar(traffic_ch.sort_values('Sessions',ascending=False),
                         x=col0, y='Sessions', color=col0, text='Sessions',
                         title='Sessions by Channel',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textposition='outside')
            fig.update_layout(height=300, paper_bgcolor='white', plot_bgcolor='white', showlegend=False)
            story.append(chart_img(fig, W, 160))
        except Exception: pass

        tc = [['Channel','Sessions','Engaged','Eng. Rate','Avg Duration','Events']]
        for _,r in traffic_ch.iterrows():
            tc.append([str(r.iloc[0]), f"{int(r['Sessions']):,}",
                f"{int(r['Engaged sessions']):,}" if 'Engaged sessions' in traffic_ch.columns else '—',
                f"{r['Engagement rate']*100:.1f}%"     if 'Engagement rate' in traffic_ch.columns else '—',
                f"{r['Average engagement time per session']:.0f}s" if 'Average engagement time per session' in traffic_ch.columns else '—',
                f"{int(r['Event count']):,}" if 'Event count' in traffic_ch.columns else '—'])
        story += [sp(6), mktbl(tc,[4.5*cm,2*cm,2*cm,2*cm,2.5*cm,W-13*cm],GRNDK), sp(12)]

    # ── Source Medium ──
    if traffic_src is not None:
        story += [banner("🔍  Traffic Sources — Source / Medium", GRNDK, W), sp(8)]
        src_col = traffic_src.columns[0]
        top15   = traffic_src.sort_values('Sessions',ascending=False).head(15)
        sc = [['Source / Medium','Sessions','Eng. Rate','Avg Duration']]
        for _,r in top15.iterrows():
            sc.append([str(r.iloc[0])[:40], f"{int(r['Sessions']):,}",
                f"{r['Engagement rate']*100:.1f}%"     if 'Engagement rate' in traffic_src.columns else '—',
                f"{r['Average engagement time per session']:.0f}s" if 'Average engagement time per session' in traffic_src.columns else '—'])
        story += [mktbl(sc,[6*cm,2*cm,2*cm,W-10*cm],GRNDK), sp(8)]
        story += [Paragraph("❌ UTM Fix: Meta → ?utm_source=facebook&utm_medium=cpc  |  TikTok → ?utm_source=tiktok&utm_medium=cpc", PS('utm2',8,False,AMBER,sp=8))]
        story.append(sp(8))

    # ── Top Pages ──
    if pages_df is not None:
        story += [banner("📄  Top Pages — Engagement Analysis", GRNDK, W), sp(8)]
        pg_col = pages_df.columns[0]
        total_views = int(pages_df['Views'].sum()) if 'Views' in pages_df.columns else 0
        story.append(Paragraph(f"Total page views: {total_views:,}  |  Unique pages: {len(pages_df):,}", PS('pgsum',10,False,NAVY,sp=6)))

        try:
            fig = px.bar(pages_df.head(15), x='Views', y=pg_col, orientation='h',
                         title='Top 15 Pages by Views', color='Views',
                         color_continuous_scale='Greens', text='Views')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=360, paper_bgcolor='white', plot_bgcolor='white',
                              yaxis={'categoryorder':'total ascending'}, showlegend=False)
            story.append(chart_img(fig, W, 200))
        except Exception: pass

        pg_rows = [['Page','Views','Active Users','Avg Eng. Time','Events']]
        for _,r in pages_df.head(15).iterrows():
            path = str(r.iloc[0])
            path = path[:48]+'…' if len(path)>48 else path
            pg_rows.append([path, f"{int(r['Views']):,}",
                f"{int(r['Active users']):,}" if 'Active users' in pages_df.columns else '—',
                f"{r['Average engagement time per active user']:.0f}s" if 'Average engagement time per active user' in pages_df.columns else '—',
                f"{int(r['Event count']):,}" if 'Event count' in pages_df.columns else '—'])
        story += [sp(6), mktbl(pg_rows,[6.5*cm,1.5*cm,2*cm,2.5*cm,W-12.5*cm],GRNDK), sp(12)]

    # ── Users ──
    if users_df is not None:
        story += [banner("👥  User Acquisition", GRNDK, W), sp(8)]
        total_u = int(users_df['Total users'].sum())    if 'Total users'     in users_df.columns else 0
        new_u   = int(users_df['New users'].sum())      if 'New users'       in users_df.columns else 0
        ret_u   = int(users_df['Returning users'].sum())if 'Returning users' in users_df.columns else 0
        story.append(kpi_row([
            ('Total Users',     f"{total_u:,}", '—', colors.HexColor('#6B7280')),
            ('New Users',       f"{new_u:,}",   f"{new_u/total_u*100:.0f}% of total" if total_u>0 else '—', BLUE),
            ('Returning Users', f"{ret_u:,}",   f"{ret_u/total_u*100:.0f}% returning" if total_u>0 else '—', TEAL),
        ], W))
        story.append(sp(8))
        usr_col = users_df.columns[0]
        u_rows = [['Channel','Total Users','New Users','Returning']]
        for _,r in users_df.iterrows():
            u_rows.append([str(r.iloc[0]),
                f"{int(r['Total users']):,}"    if 'Total users'     in users_df.columns else '—',
                f"{int(r['New users']):,}"       if 'New users'       in users_df.columns else '—',
                f"{int(r['Returning users']):,}" if 'Returning users' in users_df.columns else '—'])
        story += [mktbl(u_rows,[5*cm,3*cm,3*cm,W-11*cm],GRNDK), sp(12)]

    # ── Events ──
    if events_df is not None:
        story += [banner("⚡  Events Tracked", GRNDK, W), sp(8)]
        if len(events_df)<=4:
            story.append(Paragraph("⚠ Only basic events tracked. No WhatsApp click or purchase events set up yet — conversion measurement is blocked.", PS('evw',10,False,AMBER,sp=6)))
        ev_rows = [['Event Name','Count','Total Users','Per User']]
        for _,r in events_df.iterrows():
            ev_rows.append([str(r.iloc[0]), f"{int(r['Event count']):,}",
                f"{int(r['Total users']):,}", f"{r['Event count per active user']:.2f}"])
        story += [mktbl(ev_rows,[4*cm,3*cm,3*cm,W-10*cm],GRNDK), sp(8)]
        story.append(Paragraph("To track WhatsApp clicks: add gtag('event','whatsapp_click') when WhatsApp button is clicked, then mark as Key Event in GA4.", PS('evrec',8,False,AMBER,sp=8)))
        story.append(sp(8))

    # ── SEO ──
    if gsc_q is not None:
        story += [banner("🔎  SEO Performance — Search Console", GRNDK, W), sp(8)]
        total_gc = int(gsc_q['Clicks'].sum()) if 'Clicks' in gsc_q.columns else 0
        total_gi = int(gsc_q['Impressions'].sum()) if 'Impressions' in gsc_q.columns else 0
        avg_pos  = gsc_q['Position'].mean() if 'Position' in gsc_q.columns else 0
        story.append(kpi_row([
            ('Search Clicks',      f"{total_gc:,}",  '—', colors.HexColor('#6B7280')),
            ('Search Impressions', f"{total_gi:,}",  '—', colors.HexColor('#6B7280')),
            ('Avg Position',       f"{avg_pos:.1f}", '✅ Good' if avg_pos<10 else '⚠ Needs work', GREEN if avg_pos<10 else AMBER),
        ], W))
        story.append(sp(8))
        q_col = gsc_q.columns[0]
        click_col = 'Clicks' if 'Clicks' in gsc_q.columns else gsc_q.columns[1]
        gq_rows = [[q_col.title(),'Clicks','Impressions','CTR','Position']]
        for _,r in gsc_q.sort_values(click_col,ascending=False).head(20).iterrows():
            gq_rows.append([str(r.iloc[0])[:40],
                f"{int(r['Clicks']):,}"      if 'Clicks'      in gsc_q.columns else '—',
                f"{int(r['Impressions']):,}" if 'Impressions' in gsc_q.columns else '—',
                f"{r['CTR']*100:.1f}%"       if 'CTR'         in gsc_q.columns else '—',
                f"{r['Position']:.1f}"       if 'Position'    in gsc_q.columns else '—'])
        story += [mktbl(gq_rows,[5.5*cm,2*cm,2.5*cm,2*cm,W-12*cm],GRNDK), sp(12)]
    else:
        story += [banner("🔎  SEO Performance", GRNDK, W), sp(8)]
        story.append(Paragraph("Upload Google Search Console CSV to see SEO keyword data.", PS('seon',10,False,AMBER,sp=8)))
        story.append(sp(8))

    story.append(footer_tbl(analyst, period, "Website", W))
    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# COMBINED WEEKLY SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_pdf_report(meta_df, tiktok_df, ga4_df, analyst, period, recs, alerts, extra=None):
    """Combined summary report — all 3 channels in one PDF."""
    buf = io.BytesIO()
    W   = A4[0] - 4*cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    story = []

    story += [header_tbl("iDealz Weekly Marketing Report",
                          "Meta · TikTok · Website — Combined Summary", period, analyst, W), sp(12)]

    if alerts:
        story += [banner("⚠  All Alerts", RED, W), sp(6)]
        al = [['#','Channel','Alert','Action']]
        for i,a in enumerate(alerts,1): al.append([str(i), a.get('title','').split(':')[0] if ':' in a.get('title','') else '—', a['title'], a['msg']])
        story += [mktbl(al,[0.5*cm,2*cm,4.5*cm,W-7*cm],RED), sp(12)]

    if meta_df is not None:
        ts  = meta_df['Amount spent (LKR)'].sum()
        tr  = int(meta_df['Results'].sum())
        cpr = ts/tr if tr>0 else 0
        ctr = meta_df['CTR (link click-through rate)'].mean()
        story += [banner("📘  Meta Summary", BLUE, W), sp(8)]
        story.append(kpi_row([
            ('Spend', f"Rs {ts:,.0f}", '—', colors.HexColor('#6B7280')),
            ('Results', str(tr), '—', colors.HexColor('#6B7280')),
            ('CPR', f"Rs {cpr:,.2f}", '⚠' if cpr>25 else '✅', RED if cpr>25 else GREEN),
            ('CTR', f"{ctr:.2f}%", '✅' if ctr>=1.5 else '⚠', GREEN if ctr>=1.5 else AMBER),
        ], W))
        story.append(sp(12))

    if tiktok_df is not None:
        story += [banner("🎵  TikTok Summary", PINK, W), sp(8)]
        aw = tiktok_df['Average play time per video view'].mean()
        td = int(tiktok_df['Clicks (destination)'].sum())
        story.append(kpi_row([
            ('Spend',        f"${tiktok_df['Cost'].sum():,.2f}", '—', colors.HexColor('#6B7280')),
            ('Video Views',  f"{int(tiktok_df['Video views'].sum()):,}", '—', colors.HexColor('#6B7280')),
            ('Watch Time',   f"{aw:.1f}s", '✅' if aw>=6 else '⚠', GREEN if aw>=6 else AMBER),
            ('Dest. Clicks', str(td), '❌ Critical' if td==0 else '✅', RED if td==0 else GREEN),
        ], W))
        story.append(sp(12))

    if ga4_df is not None:
        story += [banner("🌐  Website Summary", GRNDK, W), sp(8)]
        col0 = ga4_df.columns[0]
        ts_w = int(ga4_df['Sessions'].sum()) if 'Sessions' in ga4_df.columns else 0
        er_w = ga4_df['Engagement rate'].mean()*100 if 'Engagement rate' in ga4_df.columns else 0
        story.append(kpi_row([
            ('Sessions',      f"{ts_w:,}", '—', colors.HexColor('#6B7280')),
            ('Eng. Rate',     f"{er_w:.1f}%", '✅' if er_w>50 else '⚠', GREEN if er_w>50 else AMBER),
            ('Paid Social',   'Not tracked', '❌ UTMs missing', RED),
        ], W))
        story.append(sp(12))

    story += [banner("💡  Recommendations", AMBER, W), sp(8)]
    rc = [['#','Priority','Recommendation']]
    for i,r in enumerate(recs,1):
        if r.strip():
            priority = '🔴 Urgent' if i<=2 else ('🟡 High' if i<=4 else '🟢 Normal')
            rc.append([str(i), priority, r.strip()])
    story += [mktbl(rc,[0.5*cm,2.5*cm,W-3*cm],AMBER), sp(16)]
    story.append(footer_tbl(analyst, period, "Weekly Summary", W))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# EXCEL REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_excel_report(meta_df, tiktok_df, ga4_df, period, alerts, extra=None):
    buf = io.BytesIO()
    wb  = Workbook()
    wb.remove(wb.active)

    def hfill(hex_c): return PatternFill("solid", fgColor=hex_c.lstrip('#'))
    def tborder():
        s = Side(style='thin', color='FFD3D1C7')
        return Border(left=s,right=s,top=s,bottom=s)
    def write_df(ws, df, hcolor):
        for i,col in enumerate(df.columns,1):
            c = ws.cell(row=1,column=i,value=col)
            c.font=Font(bold=True,color='FFFFFFFF',size=10,name='Arial')
            c.fill=hfill(hcolor); c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
            c.border=tborder()
            ws.column_dimensions[get_column_letter(i)].width=max(14,len(str(col))+4)
        for ri,row in df.iterrows():
            for ci,val in enumerate(row,1):
                c=ws.cell(row=ri+2,column=ci,value=val)
                c.font=Font(size=10,name='Arial'); c.alignment=Alignment(horizontal='left',vertical='center')
                c.border=tborder()
                c.fill=PatternFill("solid",fgColor='FFFFFFFF' if ri%2==0 else 'FFF9F9F9')
        ws.row_dimensions[1].height=22

    # Summary
    ws = wb.create_sheet("Summary")
    ws.column_dimensions['A'].width = 28
    ws.column_dimensions['B'].width = 28
    ws.column_dimensions['C'].width = 22
    ws.column_dimensions['D'].width = 18
    ws.merge_cells('A1:D1')
    ws['A1'] = f'iDealz Marketing Analytics — {period}'
    ws['A1'].font=Font(bold=True,size=14,color='FFFFFFFF',name='Arial')
    ws['A1'].fill=hfill('#1A1A2E')
    ws['A1'].alignment=Alignment(horizontal='center',vertical='center')
    ws.row_dimensions[1].height=32

    r = 3
    def add_section(title, rows, color):
        nonlocal r
        ws.merge_cells(f'A{r}:D{r}')
        ws[f'A{r}']=title; ws[f'A{r}'].font=Font(bold=True,size=11,color='FFFFFFFF',name='Arial')
        ws[f'A{r}'].fill=hfill(color); ws[f'A{r}'].alignment=Alignment(horizontal='left',vertical='center')
        ws.row_dimensions[r].height=20; r+=1
        for row in rows:
            for ci,val in enumerate(row,1):
                c=ws.cell(row=r,column=ci,value=val)
                c.font=Font(size=10,name='Arial'); c.fill=PatternFill("solid",fgColor='FFF9F9F9' if r%2 else 'FFFFFFFF')
                c.border=tborder()
            r+=1
        r+=1

    if meta_df is not None:
        ts=meta_df['Amount spent (LKR)'].sum(); tr=int(meta_df['Results'].sum())
        add_section('META ADS SUMMARY',[
            ['Total Spend (LKR)',  f"Rs {ts:,.0f}", '', ''],
            ['Total Results',      str(tr), '', ''],
            ['Cost per Result',    f"Rs {ts/tr:,.2f}" if tr>0 else '—', 'Benchmark: < Rs 25',''],
            ['Avg CTR',            f"{meta_df['CTR (link click-through rate)'].mean():.2f}%",'Benchmark: 1.5%+',''],
            ['Avg Frequency',      f"{meta_df['Frequency'].mean():.2f}",'Max: 3.0',''],
        ], '#378ADD')

    if tiktok_df is not None:
        td=int(tiktok_df['Clicks (destination)'].sum())
        add_section('TIKTOK ADS SUMMARY',[
            ['Total Spend (USD)', f"${tiktok_df['Cost'].sum():,.2f}", '', ''],
            ['Total Video Views',  f"{int(tiktok_df['Video views'].sum()):,}", '', ''],
            ['Avg Watch Time',     f"{tiktok_df['Average play time per video view'].mean():.1f}s",'Benchmark: 6s+',''],
            ['Completion Rate',    f"{tiktok_df['100% video view rate'].mean()*100:.1f}%",'Benchmark: 25%+',''],
            ['Destination Clicks', str(td),'Should be > 0','❌ Critical' if td==0 else '✅'],
        ], '#D4537E')

    if ga4_df is not None:
        num_cols=ga4_df.select_dtypes(include='number').columns.tolist()
        sess_col=next((c for c in num_cols if 'session' in c.lower() and 'engaged' not in c.lower()),num_cols[0] if num_cols else None)
        add_section('WEBSITE (GA4) SUMMARY',[
            ['Total Sessions', f"{int(ga4_df[sess_col].sum()):,}" if sess_col else '—', '', ''],
            ['Paid Social',    'Not detected — UTMs missing', '', '❌'],
        ], '#3B6D11')

    if alerts:
        wa=wb.create_sheet("Alerts")
        wa.column_dimensions['A'].width=8; wa.column_dimensions['B'].width=30; wa.column_dimensions['C'].width=60
        for ci,h in enumerate(['Level','Alert','Detail'],1):
            c=wa.cell(row=1,column=ci,value=h); c.font=Font(bold=True,color='FFFFFFFF',size=10,name='Arial')
            c.fill=hfill('#E24B4A'); c.border=tborder()
        for ri,a in enumerate(alerts,2):
            wa.cell(row=ri,column=1,value=a['level'].upper()).border=tborder()
            wa.cell(row=ri,column=2,value=a['title']).border=tborder()
            wa.cell(row=ri,column=3,value=a['msg']).border=tborder()

    if meta_df is not None:   write_df(wb.create_sheet("Meta_Raw"),    meta_df, '#378ADD')
    if tiktok_df is not None: write_df(wb.create_sheet("TikTok_Raw"),  tiktok_df, '#D4537E')
    if ga4_df is not None:    write_df(wb.create_sheet("Website_Channel"), ga4_df, '#3B6D11')

    if extra:
        for key, sname, color in [
            ('traffic_source','Website_Source','#3B6D11'),
            ('users','Website_Users','#3B6D11'),
            ('pages','Website_Pages','#27500A'),
            ('events','Website_Events','#27500A'),
        ]:
            df_ex=extra.get(key)
            if df_ex is not None: write_df(wb.create_sheet(sname), df_ex, color)

    wb.save(buf); buf.seek(0)
    return buf.read()
