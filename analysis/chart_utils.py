"""
chart_utils.py
Renders charts as ReportLab Image objects using matplotlib.
No kaleido needed. Drop this into analysis/ folder.
"""
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from reportlab.platypus import Image
from reportlab.lib.units import cm

# iDealz colour palette
C = {
    'blue':   '#378ADD', 'pink':  '#D4537E', 'green': '#639922',
    'teal':   '#1D9E75', 'amber': '#BA7517', 'red':   '#E24B4A',
    'navy':   '#1A1A2E', 'grey':  '#E9ECEF', 'lgrey': '#F8F9FA',
    'grndk':  '#3B6D11', 'white': '#FFFFFF',
}

def _save(fig, width_cm, height_cm):
    """Save matplotlib figure to a ReportLab Image."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width_cm*cm, height=height_cm*cm)

def _style(ax, title, xlabel='', ylabel='', grid_axis='x'):
    ax.set_title(title, fontsize=9, fontweight='bold', pad=8, color=C['navy'])
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(labelsize=7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#DEE2E6')
    ax.spines['bottom'].set_color('#DEE2E6')
    if grid_axis:
        ax.grid(axis=grid_axis, linestyle='--', linewidth=0.4, alpha=0.6)
    ax.set_facecolor('#FAFAFA')

# ── Generic bar chart (vertical) ────────────────────────────────────────────
def bar_chart(labels, values, title, color=C['blue'],
              xlabel='', ylabel='', W=15, H=6, fmt=None, rotate=0):
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    bars = ax.bar(range(len(labels)), values, color=color, width=0.6, zorder=3)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([str(l)[:20] for l in labels], rotation=rotate,
                       ha='right' if rotate else 'center', fontsize=7)
    for bar, val in zip(bars, values):
        if val > 0:
            label = fmt.format(val) if fmt else f'{val:,.0f}'
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(values)*0.01,
                    label, ha='center', va='bottom', fontsize=6.5, color=C['navy'])
    _style(ax, title, xlabel, ylabel, 'y')
    fig.tight_layout()
    return _save(fig, W, H)

# ── Horizontal bar chart ─────────────────────────────────────────────────────
def hbar_chart(labels, values, title, color=C['blue'],
               W=15, H=7, fmt=None, colormap=None):
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    y_pos = range(len(labels))
    if colormap and len(values) > 0:
        norm = plt.Normalize(min(values), max(values)+0.001)
        cmap = plt.get_cmap(colormap)
        bar_colors = [cmap(norm(v)) for v in values]
    else:
        bar_colors = color
    bars = ax.barh(list(y_pos), values, color=bar_colors, height=0.6, zorder=3)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([str(l)[:40] for l in labels], fontsize=7)
    for bar, val in zip(bars, values):
        if val > 0:
            label = fmt.format(val) if fmt else f'{val:,.0f}'
            ax.text(bar.get_width()+max(values)*0.01, bar.get_y()+bar.get_height()/2,
                    label, va='center', fontsize=6.5, color=C['navy'])
    _style(ax, title, grid_axis='x')
    ax.invert_yaxis()
    fig.tight_layout()
    return _save(fig, W, H)

# ── Grouped bar chart ────────────────────────────────────────────────────────
def grouped_bar(labels, series_dict, title, W=15, H=6, rotate=0):
    """series_dict = {'Series1': [v1,v2,...], 'Series2': [v1,v2,...]}"""
    colors = [C['blue'], C['pink'], C['teal'], C['amber'], C['green']]
    n      = len(labels)
    n_ser  = len(series_dict)
    width  = 0.7 / n_ser
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    for i, (name, vals) in enumerate(series_dict.items()):
        offsets = [j + (i - n_ser/2 + 0.5) * width for j in range(n)]
        ax.bar(offsets, vals, width=width*0.9, label=name,
               color=colors[i % len(colors)], zorder=3)
    ax.set_xticks(range(n))
    ax.set_xticklabels([str(l)[:18] for l in labels],
                       rotation=rotate, ha='right' if rotate else 'center', fontsize=7)
    ax.legend(fontsize=7, framealpha=0.5)
    _style(ax, title, grid_axis='y')
    fig.tight_layout()
    return _save(fig, W, H)

# ── Pie chart ─────────────────────────────────────────────────────────────────
def pie_chart(labels, values, title, W=10, H=7):
    colors = [C['blue'], C['pink'], C['teal'], C['amber'],
              C['green'], C['red'], C['grndk']]
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct='%1.1f%%',
        colors=colors[:len(values)], startangle=90,
        pctdistance=0.75, wedgeprops={'linewidth':0.5,'edgecolor':'white'})
    for at in autotexts: at.set_fontsize(7)
    ax.legend(wedges, [str(l)[:22] for l in labels],
              loc='lower center', bbox_to_anchor=(0.5,-0.12),
              ncol=2, fontsize=7, framealpha=0.5)
    ax.set_title(title, fontsize=9, fontweight='bold', color=C['navy'])
    fig.tight_layout()
    return _save(fig, W, H)

# ── Scatter chart ─────────────────────────────────────────────────────────────
def scatter_chart(x, y, labels, title, hline=None, hline_label='',
                  colors_list=None, sizes=None, W=15, H=7,
                  xlabel='', ylabel=''):
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    default_c = colors_list or [C['blue']]*len(x)
    sz = [max(30, s*3) for s in sizes] if sizes else 60
    ax.scatter(x, y, c=default_c, s=sz, alpha=0.7, zorder=3)
    if hline is not None:
        ax.axhline(y=hline, linestyle='--', color=C['amber'],
                   linewidth=1, label=hline_label)
        ax.legend(fontsize=7)
    _style(ax, title, xlabel, ylabel, 'both')
    fig.tight_layout()
    return _save(fig, W, H)

# ── Funnel chart ─────────────────────────────────────────────────────────────
def funnel_chart(stages, values, title, color=C['pink'], W=14, H=8):
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    max_v = max(values) if max(values) > 0 else 1
    bar_h = 0.6
    for i, (stage, val) in enumerate(zip(stages, values)):
        width = val / max_v
        left  = (1 - width) / 2
        alpha = 0.9 - i * 0.1
        ax.barh(i, width, left=left, height=bar_h,
                color=color, alpha=max(0.3, alpha), zorder=3)
        pct = f"{val/values[0]*100:.1f}%" if values[0]>0 else '0%'
        ax.text(0.5, i, f"{stage}: {val:,}  ({pct})",
                ha='center', va='center', fontsize=7.5,
                color='white', fontweight='bold')
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines[:].set_visible(False)
    ax.set_title(title, fontsize=9, fontweight='bold', color=C['navy'], pad=10)
    ax.set_facecolor('#FAFAFA')
    fig.tight_layout()
    return _save(fig, W, H)

# ── Colour bar (gradient colour by value) ────────────────────────────────────
def color_bar(labels, values, title, cmap_name='RdYlGn', W=15, H=6,
              fmt=None, rotate=0, low_good=False):
    """Bar chart where bar colour encodes value magnitude."""
    norm_vals = np.array(values, dtype=float)
    if len(norm_vals) > 0 and norm_vals.max() > norm_vals.min():
        normed = (norm_vals - norm_vals.min()) / (norm_vals.max() - norm_vals.min())
    else:
        normed = np.ones_like(norm_vals) * 0.5
    if low_good:
        normed = 1 - normed
    cmap   = plt.get_cmap(cmap_name)
    bar_colors = [cmap(n) for n in normed]

    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    bars = ax.bar(range(len(labels)), norm_vals, color=bar_colors, width=0.6, zorder=3)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([str(l)[:18] for l in labels],
                       rotation=rotate, ha='right' if rotate else 'center', fontsize=7)
    for bar, val in zip(bars, norm_vals):
        if val >= 0:
            label = fmt.format(val) if fmt else f'{val:,.1f}'
            ax.text(bar.get_x()+bar.get_width()/2,
                    bar.get_height()+norm_vals.max()*0.01,
                    label, ha='center', va='bottom', fontsize=6.5, color=C['navy'])
    _style(ax, title, grid_axis='y')
    fig.tight_layout()
    return _save(fig, W, H)
