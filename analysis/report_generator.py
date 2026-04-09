import io
import pandas as pd
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from analysis.chart_utils import (
        bar_chart, hbar_chart, grouped_bar, pie_chart,
        scatter_chart, funnel_chart, color_bar
    )
except ImportError:
    from chart_utils import (
        bar_chart, hbar_chart, grouped_bar, pie_chart,
        scatter_chart, funnel_chart, color_bar
    )

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
def PS(name, fs=10, bold=False, color=None, align=TA_LEFT, sp=4, lft=0):
    return ParagraphStyle(name,
        fontName='Helvetica-Bold' if bold else 'Helvetica',
        fontSize=fs, textColor=color or colors.HexColor('#2C2C2A'),
        spaceAfter=sp, leading=fs+4, alignment=align, leftIndent=lft)

def sp(n=8):    return Spacer(1, n)
def shorten(s, n=30): s=str(s); return s[:n]+'…' if len(s)>n else s
def hr(W):      return HRFlowable(width=W, color=MGREY, thickness=0.5)

def mktbl(data, cw, hcol=BLUE):
    ts = [
        ('BACKGROUND',    (0,0),(-1,0),  hcol),
        ('TEXTCOLOR',     (0,0),(-1,0),  WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,-1), 8),
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
    t = Table([[Paragraph(txt, PS('bh',12,True,WHITE))]], colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),col),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),12),
    ]))
    return t

def kpi_row(items, W):
    n  = len(items)
    cw = W / n
    cells = []
    for lbl, val, note, nc in items:
        inner = Table([
            [Paragraph(val,  PS('kv',13,True, NAVY, TA_CENTER,0))],
            [Paragraph(lbl,  PS('kl', 8,False,colors.HexColor('#6B7280'),TA_CENTER,1))],
            [Paragraph(note, PS('kn', 8,False,nc,   TA_CENTER,0))],
        ], colWidths=[cw-4])
        inner.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),LGREY),
            ('BOX',(0,0),(-1,-1),0.5,MGREY),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ]))
        cells.append(inner)
    row = Table([cells], colWidths=[cw]*n)
    row.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2)]))
    return row

def two_charts(img1, img2):
    """Place two chart images side by side."""
    return Table([[img1, img2]], colWidths=['50%','50%'],
                 style=[('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2)])

def header_tbl(title, subtitle, period, analyst, W):
    rows = [
        [Paragraph(title,    PS('ht',20,True, WHITE,TA_CENTER,2))],
        [Paragraph(subtitle, PS('hs',10,False,colors.HexColor('#9CA3AF'),TA_CENTER,2))],
        [Paragraph(f"Period: {period}  ·  Analyst: {analyst}  ·  {datetime.now().strftime('%d %b %Y %H:%M')}",
                   PS('hd', 9,False,colors.HexColor('#9CA3AF'),TA_CENTER,0))],
    ]
    t = Table(rows, colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),NAVY),
        ('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14),
        ('LEFTPADDING',(0,0),(-1,-1),10)]))
    return t

def footer_tbl(analyst, period, channel, W):
    t = Table([[Paragraph(
        f"iDealz {channel} Report  ·  {analyst}  ·  {period}  ·  Confidential",
        PS('ft',8,False,colors.HexColor('#9CA3AF'),TA_CENTER))]],colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),NAVY),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t


# ═════════════════════════════════════════════════════════════════════════════
# META PDF REPORT
# ═════════════════════════════════════════════════════════════════════════════
def generate_meta_pdf(meta_df, analyst, period, alerts=None, meta_prev=None):
    buf = io.BytesIO()
    W   = A4[0] - 4*cm
    Wcm = W / cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    story = []

    story += [header_tbl("iDealz Meta Ads Report",
                          "Facebook & Instagram Ad Performance Analysis",
                          period, analyst, W), sp(12)]

    # Alerts
    if alerts:
        ma = [a for a in alerts if any(k in a.get('title','').lower()
              for k in ['meta','facebook','instagram','frequency','ctr','fatigue'])]
        if ma:
            story += [banner("⚠  Alerts", RED, W), sp(6)]
            al = [['#','Alert','Action']]
            for i,a in enumerate(ma,1): al.append([str(i), a['title'], a['msg']])
            story += [mktbl(al,[0.5*cm,5*cm,W-5.5*cm],RED), sp(12)]

    # ── KPIs ──
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

    story += [banner("📊  Performance Overview", BLUE, W), sp(8)]
    story.append(kpi_row([
        ('Total Spend',   f"Rs {ts:,.0f}",  '—',                   colors.HexColor('#6B7280')),
        ('Total Results', f"{tr:,}",          '—',                   colors.HexColor('#6B7280')),
        ('Cost/Result',   f"Rs {cpr:,.2f}",  '⚠ High' if cpr>25 else '✅ Good', RED if cpr>25 else GREEN),
        ('Avg CTR',       f"{ctr:.2f}%",      '✅' if ctr>=1.5 else '⚠ Low',    GREEN if ctr>=1.5 else AMBER),
        ('Avg CPM',       f"Rs {cpm:,.0f}",  '—',                   colors.HexColor('#6B7280')),
        ('Avg Frequency', f"{frq:.2f}",       '⚠ High' if frq>3 else '✅ OK',   RED if frq>3 else GREEN),
    ], W))
    story.append(sp(6))
    kpi2 = [['Total Impressions','Total Reach','Total Clicks','Avg CPC']]
    kpi2.append([f"{impr:,}", f"{rch:,}", f"{clk:,}", f"Rs {cpc:,.2f}"])
    story += [mktbl(kpi2,[W/4]*4,BLUE), sp(10)]

    # vs previous
    if meta_prev is not None:
        story.append(Paragraph("vs Previous Period:", PS('pv',10,True,NAVY,sp=4)))
        pv_ts=meta_prev['Amount spent (LKR)'].sum(); pv_tr=int(meta_prev['Results'].sum()); pv_rch=int(meta_prev['Reach'].sum())
        pd_rows = [['Metric','This Period','Previous','Change']]
        for m,c,p in [('Spend (LKR)',f"Rs {ts:,.0f}",f"Rs {pv_ts:,.0f}"),
                      ('Results',str(tr),str(pv_tr)),('Reach',f"{rch:,}",f"{pv_rch:,}")]:
            prev_v = float(str(p).replace('Rs ','').replace(',','')) if p!='—' else 0
            curr_v = float(str(c).replace('Rs ','').replace(',','')) if c!='—' else 0
            chg = f"{(curr_v-prev_v)/prev_v*100:+.1f}%" if prev_v>0 else '—'
            pd_rows.append([m,c,p,chg])
        story += [mktbl(pd_rows,[4*cm,4*cm,4*cm,W-12*cm],BLUE), sp(10)]

    # ── FB vs IG ──
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
        plat_colors = ['#378ADD' if 'face' in str(p).lower() else '#D4537E' for p in plat['Platform']]

        c1 = bar_chart(plat['Platform'].tolist(), plat['Results'].tolist(),
                       'Results by Platform', color=plat_colors, W=Wcm/2-1, H=6)
        c2 = bar_chart(plat['Platform'].tolist(), plat['CPR'].tolist(),
                       'Cost Per Result (Rs)', color=plat_colors,
                       fmt='Rs {:.0f}', W=Wcm/2-1, H=6)
        story.append(two_charts(c1, c2))
        story.append(sp(6))
        c3 = bar_chart(plat['Platform'].tolist(), plat['Avg_CTR'].tolist(),
                       'Avg CTR (%)', color=plat_colors, fmt='{:.2f}%', W=Wcm/2-1, H=6)
        c4 = bar_chart(plat['Platform'].tolist(), plat['Avg_CPM'].tolist(),
                       'Avg CPM (Rs)', color=plat_colors, fmt='Rs {:.0f}', W=Wcm/2-1, H=6)
        story += [two_charts(c3, c4), sp(6)]

        pd_rows = [['Platform','Spend (LKR)','Results','CPR','CTR','CPM','CPC','Freq']]
        for _,r in plat.iterrows():
            pd_rows.append([r['Platform'].title(), f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                f"Rs {r['CPR']:,.2f}", f"{r['Avg_CTR']:.2f}%",
                f"Rs {r['Avg_CPM']:,.0f}", f"Rs {r['Avg_CPC']:,.0f}", f"{r['Avg_Freq']:.2f}"])
        story += [mktbl(pd_rows,[3*cm,3*cm,2*cm,2.5*cm,2*cm,2.5*cm,2.5*cm,W-17.5*cm],BLUE), sp(12)]

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
        adset_s = adset.sort_values('Avg_CTR',ascending=False)

        c1 = color_bar(adset_s['Ad set name'].tolist(), adset_s['Avg_CTR'].tolist(),
                       'CTR by Ad Set (%)', cmap_name='Greens', fmt='{:.2f}%',
                       W=Wcm/2-1, H=max(6, len(adset)*0.7), rotate=30)
        c2 = color_bar(adset.sort_values('Avg_CPM')['Ad set name'].tolist(),
                       adset.sort_values('Avg_CPM')['Avg_CPM'].tolist(),
                       'CPM by Ad Set (Rs) — lower = better',
                       cmap_name='RdYlGn_r', fmt='Rs {:.0f}',
                       W=Wcm/2-1, H=max(6, len(adset)*0.7), rotate=30)
        story += [two_charts(c1, c2), sp(6)]

        c3 = color_bar(adset.sort_values('Avg_CPC')['Ad set name'].tolist(),
                       adset.sort_values('Avg_CPC')['Avg_CPC'].tolist(),
                       'CPC by Ad Set (Rs) — lower = better',
                       cmap_name='RdYlGn_r', fmt='Rs {:.0f}',
                       W=Wcm/2-1, H=max(6, len(adset)*0.7), rotate=30)
        c4 = bar_chart(adset.sort_values('Results',ascending=False)['Ad set name'].tolist(),
                       adset.sort_values('Results',ascending=False)['Results'].tolist(),
                       'Results by Ad Set', color='#378ADD',
                       W=Wcm/2-1, H=max(6, len(adset)*0.7), rotate=30)
        story += [two_charts(c3, c4), sp(6)]

        as_rows = [['Ad Set','Spend','Results','CPR','CTR','CPM','CPC','Freq']]
        for _,r in adset.sort_values('Results',ascending=False).iterrows():
            nm = str(r['Ad set name'])[:28]+'…' if len(str(r['Ad set name']))>28 else str(r['Ad set name'])
            as_rows.append([nm, f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                f"Rs {r['CPR']:,.2f}", f"{r['Avg_CTR']:.2f}%",
                f"Rs {r['Avg_CPM']:,.0f}", f"Rs {r['Avg_CPC']:,.0f}", f"{r['Avg_Freq']:.2f}"])
        story += [mktbl(as_rows,[3.5*cm,2.5*cm,1.5*cm,2.5*cm,1.8*cm,2.5*cm,2.5*cm,W-16.8*cm],BLUE), sp(12)]

    # ── Campaign Pacing ──
    story += [banner("💰  Campaign Pacing vs Budget", BLUE, W), sp(8)]
    if 'Ad set name' in meta_df.columns:
        pacing = meta_df.groupby('Ad set name').agg(
            Spend=('Amount spent (LKR)','sum'), Results=('Results','sum')).round(2).reset_index()
        avg_sp = pacing['Spend'].mean()
        pacing['vs_avg_%'] = ((pacing['Spend']-avg_sp)/avg_sp*100).round(1)
        pacing['Status'] = pacing['vs_avg_%'].apply(
            lambda x:'🔴 Overspending' if x>30 else('🟡 Slightly over' if x>10
                     else('🟢 On track' if x>-10 else '⚠ Underspending')))
        pc_s = pacing.sort_values('Spend',ascending=False)
        chart = color_bar(pc_s['Ad set name'].tolist(), pc_s['Spend'].tolist(),
                          'Spend by Ad Set vs Average', cmap_name='RdYlGn_r',
                          fmt='Rs {:.0f}', W=Wcm, H=6, rotate=30)
        story += [chart, sp(6)]
        pc_rows = [['Ad Set','Spend (LKR)','Results','vs Avg','Status']]
        for _,r in pc_s.iterrows():
            nm = str(r['Ad set name'])[:32]+'…' if len(str(r['Ad set name']))>32 else str(r['Ad set name'])
            pc_rows.append([nm, f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                            f"{r['vs_avg_%']:+.1f}%", r['Status']])
        story += [mktbl(pc_rows,[5*cm,3*cm,2*cm,2.5*cm,W-12.5*cm],BLUE), sp(12)]

    # ── Top & Bottom Ads ──
    story += [banner("🏆  Top & Bottom Performing Ads", BLUE, W), sp(8)]
    active = meta_df[meta_df['Results']>0].copy()
    if len(active)>0:
        top10 = active.sort_values('Cost per result').head(10)
        bot10 = active.sort_values('Cost per result',ascending=False).head(10)

        c1 = hbar_chart(top10['Ad name'].str[:25].tolist(),
                        top10['Cost per result'].tolist(),
                        'Top 10 Ads — Lowest CPR (Rs)', colormap='Greens',
                        fmt='Rs {:.0f}', W=Wcm/2-1, H=max(7, len(top10)*0.8))
        c2 = hbar_chart(bot10['Ad name'].str[:25].tolist(),
                        bot10['Cost per result'].tolist(),
                        'Bottom 10 Ads — Highest CPR (Rs)', colormap='Reds',
                        fmt='Rs {:.0f}', W=Wcm/2-1, H=max(7, len(bot10)*0.8))
        story += [two_charts(c1, c2), sp(6)]

        # Spend vs CTR scatter
        p_colors = ['#378ADD' if 'face' in str(p).lower() else '#D4537E'
                    for p in active['Platform']]
        c_scatter = scatter_chart(
            active['Amount spent (LKR)'].tolist(),
            active['CTR (link click-through rate)'].tolist(),
            active['Ad name'].tolist(),
            'Spend vs CTR per Ad (size = results)',
            hline=1.5, hline_label='1.5% CTR benchmark',
            colors_list=p_colors,
            sizes=active['Results'].tolist(),
            W=Wcm, H=7,
            xlabel='Amount Spent (LKR)', ylabel='CTR (%)')
        story += [c_scatter, sp(6)]

        t5r = [['Ad Name','Platform','Results','Cost/Result','Spend','CTR']]
        for _,r in top10.iterrows():
            nm = str(r['Ad name'])[:38]+'…' if len(str(r['Ad name']))>38 else str(r['Ad name'])
            t5r.append([nm, r['Platform'].title(), str(int(r['Results'])),
                f"Rs {r['Cost per result']:,.2f}", f"Rs {r['Amount spent (LKR)']:,.0f}",
                f"{r['CTR (link click-through rate)']:.2f}%"])
        story += [mktbl(t5r,[5*cm,2*cm,1.5*cm,3*cm,2.5*cm,W-14*cm],BLUE), sp(8)]

        b5r = [['Ad Name','Platform','Results','Cost/Result','Spend','CTR']]
        for _,r in bot10.iterrows():
            nm = str(r['Ad name'])[:38]+'…' if len(str(r['Ad name']))>38 else str(r['Ad name'])
            b5r.append([nm, r['Platform'].title(), str(int(r['Results'])),
                f"Rs {r['Cost per result']:,.2f}", f"Rs {r['Amount spent (LKR)']:,.0f}",
                f"{r['CTR (link click-through rate)']:.2f}%"])
        story += [mktbl(b5r,[5*cm,2*cm,1.5*cm,3*cm,2.5*cm,W-14*cm],colors.HexColor('#A03060')), sp(12)]

    # ── Frequency ──
    story += [banner("🔄  Frequency & Audience Fatigue", BLUE, W), sp(8)]
    fatigued = meta_df[meta_df['Frequency']>3]
    if len(fatigued)>0:
        story.append(Paragraph(f"⚠ {len(fatigued)} ads with frequency > 3.0 — audience needs refreshing.", PS('fa',10,False,RED,sp=4)))
        fa_rows = [['Ad Name','Platform','Frequency','Spend','Results']]
        for _,r in fatigued.sort_values('Frequency',ascending=False).iterrows():
            fa_rows.append([str(r['Ad name'])[:40], r['Platform'].title(),
                f"{r['Frequency']:.2f}", f"Rs {r['Amount spent (LKR)']:,.0f}", str(int(r['Results']))])
        story += [mktbl(fa_rows,[5.5*cm,2*cm,2*cm,3*cm,W-12.5*cm],RED), sp(8)]
    else:
        story.append(Paragraph("✅ No fatigued audiences — all frequency below 3.0", PS('ok',10,False,GREEN,sp=4)))

    # Frequency histogram
    freq_vals = meta_df['Frequency'].dropna().tolist()
    if freq_vals:
        import matplotlib; matplotlib.use('Agg')
        import matplotlib.pyplot as plt, io as _io
        fig, ax = plt.subplots(figsize=(Wcm/2.54, 4/2.54))
        ax.hist(freq_vals, bins=20, color='#378ADD', edgecolor='white', alpha=0.8)
        ax.axvline(x=3, color='#E24B4A', linestyle='--', linewidth=1, label='Fatigue threshold (3.0)')
        ax.legend(fontsize=7); ax.set_title('Frequency Distribution', fontsize=9, fontweight='bold')
        ax.set_xlabel('Frequency', fontsize=8); ax.set_ylabel('Ad count', fontsize=8)
        ax.tick_params(labelsize=7)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.set_facecolor('#FAFAFA'); fig.tight_layout()
        buf2 = _io.BytesIO(); fig.savefig(buf2, format='png', dpi=150, bbox_inches='tight', facecolor='white'); plt.close(fig); buf2.seek(0)
        story += [Image(buf2, width=W/2, height=4*cm), sp(8)]

    zero = meta_df[(meta_df['Results']==0)&(meta_df['Amount spent (LKR)']>100)]
    if len(zero)>0:
        story.append(Paragraph(f"⚠ {len(zero)} zero-result ads spending budget — consider pausing.", PS('zr',10,False,RED,sp=4)))
        zr_rows = [['Ad Name','Platform','Spend','Impressions']]
        for _,r in zero.iterrows():
            zr_rows.append([str(r['Ad name'])[:45], r['Platform'].title(),
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
        c1 = pie_chart(place['Placement'].tolist(), place['Spend'].tolist(),
                       'Spend by Placement', W=Wcm/2-1, H=7)
        c2 = bar_chart(place['Placement'].tolist(), place['Avg_CTR'].tolist(),
                       'CTR by Placement (%)', color='#639922',
                       fmt='{:.2f}%', W=Wcm/2-1, H=7, rotate=20)
        story += [two_charts(c1, c2), sp(6)]
        pl_rows = [['Placement','Spend','Results','CPR','CTR','CPM']]
        for _,r in place.iterrows():
            pl_rows.append([str(r['Placement']), f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                f"Rs {r['CPR']:,.2f}", f"{r['Avg_CTR']:.2f}%", f"Rs {r['Avg_CPM']:,.0f}"])
        story += [mktbl(pl_rows,[4*cm,3*cm,2*cm,2.5*cm,2*cm,W-13.5*cm],BLUE), sp(12)]

    story.append(footer_tbl(analyst, period, "Meta Ads", W))
    doc.build(story)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════════════════════
# TIKTOK PDF REPORT
# ═════════════════════════════════════════════════════════════════════════════
def generate_tiktok_pdf(df, analyst, period, alerts=None, prev_df=None):
    buf  = io.BytesIO()
    W    = A4[0] - 4*cm
    Wcm  = W / cm
    doc  = SimpleDocTemplate(buf, pagesize=A4,
           leftMargin=2*cm, rightMargin=2*cm,
           topMargin=1.5*cm, bottomMargin=2*cm)
    story = []

    # ── HEADER ──
    story += [header_tbl("iDealz TikTok Ads Report",
                         "Video Performance & Engagement Analysis",
                         period, analyst, W), sp(14)]

    # ── ALERTS ──
    if alerts:
        ta = [a for a in alerts if 'tiktok' in a.get('title','').lower()]
        if ta:
            story += [banner("⚠  Alerts", RED, W), sp(6)]
            al = [['#','Alert','Action Required']]
            for i,a in enumerate(ta,1):
                al.append([str(i),
                    Paragraph(a['title'], PS('at',8,False)),
                    Paragraph(a['msg'],   PS('am',8,False))])
            story += [mktbl(al,[1*cm, 5.5*cm, W-6.5*cm], RED), sp(14)]

    # ── OVERVIEW KPIs ──
    ts  = df['Cost'].sum()
    tv  = int(df['Video views'].sum())
    aw  = df['Average play time per video view'].mean()
    ac  = df['100% video view rate'].mean()*100
    td  = int(df['Clicks (destination)'].sum())
    ti  = int(df['Impressions'].sum())
    tr  = int(df['Reach'].sum())
    tf  = df['Frequency'].mean()
    tall= int(df['Clicks (all)'].sum())

    story += [banner("📊  Performance Overview", PINK, W), sp(8)]
    story.append(kpi_row([
        ('Total Spend',     f"${ts:,.2f}",  '—',                    colors.HexColor('#6B7280')),
        ('Video Views',     f"{tv:,}",       '—',                    colors.HexColor('#6B7280')),
        ('Avg Watch Time',  f"{aw:.1f}s",    '✅ Good' if aw>=6 else '⚠ Low', GREEN if aw>=6 else AMBER),
        ('Completion Rate', f"{ac:.1f}%",    '⚠ Low'  if ac<15 else '✅ OK',  RED   if ac<15 else GREEN),
        ('Dest. Clicks',    str(td),         '❌ Critical' if td==0 else '✅', RED   if td==0 else GREEN),
        ('Avg Frequency',   f"{tf:.2f}",     '—',                    colors.HexColor('#6B7280')),
    ], W))
    story.append(sp(6))

    kpi2 = [['Total Impressions','Total Reach','Clicks (all)','Avg Frequency']]
    kpi2.append([f"{ti:,}", f"{tr:,}", f"{tall:,}", f"{tf:.2f}"])
    story += [mktbl(kpi2,[W/4]*4, PINK), sp(8)]

    if td == 0:
        story.append(Paragraph(
            "❌  CRITICAL: Zero destination clicks — nobody clicked to WhatsApp or idealz.lk "
            "from any TikTok ad. Fix: (1) Set destination URL in every ad.  "
            "(2) Add 'Message Us' CTA button.  (3) Move CTA text to first 3 seconds of video.",
            PS('crit',9,False,RED,sp=10,lft=4)))

    # vs previous
    if prev_df is not None:
        story.append(Paragraph("vs Previous Period:", PS('pv',10,True,NAVY,sp=4)))
        pv_ts=prev_df['Cost'].sum(); pv_tv=int(prev_df['Video views'].sum()); pv_tr=int(prev_df['Reach'].sum())
        prev_tbl=[['Metric','This Period','Previous Period','Change']]
        for m,cv,pv in [('Spend (USD)',ts,pv_ts),('Video Views',tv,pv_tv),('Reach',tr,pv_tr)]:
            chg = f"{(cv-pv)/pv*100:+.1f}%" if pv>0 else '—'
            fv  = f"${cv:,.2f}" if 'Spend' in m else f"{int(cv):,}"
            fp  = f"${pv:,.2f}" if 'Spend' in m else f"{int(pv):,}"
            prev_tbl.append([m,fv,fp,chg])
        story += [mktbl(prev_tbl,[4*cm,4*cm,4*cm,W-12*cm],PINK), sp(10)]

    story.append(sp(4))

    # ── CAMPAIGN BREAKDOWN ──
    camp = df.groupby('Campaign name').agg(
        Spend=('Cost','sum'), Impressions=('Impressions','sum'),
        Reach=('Reach','sum'), Avg_Freq=('Frequency','mean'),
        Video_Views=('Video views','sum'),
        Avg_Watch=('Average play time per video view','mean'),
        Avg_Comp=('100% video view rate','mean'),
        Dest_Clicks=('Clicks (destination)','sum'),
    ).round(2).reset_index()
    camp['Comp_%'] = (camp['Avg_Comp']*100).round(1)

    hw = Wcm/2 - 0.5   # half width in cm
    c1 = bar_chart(camp['Campaign name'].tolist(), camp['Spend'].tolist(),
                   'Spend by Campaign (USD)', color='#D4537E',
                   fmt='${:.2f}', W=hw, H=6)
    c2 = bar_chart(camp['Campaign name'].tolist(), camp['Avg_Watch'].tolist(),
                   'Avg Watch Time (seconds)', color='#1D9E75',
                   fmt='{:.1f}s', W=hw, H=6)
    c3 = bar_chart(camp['Campaign name'].tolist(), camp['Comp_%'].tolist(),
                   'Completion Rate (%)', color='#BA7517',
                   fmt='{:.1f}%', W=hw, H=6)
    c4 = bar_chart(camp['Campaign name'].tolist(), camp['Video_Views'].tolist(),
                   'Video Views by Campaign', color='#D4537E',
                   W=hw, H=6)

    # Campaign table — 7 cols, precise widths
    cr = [['Campaign','Spend\n(USD)','Impressions','Video\nViews','Watch\nTime','Comp\n%','Dest\nClicks']]
    for _,r in camp.iterrows():
        cr.append([
            Paragraph(shorten(r['Campaign name'],22), PS('cn',8,False)),
            f"${r['Spend']:,.2f}",
            f"{int(r['Impressions']):,}",
            f"{int(r['Video_Views']):,}",
            f"{r['Avg_Watch']:.1f}s",
            f"{r['Comp_%']:.1f}%",
            str(int(r['Dest_Clicks'])),
        ])
    # col widths sum = W
    cr_cw = [3.8*cm, 2.2*cm, 2.5*cm, 2.2*cm, 1.8*cm, 1.8*cm, W-14.3*cm]

    story += [
        KeepTogether([banner("📂  Campaign Breakdown", PINK, W), sp(8),
                      two_charts(c1,c2), sp(6),
                      two_charts(c3,c4), sp(6),
                      mktbl(cr, cr_cw, PINK)]),
        sp(14)
    ]

    # ── VIDEO METRICS AUDIT ──
    df['comp_%'] = (df['100% video view rate']*100).round(1)
    df['2sec_%'] = (df['2-second video views']/df['Video views'].replace(0,1)*100).round(1)
    df['6sec_%'] = (df['6-second video views']/df['Video views'].replace(0,1)*100).round(1)
    tt_s = df.sort_values('Average play time per video view', ascending=False)

    ad_labels_short = [shorten(n, 18) for n in tt_s['Ad name']]

    c1 = color_bar(ad_labels_short, tt_s['Average play time per video view'].tolist(),
                   'Avg Watch Time per Ad (seconds)', cmap_name='RdYlGn',
                   fmt='{:.1f}s', W=hw, H=max(7, len(df)*0.55), rotate=35)
    c2 = color_bar([shorten(n,18) for n in df.sort_values('comp_%',ascending=False)['Ad name']],
                   df.sort_values('comp_%',ascending=False)['comp_%'].tolist(),
                   'Completion Rate per Ad (%)', cmap_name='RdYlGn',
                   fmt='{:.1f}%', W=hw, H=max(7, len(df)*0.55), rotate=35)

    tt2 = df.sort_values('2sec_%', ascending=False)
    c3  = grouped_bar(
        [shorten(n,14) for n in tt2['Ad name']],
        {'2-sec %': tt2['2sec_%'].tolist(), '6-sec %': tt2['6sec_%'].tolist()},
        '2-second vs 6-second View Rate per Ad (%)',
        W=Wcm, H=max(6, len(df)*0.55), rotate=35)

    # Video metrics table — 7 cols
    vm_rows = [['Ad Name','Campaign','Watch\nTime','Comp\n%','2-sec\n%','6-sec\n%','Dest\nClicks']]
    for _,r in tt_s.iterrows():
        vm_rows.append([
            Paragraph(shorten(r['Ad name'],26), PS('an',7.5,False)),
            Paragraph(shorten(r['Campaign name'],18), PS('cn',7.5,False)),
            f"{r['Average play time per video view']:.1f}s",
            f"{r['comp_%']:.1f}%",
            f"{r['2sec_%']:.1f}%",
            f"{r['6sec_%']:.1f}%",
            str(int(r['Clicks (destination)'])),
        ])
    # col widths: Ad name gets most space
    vm_cw = [3.8*cm, 2.8*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, W-12.6*cm]

    bm_para = Paragraph(
        "Benchmark:  0–3s Very weak  ·  3–6s Needs work  ·  6–10s Good  ·  10s+ Excellent  ·  Completion target: 25%+",
        PS('bm',8,False,AMBER,sp=6))

    drop_note = Paragraph(
        "Drop-off summary:  "
        f"Avg 2-sec view rate: {df['2sec_%'].mean():.1f}%  ·  "
        f"Avg 6-sec view rate: {df['6sec_%'].mean():.1f}%  ·  "
        f"Avg full completion: {df['comp_%'].mean():.1f}%",
        PS('dn',9,False,NAVY,sp=6))

    story += [
        KeepTogether([banner("🎬  Video Metrics Audit — Completion & Watch Time", PINK, W), sp(8),
                      two_charts(c1,c2), sp(6)]),
        c3, sp(6),
        mktbl(vm_rows, vm_cw, PINK),
        sp(4), drop_note, bm_para,
        sp(12)
    ]

    # ── VIDEO ENGAGEMENT FUNNEL ──
    sec2   = int(df['2-second video views'].sum())
    sec6   = int(df['6-second video views'].sum())
    full_v = int((df['Video views']*df['100% video view rate']).sum())
    stages = ['Impressions','Video Views','2-sec Views','6-sec Views','Full Views','Dest. Clicks']
    vals   = [ti, tv, sec2, sec6, full_v, td]

    interps = [
        '—',
        'Strong view-through rate (97%)',
        'Initial hook strength',
        '⚠ Drop-off here — CTA too late' if sec6<sec2*0.4 else 'Decent retention',
        '❌ Very low — move CTA to first 3s' if ac<10 else 'Below average',
        '❌ Fix destination URL' if td==0 else '✅ Clicks recorded',
    ]
    fn_rows = [['Stage','Count','% of Impressions','Interpretation']]
    for s,v,interp in zip(stages,vals,interps):
        fn_rows.append([s, f"{v:,}", f"{v/ti*100:.2f}%" if ti>0 else '—',
                        Paragraph(interp, PS('fi',8,False))])

    fn_cw  = [3*cm, 3*cm, 3.5*cm, W-9.5*cm]
    c_funnel = funnel_chart(stages, vals, 'Video Engagement Funnel',
                             color='#D4537E', W=Wcm, H=9)

    story += [
        KeepTogether([banner("🔻  Video Engagement Funnel", PINK, W), sp(8),
                      c_funnel, sp(8),
                      mktbl(fn_rows, fn_cw, PINK)]),
        sp(14)
    ]

    # ── DESTINATION CTR AUDIT ──
    note_txt = (
        "All destination CTR values are 0.0000 — no clicks to WhatsApp or idealz.lk from any ad.  "
        "Action required:  (1) Set destination URL in every TikTok ad.  "
        "(2) Add 'Message Us' CTA button in ad settings.  "
        "(3) Move CTA text/button to the first 3 seconds of the video."
        if td==0 else
        "Some ads have zero destination CTR — review those creatives."
    )
    # CTR table — 6 cols, precise widths
    ctr_rows = [['Ad Name','Campaign','Dest. CTR','Dest.\nClicks','Impressions','Spend\n(USD)']]
    for _,r in df.sort_values('Cost',ascending=False).iterrows():
        ctr_rows.append([
            Paragraph(shorten(r['Ad name'],28), PS('an',7.5,False)),
            Paragraph(shorten(r['Campaign name'],20), PS('cn',7.5,False)),
            f"{r['CTR (destination)']:.4f}",
            str(int(r['Clicks (destination)'])),
            f"{int(r['Impressions']):,}",
            f"${r['Cost']:,.2f}",
        ])
    ctr_cw = [4.0*cm, 3.0*cm, 2.0*cm, 1.8*cm, 2.5*cm, W-13.3*cm]

    story += [
        KeepTogether([
            banner("🔗  Destination CTR Audit", PINK, W), sp(6),
            Paragraph(note_txt, PS('cn2',9,False,RED if td==0 else AMBER, sp=8, lft=4)),
        ]),
        mktbl(ctr_rows, ctr_cw, PINK),
        sp(14)
    ]

    # ── MONTHLY BENCHMARKS ──
    story += [
        KeepTogether([
            banner("📈  Monthly Benchmarks Summary", PINK, W), sp(8),
            kpi_row([
                ('Total Spend',      f"${ts:,.2f}",   '—', colors.HexColor('#6B7280')),
                ('Total Impressions',f"{ti:,}",        '—', colors.HexColor('#6B7280')),
                ('Total Reach',      f"{tr:,}",        '—', colors.HexColor('#6B7280')),
                ('Total Views',      f"{tv:,}",        '—', colors.HexColor('#6B7280')),
                ('Dest. Clicks',     str(td),
                 '❌ Critical' if td==0 else '✅ OK',
                 RED if td==0 else GREEN),
            ], W),
            sp(6),
            Paragraph(
                "Month-over-month comparison will appear here once you upload the previous period "
                "TikTok export in the sidebar.",
                PS('mo',9,False,AMBER,sp=6)) if prev_df is None else sp(2),
        ]),
        sp(16)
    ]

    # ── FOOTER ──
    story.append(footer_tbl(analyst, period, "TikTok Ads", W))

    doc.build(story)
    buf.seek(0)
    return buf.read()


def generate_website_pdf(ga4_bundle, analyst, period, alerts=None, gsc_bundle=None):
    buf = io.BytesIO()
    W   = A4[0] - 4*cm
    Wcm = W / cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    story = []

    traffic_ch  = ga4_bundle.get('traffic_channel')
    traffic_src = ga4_bundle.get('traffic_source')
    users_df    = ga4_bundle.get('users')
    pages_df    = ga4_bundle.get('pages')
    events_df   = ga4_bundle.get('events')
    gsc_q       = gsc_bundle.get('queries') if gsc_bundle else None

    story += [header_tbl("iDealz Website Report",
                          "GA4 Traffic, Engagement & SEO Analysis",
                          period, analyst, W), sp(12)]

    if alerts:
        wa = [a for a in alerts if any(k in a.get('title','').lower()
              for k in ['website','ga4','utm','paid social','traffic','session'])]
        if wa:
            story += [banner("⚠  Alerts", RED, W), sp(6)]
            al = [['#','Alert','Action']]
            for i,a in enumerate(wa,1): al.append([str(i), a['title'], a['msg']])
            story += [mktbl(al,[0.5*cm,5*cm,W-5.5*cm],RED), sp(12)]

    # ── Traffic Overview ──
    if traffic_ch is not None:
        story += [banner("📊  Traffic Overview", GRNDK, W), sp(8)]
        col0 = traffic_ch.columns[0]
        ts   = int(traffic_ch['Sessions'].sum())
        es   = int(traffic_ch['Engaged sessions'].sum()) if 'Engaged sessions' in traffic_ch.columns else 0
        er   = traffic_ch['Engagement rate'].mean()*100  if 'Engagement rate'  in traffic_ch.columns else 0
        ad   = traffic_ch['Average engagement time per session'].mean() if 'Average engagement time per session' in traffic_ch.columns else 0
        ev   = int(traffic_ch['Event count'].sum()) if 'Event count' in traffic_ch.columns else 0

        story.append(kpi_row([
            ('Total Sessions',   f"{ts:,}",    '—',                 colors.HexColor('#6B7280')),
            ('Engaged Sessions', f"{es:,}",    '—',                 colors.HexColor('#6B7280')),
            ('Engagement Rate',  f"{er:.1f}%", '✅ Good' if er>50 else '⚠ Low', GREEN if er>50 else AMBER),
            ('Avg Duration',     f"{ad:.0f}s",  '✅ Good' if ad>45 else '⚠ Low', GREEN if ad>45 else AMBER),
            ('Total Events',     f"{ev:,}",    '—',                 colors.HexColor('#6B7280')),
        ], W))
        story.append(sp(6))

        channels = traffic_ch[col0].astype(str).str.lower().tolist()
        if not any('paid' in c for c in channels):
            story.append(Paragraph(
                "❌ No Paid Social in GA4 — Meta & TikTok spend not tracked. "
                "Add UTM tags: ?utm_source=facebook&utm_medium=cpc to all ad URLs.",
                PS('utmw',10,False,RED,sp=6)))

        c1 = bar_chart(traffic_ch[col0].tolist(), traffic_ch['Sessions'].tolist(),
                       'Sessions by Channel', color='#3B6D11',
                       W=Wcm/2-1, H=6, rotate=15)
        c2 = pie_chart(traffic_ch[col0].tolist(), traffic_ch['Sessions'].tolist(),
                       'Session Share', W=Wcm/2-1, H=6)
        story += [two_charts(c1, c2), sp(6)]

        if 'Engagement rate' in traffic_ch.columns:
            traffic_ch['Eng %'] = (traffic_ch['Engagement rate']*100).round(1)
            c3 = color_bar(traffic_ch[col0].tolist(), traffic_ch['Eng %'].tolist(),
                           'Engagement Rate by Channel (%)', cmap_name='RdYlGn',
                           fmt='{:.1f}%', W=Wcm, H=5, rotate=10)
            story += [c3, sp(6)]

        tc = [['Channel','Sessions','Engaged','Eng. Rate','Avg Duration','Events']]
        for _,r in traffic_ch.iterrows():
            tc.append([str(r.iloc[0]), f"{int(r['Sessions']):,}",
                f"{int(r['Engaged sessions']):,}" if 'Engaged sessions' in traffic_ch.columns else '—',
                f"{r['Engagement rate']*100:.1f}%"     if 'Engagement rate' in traffic_ch.columns else '—',
                f"{r['Average engagement time per session']:.0f}s" if 'Average engagement time per session' in traffic_ch.columns else '—',
                f"{int(r['Event count']):,}" if 'Event count' in traffic_ch.columns else '—'])
        story += [mktbl(tc,[4.5*cm,2*cm,2*cm,2*cm,2.5*cm,W-13*cm],GRNDK), sp(12)]

    # ── Source Medium ──
    if traffic_src is not None:
        story += [banner("🔍  Traffic Sources — Source / Medium", GRNDK, W), sp(8)]
        src_col = traffic_src.columns[0]
        top15   = traffic_src.sort_values('Sessions',ascending=False).head(15)
        c1 = hbar_chart(top15[src_col].str[:35].tolist(), top15['Sessions'].tolist(),
                        'Top 15 Sources by Sessions', colormap='Greens',
                        W=Wcm, H=max(8, len(top15)*0.7))
        story += [c1, sp(6)]
        sc = [['Source / Medium','Sessions','Eng. Rate','Avg Duration']]
        for _,r in top15.iterrows():
            sc.append([str(r.iloc[0])[:40], f"{int(r['Sessions']):,}",
                f"{r['Engagement rate']*100:.1f}%"     if 'Engagement rate'  in traffic_src.columns else '—',
                f"{r['Average engagement time per session']:.0f}s" if 'Average engagement time per session' in traffic_src.columns else '—'])
        story += [mktbl(sc,[6*cm,2*cm,2*cm,W-10*cm],GRNDK), sp(6)]
        story.append(Paragraph(
            "UTM Fix — Meta: ?utm_source=facebook&utm_medium=cpc  |  "
            "TikTok: ?utm_source=tiktok&utm_medium=cpc",
            PS('utmfix',8,False,AMBER,sp=8)))
        story.append(sp(8))

    # ── Top Pages ──
    if pages_df is not None:
        story += [banner("📄  Top Pages — Engagement Analysis", GRNDK, W), sp(8)]
        pg_col = pages_df.columns[0]
        total_views = int(pages_df['Views'].sum()) if 'Views' in pages_df.columns else 0
        story.append(Paragraph(
            f"Total page views: {total_views:,}  |  Unique pages tracked: {len(pages_df):,}",
            PS('pgsum',10,False,NAVY,sp=6)))

        top15_pg = pages_df.head(15)
        c1 = hbar_chart(top15_pg[pg_col].str[-35:].tolist(), top15_pg['Views'].tolist(),
                        'Top 15 Pages by Views', colormap='Greens',
                        W=Wcm, H=max(8, len(top15_pg)*0.7))
        story += [c1, sp(6)]

        if 'Average engagement time per active user' in pages_df.columns:
            top_eng = pages_df.nlargest(15,'Average engagement time per active user')
            c2 = hbar_chart(top_eng[pg_col].str[-35:].tolist(),
                            top_eng['Average engagement time per active user'].tolist(),
                            'Avg Engagement Time by Page (seconds)', colormap='Blues',
                            fmt='{:.0f}s', W=Wcm, H=max(8, len(top_eng)*0.7))
            story += [c2, sp(6)]

        pg_rows = [['Page','Views','Active Users','Avg Eng. Time','Events']]
        for _,r in top15_pg.iterrows():
            path = str(r.iloc[0]); path = path[:48]+'…' if len(path)>48 else path
            pg_rows.append([path, f"{int(r['Views']):,}",
                f"{int(r['Active users']):,}" if 'Active users' in pages_df.columns else '—',
                f"{r['Average engagement time per active user']:.0f}s" if 'Average engagement time per active user' in pages_df.columns else '—',
                f"{int(r['Event count']):,}" if 'Event count' in pages_df.columns else '—'])
        story += [mktbl(pg_rows,[6.5*cm,1.5*cm,2*cm,2.5*cm,W-12.5*cm],GRNDK), sp(12)]

    # ── Users ──
    if users_df is not None:
        story += [banner("👥  User Acquisition", GRNDK, W), sp(8)]
        total_u = int(users_df['Total users'].sum())    if 'Total users'    in users_df.columns else 0
        new_u   = int(users_df['New users'].sum())      if 'New users'      in users_df.columns else 0
        ret_u   = int(users_df['Returning users'].sum())if 'Returning users' in users_df.columns else 0
        story.append(kpi_row([
            ('Total Users',     f"{total_u:,}", '—',                  colors.HexColor('#6B7280')),
            ('New Users',       f"{new_u:,}",   f"{new_u/total_u*100:.0f}% of total" if total_u>0 else '—', BLUE),
            ('Returning Users', f"{ret_u:,}",   f"{ret_u/total_u*100:.0f}% returning" if total_u>0 else '—', TEAL),
        ], W))
        story.append(sp(8))
        usr_col = users_df.columns[0]
        if 'New users' in users_df.columns and 'Returning users' in users_df.columns:
            c1 = bar_chart(users_df[usr_col].tolist(), users_df['New users'].tolist(),
                           'New Users by Channel', color='#378ADD',
                           W=Wcm/2-1, H=6, rotate=15)
            c2 = bar_chart(users_df[usr_col].tolist(), users_df['Returning users'].tolist(),
                           'Returning Users by Channel', color='#1D9E75',
                           W=Wcm/2-1, H=6, rotate=15)
            story += [two_charts(c1, c2), sp(6)]
        u_rows = [['Channel','Total','New','Returning']]
        for _,r in users_df.iterrows():
            u_rows.append([str(r.iloc[0]),
                f"{int(r['Total users']):,}"    if 'Total users'    in users_df.columns else '—',
                f"{int(r['New users']):,}"       if 'New users'      in users_df.columns else '—',
                f"{int(r['Returning users']):,}" if 'Returning users' in users_df.columns else '—'])
        story += [mktbl(u_rows,[5*cm,3*cm,3*cm,W-11*cm],GRNDK), sp(12)]

    # ── Events ──
    if events_df is not None:
        story += [banner("⚡  Events Tracked", GRNDK, W), sp(8)]
        if len(events_df)<=4:
            story.append(Paragraph(
                "⚠ Only 4 basic events tracked. No WhatsApp clicks or purchase events yet. "
                "Set up: gtag('event','whatsapp_click') when WhatsApp button is clicked, "
                "then mark as Key Event in GA4.",
                PS('evw',9,False,AMBER,sp=6)))
        evt_col = events_df.columns[0]
        if 'Event count' in events_df.columns:
            c1 = pie_chart(events_df[evt_col].tolist(), events_df['Event count'].tolist(),
                           'Event Distribution', W=Wcm/2-1, H=7)
            c2 = bar_chart(events_df[evt_col].tolist(), events_df['Event count'].tolist(),
                           'Event Count', color='#3B6D11', W=Wcm/2-1, H=7)
            story += [two_charts(c1, c2), sp(6)]
        ev_rows = [['Event Name','Count','Total Users','Per User']]
        for _,r in events_df.iterrows():
            ev_rows.append([str(r.iloc[0]), f"{int(r['Event count']):,}",
                f"{int(r['Total users']):,}",
                f"{r['Event count per active user']:.2f}" if 'Event count per active user' in events_df.columns else '—'])
        story += [mktbl(ev_rows,[4*cm,3*cm,3*cm,W-10*cm],GRNDK), sp(12)]

    # ── SEO ──
    story += [banner("🔎  SEO Performance", GRNDK, W), sp(8)]
    if gsc_q is not None:
        total_gc = int(gsc_q['Clicks'].sum()) if 'Clicks' in gsc_q.columns else 0
        total_gi = int(gsc_q['Impressions'].sum()) if 'Impressions' in gsc_q.columns else 0
        avg_pos  = gsc_q['Position'].mean() if 'Position' in gsc_q.columns else 0
        story.append(kpi_row([
            ('Search Clicks',      f"{total_gc:,}",  '—', colors.HexColor('#6B7280')),
            ('Search Impressions', f"{total_gi:,}",  '—', colors.HexColor('#6B7280')),
            ('Avg Position',       f"{avg_pos:.1f}", '✅ Good' if avg_pos<10 else '⚠ Work needed',
             GREEN if avg_pos<10 else AMBER),
        ], W))
        story.append(sp(8))
        q_col = gsc_q.columns[0]
        if 'Clicks' in gsc_q.columns:
            top20 = gsc_q.sort_values('Clicks',ascending=False).head(20)
            c1 = hbar_chart(top20[q_col].str[:35].tolist(), top20['Clicks'].tolist(),
                            'Top 20 Queries by Clicks', colormap='Greens',
                            W=Wcm, H=max(8, len(top20)*0.7))
            story += [c1, sp(6)]
            gq_rows = [[q_col.title(),'Clicks','Impressions','CTR','Position']]
            for _,r in top20.iterrows():
                gq_rows.append([str(r.iloc[0])[:40],
                    f"{int(r['Clicks']):,}"      if 'Clicks'      in gsc_q.columns else '—',
                    f"{int(r['Impressions']):,}" if 'Impressions' in gsc_q.columns else '—',
                    f"{r['CTR']*100:.1f}%"       if 'CTR'         in gsc_q.columns else '—',
                    f"{r['Position']:.1f}"       if 'Position'    in gsc_q.columns else '—'])
            story += [mktbl(gq_rows,[5.5*cm,2*cm,2.5*cm,2*cm,W-12*cm],GRNDK), sp(12)]
    else:
        story.append(Paragraph(
            "Upload Google Search Console Queries CSV to see keyword performance and SEO data. "
            "Export from: Search Console → Performance → Export CSV.",
            PS('seon',10,False,AMBER,sp=8)))
        story.append(sp(8))

    story.append(footer_tbl(analyst, period, "Website", W))
    doc.build(story)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════════════════════
# COMBINED WEEKLY SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
def generate_pdf_report(meta_df, tiktok_df, ga4_df, analyst, period, recs, alerts, extra=None):
    buf = io.BytesIO()
    W   = A4[0] - 4*cm
    Wcm = W / cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    story = []
    story += [header_tbl("iDealz Weekly Marketing Report",
                          "Meta · TikTok · Website — Combined Summary",
                          period, analyst, W), sp(12)]

    if alerts:
        story += [banner("⚠  All Alerts", RED, W), sp(6)]
        al = [['#','Alert','Action']]
        for i,a in enumerate(alerts,1): al.append([str(i), a['title'], a['msg']])
        story += [mktbl(al,[0.5*cm,5.5*cm,W-6*cm],RED), sp(12)]

    if meta_df is not None:
        ts=meta_df['Amount spent (LKR)'].sum(); tr=int(meta_df['Results'].sum())
        cpr=ts/tr if tr>0 else 0; ctr=meta_df['CTR (link click-through rate)'].mean()
        story += [banner("📘  Meta Summary", BLUE, W), sp(8)]
        story.append(kpi_row([
            ('Spend',   f"Rs {ts:,.0f}", '—',                   colors.HexColor('#6B7280')),
            ('Results', str(tr),          '—',                   colors.HexColor('#6B7280')),
            ('CPR',     f"Rs {cpr:,.2f}", '⚠' if cpr>25 else '✅', RED if cpr>25 else GREEN),
            ('CTR',     f"{ctr:.2f}%",    '✅' if ctr>=1.5 else '⚠', GREEN if ctr>=1.5 else AMBER),
        ], W))
        story.append(sp(12))

    if tiktok_df is not None:
        aw=tiktok_df['Average play time per video view'].mean(); td=int(tiktok_df['Clicks (destination)'].sum())
        story += [banner("🎵  TikTok Summary", PINK, W), sp(8)]
        story.append(kpi_row([
            ('Spend',       f"${tiktok_df['Cost'].sum():,.2f}", '—', colors.HexColor('#6B7280')),
            ('Video Views', f"{int(tiktok_df['Video views'].sum()):,}", '—', colors.HexColor('#6B7280')),
            ('Watch Time',  f"{aw:.1f}s", '✅' if aw>=6 else '⚠', GREEN if aw>=6 else AMBER),
            ('Dest. Clicks',str(td), '❌ Critical' if td==0 else '✅', RED if td==0 else GREEN),
        ], W))
        story.append(sp(12))

    if ga4_df is not None:
        ts_w=int(ga4_df['Sessions'].sum()) if 'Sessions' in ga4_df.columns else 0
        er_w=ga4_df['Engagement rate'].mean()*100 if 'Engagement rate' in ga4_df.columns else 0
        story += [banner("🌐  Website Summary", GRNDK, W), sp(8)]
        story.append(kpi_row([
            ('Sessions',   f"{ts_w:,}",   '—',                colors.HexColor('#6B7280')),
            ('Eng. Rate',  f"{er_w:.1f}%",'✅' if er_w>50 else '⚠', GREEN if er_w>50 else AMBER),
            ('Paid Social','Not tracked', '❌ UTMs missing',  RED),
        ], W))
        story.append(sp(12))

    story += [banner("💡  Recommendations", AMBER, W), sp(8)]
    rc = [['#','Priority','Recommendation']]
    for i,r in enumerate(recs,1):
        if r.strip():
            p = '🔴 Urgent' if i<=2 else ('🟡 High' if i<=4 else '🟢 Normal')
            rc.append([str(i), p, r.strip()])
    story += [mktbl(rc,[0.5*cm,2.5*cm,W-3*cm],AMBER), sp(16)]
    story.append(footer_tbl(analyst, period, "Weekly Summary", W))
    doc.build(story)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════════════════════
# EXCEL REPORT
# ═════════════════════════════════════════════════════════════════════════════
def generate_excel_report(meta_df, tiktok_df, ga4_df, period, alerts, extra=None):
    buf = io.BytesIO()
    wb  = Workbook()
    wb.remove(wb.active)

    def hfill(hx): return PatternFill("solid", fgColor=hx.lstrip('#'))
    def tborder():
        s=Side(style='thin',color='FFD3D1C7')
        return Border(left=s,right=s,top=s,bottom=s)
    def write_df(ws, df, hcolor):
        for i,col in enumerate(df.columns,1):
            c=ws.cell(row=1,column=i,value=col)
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

    ws=wb.create_sheet("Summary")
    ws.column_dimensions['A'].width=28; ws.column_dimensions['B'].width=28
    ws.column_dimensions['C'].width=22; ws.column_dimensions['D'].width=18
    ws.merge_cells('A1:D1'); ws['A1']=f'iDealz Marketing Analytics — {period}'
    ws['A1'].font=Font(bold=True,size=14,color='FFFFFFFF',name='Arial')
    ws['A1'].fill=hfill('#1A1A2E'); ws['A1'].alignment=Alignment(horizontal='center',vertical='center')
    ws.row_dimensions[1].height=32

    r=3
    def add_sec(title, rows, color):
        nonlocal r
        ws.merge_cells(f'A{r}:D{r}'); ws[f'A{r}']=title
        ws[f'A{r}'].font=Font(bold=True,size=11,color='FFFFFFFF',name='Arial')
        ws[f'A{r}'].fill=hfill(color); ws[f'A{r}'].alignment=Alignment(horizontal='left',vertical='center')
        ws.row_dimensions[r].height=20; r+=1
        for row in rows:
            for ci,val in enumerate(row,1):
                c=ws.cell(row=r,column=ci,value=val)
                c.font=Font(size=10,name='Arial')
                c.fill=PatternFill("solid",fgColor='FFF9F9F9' if r%2 else 'FFFFFFFF')
                c.border=tborder()
            r+=1
        r+=1

    if meta_df is not None:
        ts=meta_df['Amount spent (LKR)'].sum(); tr=int(meta_df['Results'].sum())
        add_sec('META ADS SUMMARY',[
            ['Total Spend (LKR)',f"Rs {ts:,.0f}",'',''],
            ['Total Results',str(tr),'',''],
            ['Cost per Result',f"Rs {ts/tr:,.2f}" if tr>0 else '—','Benchmark: < Rs 25',''],
            ['Avg CTR',f"{meta_df['CTR (link click-through rate)'].mean():.2f}%",'Benchmark: 1.5%+',''],
            ['Avg Frequency',f"{meta_df['Frequency'].mean():.2f}",'Max: 3.0',''],
        ],'#378ADD')

    if tiktok_df is not None:
        td=int(tiktok_df['Clicks (destination)'].sum())
        add_sec('TIKTOK ADS SUMMARY',[
            ['Total Spend (USD)',f"${tiktok_df['Cost'].sum():,.2f}",'',''],
            ['Total Video Views',f"{int(tiktok_df['Video views'].sum()):,}",'',''],
            ['Avg Watch Time',f"{tiktok_df['Average play time per video view'].mean():.1f}s",'Benchmark: 6s+',''],
            ['Completion Rate',f"{tiktok_df['100% video view rate'].mean()*100:.1f}%",'Benchmark: 25%+',''],
            ['Destination Clicks',str(td),'Should be > 0','❌ Critical' if td==0 else '✅'],
        ],'#D4537E')

    if ga4_df is not None:
        nc=ga4_df.select_dtypes(include='number').columns.tolist()
        sc=next((c for c in nc if 'session' in c.lower() and 'engaged' not in c.lower()),nc[0] if nc else None)
        add_sec('WEBSITE (GA4) SUMMARY',[
            ['Total Sessions',f"{int(ga4_df[sc].sum()):,}" if sc else '—','',''],
            ['Paid Social','Not detected — UTMs missing','','❌'],
        ],'#3B6D11')

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

    if meta_df is not None:   write_df(wb.create_sheet("Meta_Raw"),         meta_df,   '#378ADD')
    if tiktok_df is not None: write_df(wb.create_sheet("TikTok_Raw"),       tiktok_df, '#D4537E')
    if ga4_df is not None:    write_df(wb.create_sheet("Website_Channel"),  ga4_df,    '#3B6D11')

    if extra:
        for key,sname,color in [('traffic_source','Website_Source','#3B6D11'),
                                  ('users','Website_Users','#3B6D11'),
                                  ('pages','Website_Pages','#27500A'),
                                  ('events','Website_Events','#27500A')]:
            df_ex=extra.get(key)
            if df_ex is not None: write_df(wb.create_sheet(sname),df_ex,color)

    wb.save(buf); buf.seek(0)
    return buf.read()
