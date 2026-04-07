import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── Colour palette ──
DARK_NAVY  = colors.HexColor('#1A1A2E')
BLUE       = colors.HexColor('#378ADD')
PINK       = colors.HexColor('#D4537E')
GREEN      = colors.HexColor('#639922')
AMBER      = colors.HexColor('#BA7517')
RED        = colors.HexColor('#E24B4A')
LIGHT_GREY = colors.HexColor('#F8F9FA')
MID_GREY   = colors.HexColor('#E9ECEF')
WHITE      = colors.white

def _styles():
    base = getSampleStyleSheet()
    return {
        'title':    ParagraphStyle('t',  fontSize=22, textColor=WHITE,     alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4),
        'subtitle': ParagraphStyle('s',  fontSize=11, textColor=colors.HexColor('#B4B2A9'), alignment=TA_CENTER, fontName='Helvetica', spaceAfter=2),
        'h2':       ParagraphStyle('h2', fontSize=14, textColor=DARK_NAVY,  fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6),
        'body':     ParagraphStyle('b',  fontSize=10, textColor=colors.HexColor('#2C2C2A'), fontName='Helvetica', spaceAfter=4, leading=15),
        'alert':    ParagraphStyle('al', fontSize=10, textColor=colors.HexColor('#742A2A'), fontName='Helvetica', spaceAfter=3, leftIndent=12),
        'rec':      ParagraphStyle('rc', fontSize=10, textColor=colors.HexColor('#1C4532'), fontName='Helvetica', spaceAfter=3, leftIndent=12),
        'small':    ParagraphStyle('sm', fontSize=8,  textColor=colors.HexColor('#6C757D'), fontName='Helvetica', spaceAfter=2),
    }

def _tbl_style(header_color=BLUE):
    return TableStyle([
        ('BACKGROUND',  (0,0), (-1,0),  header_color),
        ('TEXTCOLOR',   (0,0), (-1,0),  WHITE),
        ('FONTNAME',    (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,0),  9),
        ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
        ('ALIGN',       (0,1), (0,-1),  'LEFT'),
        ('FONTNAME',    (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',    (0,1), (-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE, LIGHT_GREY]),
        ('GRID',        (0,0), (-1,-1), 0.25, MID_GREY),
        ('TOPPADDING',  (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ])

def generate_pdf_report(meta_df, tiktok_df, ga4_df, analyst, period, recs, alerts, extra=None):
    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=1.5*cm, bottomMargin=2*cm)
    S    = _styles()
    W    = A4[0] - 4*cm
    story= []

    # ── Header banner ──
    story.append(Table(
        [[Paragraph("iDealz Marketing Analytics", S['title'])],
         [Paragraph("Weekly Performance Report", S['subtitle'])],
         [Paragraph(f"Period: {period}  |  Analyst: {analyst}  |  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}", S['subtitle'])]],
        colWidths=[W],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), DARK_NAVY),
            ('TOPPADDING',    (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('LEFTPADDING',   (0,0), (-1,-1), 16),
            ('ROUNDEDCORNERS', [8]),
        ])
    ))
    story.append(Spacer(1, 16))

    # ── Alerts ──
    if alerts:
        red_alerts = [a for a in alerts if a['level'] == 'red']
        if red_alerts:
            story.append(Paragraph("⚠ Alerts Requiring Action", S['h2']))
            rows = [['#','Alert','Detail']]
            for i, a in enumerate(red_alerts, 1):
                rows.append([str(i), a['title'], a['msg']])
            t = Table(rows, colWidths=[0.5*cm, 4*cm, W-4.5*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND',  (0,0), (-1,0),  RED),
                ('TEXTCOLOR',   (0,0), (-1,0),  WHITE),
                ('FONTNAME',    (0,0), (-1,0),  'Helvetica-Bold'),
                ('FONTSIZE',    (0,0), (-1,-1), 8),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#FFF5F5'), WHITE]),
                ('GRID',        (0,0), (-1,-1), 0.25, MID_GREY),
                ('TOPPADDING',  (0,0), (-1,-1), 5),
                ('BOTTOMPADDING',(0,0),(-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('TEXTCOLOR',   (0,1), (-1,-1), colors.HexColor('#742A2A')),
            ]))
            story.append(t)
            story.append(Spacer(1, 12))

    # ── META section ──
    if meta_df is not None:
        story.append(HRFlowable(width=W, color=BLUE, thickness=2))
        story.append(Paragraph("📘 Meta Ads Performance", S['h2']))

        total_spend   = meta_df['Amount spent (LKR)'].sum()
        total_results = int(meta_df['Results'].sum())
        avg_cpr       = total_spend / total_results if total_results > 0 else 0
        avg_ctr       = meta_df['CTR (link click-through rate)'].mean()
        avg_freq      = meta_df['Frequency'].mean()

        kpi = [
            ['Metric','Value','Benchmark','Status'],
            ['Total Spend',     f"Rs {total_spend:,.0f}", '—',         '—'],
            ['Total Results',   f"{total_results:,}",     '—',         '—'],
            ['Cost per Result', f"Rs {avg_cpr:,.2f}",     'Rs 25 max', '✅ Good' if avg_cpr < 25 else '⚠ High'],
            ['Avg CTR',         f"{avg_ctr:.2f}%",         '1.5%+',    '✅ Good' if avg_ctr >= 1.5 else '⚠ Low'],
            ['Avg Frequency',   f"{avg_freq:.2f}",         'Below 3',  '✅ OK'   if avg_freq < 3   else '⚠ Fatigued'],
        ]
        t = Table(kpi, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3*cm])
        t.setStyle(_tbl_style(BLUE))
        story.append(t)
        story.append(Spacer(1, 10))

        if 'Platform' in meta_df.columns:
            plat = meta_df.groupby('Platform').agg(
                Spend=('Amount spent (LKR)', 'sum'),
                Results=('Results', 'sum'),
                Avg_CTR=('CTR (link click-through rate)', 'mean'),
            ).round(2).reset_index()
            plat['Cost/Result'] = (plat['Spend'] / plat['Results'].replace(0,1)).round(2)
            rows = [['Platform','Spend (LKR)','Results','Avg CTR','Cost/Result']]
            for _, r in plat.iterrows():
                rows.append([r['Platform'], f"Rs {r['Spend']:,.0f}", str(int(r['Results'])),
                              f"{r['Avg_CTR']:.2f}%", f"Rs {r['Cost/Result']:,.2f}"])
            t = Table(rows, colWidths=[3*cm, 4*cm, 2.5*cm, 2.5*cm, 3.5*cm])
            t.setStyle(_tbl_style(BLUE))
            story.append(Paragraph("Platform Breakdown", S['body']))
            story.append(t)

        story.append(Spacer(1, 12))

    # ── TIKTOK section ──
    if tiktok_df is not None:
        story.append(HRFlowable(width=W, color=PINK, thickness=2))
        story.append(Paragraph("🎵 TikTok Ads Performance", S['h2']))

        total_spend  = tiktok_df['Cost'].sum()
        avg_watch    = tiktok_df['Average play time per video view'].mean()
        avg_comp     = tiktok_df['100% video view rate'].mean() * 100
        dest_clicks  = int(tiktok_df['Clicks (destination)'].sum())
        total_views  = int(tiktok_df['Video views'].sum())

        kpi = [
            ['Metric','Value','Benchmark','Status'],
            ['Total Spend',      f"${total_spend:,.2f} USD", '—',     '—'],
            ['Video Views',      f"{total_views:,}",         '—',     '—'],
            ['Avg Watch Time',   f"{avg_watch:.1f}s",        '6s+',   '✅ Good' if avg_watch >= 6 else '⚠ Low'],
            ['Completion Rate',  f"{avg_comp:.1f}%",         '25%+',  '⚠ Low'  if avg_comp < 15  else '✅ OK'],
            ['Dest. Clicks',     f"{dest_clicks}",           '>0',    '✅ OK'   if dest_clicks > 0 else '❌ Critical'],
        ]
        t = Table(kpi, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3*cm])
        t.setStyle(_tbl_style(PINK))
        story.append(t)
        story.append(Spacer(1, 10))

        camp = tiktok_df.groupby('Campaign name').agg(
            Spend=('Cost', 'sum'),
            Views=('Video views', 'sum'),
            Watch=('Average play time per video view', 'mean'),
            Comp=('100% video view rate', 'mean'),
        ).round(2).reset_index()
        rows = [['Campaign','Spend (USD)','Video Views','Avg Watch','Completion']]
        for _, r in camp.iterrows():
            rows.append([r['Campaign name'], f"${r['Spend']:,.2f}",
                         f"{int(r['Views']):,}", f"{r['Watch']:.1f}s", f"{r['Comp']*100:.1f}%"])
        t = Table(rows, colWidths=[5*cm, 3*cm, 3*cm, 2.5*cm, 2.5*cm])
        t.setStyle(_tbl_style(PINK))
        story.append(Paragraph("Campaign Breakdown", S['body']))
        story.append(t)
        story.append(Spacer(1, 12))

    # ── WEBSITE section ──
    if ga4_df is not None:
        story.append(HRFlowable(width=W, color=GREEN, thickness=2))
        story.append(Paragraph("🌐 Website (GA4) Performance", S['h2']))

        col0     = ga4_df.columns[0]
        num_cols = ga4_df.select_dtypes(include='number').columns.tolist()
        sess_col = next((c for c in num_cols if 'session' in c.lower() and 'engaged' not in c.lower()), num_cols[0] if num_cols else None)
        rate_col = next((c for c in num_cols if 'engagement' in c.lower() and 'rate' in c.lower()), None)
        dur_col  = next((c for c in num_cols if 'duration' in c.lower() or 'time' in c.lower()), None)

        total_sess = int(ga4_df[sess_col].sum()) if sess_col else 0
        avg_rate   = ga4_df[rate_col].mean() * 100 if rate_col else 0
        avg_dur    = ga4_df[dur_col].mean() if dur_col else 0

        kpi = [
            ['Metric','Value','Benchmark','Status'],
            ['Total Sessions',   f"{total_sess:,}",   '—',      '—'],
            ['Engagement Rate',  f"{avg_rate:.1f}%",  '50%+',   '✅ Good' if avg_rate >= 50 else '⚠ Low'],
            ['Avg Duration',     f"{avg_dur:.0f}s",   '45s+',   '✅ Good' if avg_dur >= 45   else '⚠ Low'],
            ['Paid Social',      'Not detected',       'Should show', '❌ UTMs missing'],
        ]
        t = Table(kpi, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3*cm])
        t.setStyle(_tbl_style(colors.HexColor('#3B6D11')))
        story.append(t)
        story.append(Spacer(1, 10))

        rows = [[col0] + num_cols[:4]]
        for _, row in ga4_df.iterrows():
            rows.append([str(row[col0])] + [str(round(row[c], 2)) for c in num_cols[:4]])
        col_w = [4*cm] + [(W - 4*cm) / min(4, len(num_cols))] * min(4, len(num_cols))
        t = Table(rows, colWidths=col_w)
        t.setStyle(_tbl_style(colors.HexColor('#3B6D11')))
        story.append(Paragraph("Traffic by Channel", S['body']))
        story.append(t)
        story.append(Spacer(1, 12))

    # ── Recommendations ──
    story.append(HRFlowable(width=W, color=AMBER, thickness=2))
    story.append(Paragraph("💡 Recommendations for Next Week", S['h2']))
    for i, r in enumerate(recs, 1):
        if r.strip():
            story.append(Paragraph(f"→  {r.strip()}", S['rec']))
    story.append(Spacer(1, 16))

    # ── Footer ──
    story.append(Table(
        [[Paragraph(f"iDealz Marketing Analytics  |  {analyst}  |  {datetime.now().strftime('%d %b %Y')}  |  Confidential", S['small'])]],
        colWidths=[W],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), DARK_NAVY),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ])
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


def generate_excel_report(meta_df, tiktok_df, ga4_df, period, alerts, extra=None):
    buf = io.BytesIO()
    wb  = Workbook()
    wb.remove(wb.active)

    def hdr_fill(hex_color):
        return PatternFill("solid", fgColor=hex_color.lstrip('#'))

    def thin_border():
        s = Side(style='thin', color='FFD3D1C7')
        return Border(left=s, right=s, top=s, bottom=s)

    def write_df(ws, df, header_hex):
        for i, col in enumerate(df.columns, 1):
            c = ws.cell(row=1, column=i, value=col)
            c.font      = Font(bold=True, color='FFFFFFFF', size=10, name='Arial')
            c.fill      = hdr_fill(header_hex)
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            c.border    = thin_border()
            ws.column_dimensions[get_column_letter(i)].width = max(14, len(str(col)) + 4)
        for ri, row in df.iterrows():
            for ci, val in enumerate(row, 1):
                c = ws.cell(row=ri+2, column=ci, value=val)
                c.font      = Font(size=10, name='Arial')
                c.alignment = Alignment(horizontal='left', vertical='center')
                c.border    = thin_border()
                c.fill      = PatternFill("solid", fgColor='FFFFFFFF' if ri % 2 == 0 else 'FFF9F9F9')
        ws.row_dimensions[1].height = 22

    # Summary sheet
    ws = wb.create_sheet("Summary")
    ws.column_dimensions['A'].width = 28
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 22
    ws.column_dimensions['D'].width = 18

    ws.merge_cells('A1:D1')
    ws['A1'] = f'iDealz Marketing Analytics — {period}'
    ws['A1'].font      = Font(bold=True, size=14, color='FFFFFFFF', name='Arial')
    ws['A1'].fill      = hdr_fill('#1A1A2E')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 32

    r = 3
    def add_section(title, rows, color):
        nonlocal r
        ws.merge_cells(f'A{r}:D{r}')
        ws[f'A{r}'] = title
        ws[f'A{r}'].font = Font(bold=True, size=11, color='FFFFFFFF', name='Arial')
        ws[f'A{r}'].fill = hdr_fill(color)
        ws[f'A{r}'].alignment = Alignment(horizontal='left', vertical='center')
        ws.row_dimensions[r].height = 20
        r += 1
        for row in rows:
            for ci, val in enumerate(row, 1):
                c = ws.cell(row=r, column=ci, value=val)
                c.font   = Font(size=10, name='Arial')
                c.fill   = PatternFill("solid", fgColor='FFF9F9F9' if r % 2 else 'FFFFFFFF')
                c.border = thin_border()
            r += 1
        r += 1

    if meta_df is not None:
        ts = meta_df['Amount spent (LKR)'].sum()
        tr = int(meta_df['Results'].sum())
        cpr = ts/tr if tr > 0 else 0
        add_section('META ADS SUMMARY', [
            ['Total Spend (LKR)', f"Rs {ts:,.0f}", '', ''],
            ['Total Results',     str(tr), '', ''],
            ['Cost per Result',   f"Rs {cpr:,.2f}", 'Benchmark: Rs 25', '✅' if cpr < 25 else '⚠'],
            ['Avg CTR',           f"{meta_df['CTR (link click-through rate)'].mean():.2f}%", 'Benchmark: 1.5%+', ''],
            ['Avg Frequency',     f"{meta_df['Frequency'].mean():.2f}", 'Max: 3.0', '⚠' if meta_df['Frequency'].mean() > 3 else '✅'],
        ], '#378ADD')

    if tiktok_df is not None:
        add_section('TIKTOK ADS SUMMARY', [
            ['Total Spend (USD)',    f"${tiktok_df['Cost'].sum():,.2f}", '', ''],
            ['Total Video Views',   f"{int(tiktok_df['Video views'].sum()):,}", '', ''],
            ['Avg Watch Time',      f"{tiktok_df['Average play time per video view'].mean():.1f}s", 'Benchmark: 6s+', ''],
            ['Completion Rate',     f"{tiktok_df['100% video view rate'].mean()*100:.1f}%", 'Benchmark: 25%+', ''],
            ['Destination Clicks',  str(int(tiktok_df['Clicks (destination)'].sum())), 'Should be > 0', '❌ Critical' if tiktok_df['Clicks (destination)'].sum() == 0 else '✅'],
        ], '#D4537E')

    if ga4_df is not None:
        num_cols = ga4_df.select_dtypes(include='number').columns.tolist()
        sess_col = next((c for c in num_cols if 'session' in c.lower() and 'engaged' not in c.lower()), num_cols[0] if num_cols else None)
        add_section('WEBSITE (GA4) SUMMARY', [
            ['Total Sessions', f"{int(ga4_df[sess_col].sum()):,}" if sess_col else 'N/A', '', ''],
            ['Paid Social traffic', 'Not detected — UTMs missing', '', '❌'],
        ], '#3B6D11')

    # Alerts sheet
    if alerts:
        wa = wb.create_sheet("Alerts")
        wa.column_dimensions['A'].width = 8
        wa.column_dimensions['B'].width = 30
        wa.column_dimensions['C'].width = 60
        for ci, h in enumerate(['Level','Alert','Detail'], 1):
            c = wa.cell(row=1, column=ci, value=h)
            c.font = Font(bold=True, color='FFFFFFFF', size=10, name='Arial')
            c.fill = hdr_fill('#E24B4A')
            c.border = thin_border()
        for ri, a in enumerate(alerts, 2):
            wa.cell(row=ri, column=1, value=a['level'].upper()).border = thin_border()
            wa.cell(row=ri, column=2, value=a['title']).border = thin_border()
            wa.cell(row=ri, column=3, value=a['msg']).border = thin_border()

    # Raw data sheets
    if meta_df is not None:
        wm = wb.create_sheet("Meta_Raw")
        write_df(wm, meta_df, '#378ADD')
    if tiktok_df is not None:
        wt = wb.create_sheet("TikTok_Raw")
        write_df(wt, tiktok_df, '#D4537E')
    if ga4_df is not None:
        wg = wb.create_sheet("Website_Channel")
        write_df(wg, ga4_df, '#3B6D11')
    if extra:
        for key, sname, color in [
            ('traffic_source','Website_Source','#3B6D11'),
            ('users','Website_Users','#3B6D11'),
            ('pages','Website_Pages','#27500A'),
            ('events','Website_Events','#27500A'),
        ]:
            df_ex = extra.get(key)
            if df_ex is not None:
                ws_ex = wb.create_sheet(sname)
                write_df(ws_ex, df_ex, color)
    wb.save(buf)
    buf.seek(0)
    return buf.read()
