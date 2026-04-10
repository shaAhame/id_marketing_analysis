import io
import os
os.environ.setdefault('MPLBACKEND', 'Agg')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.platypus import Image
from reportlab.lib.units import cm

C = {
    'blue':'#378ADD','pink':'#D4537E','green':'#639922',
    'teal':'#1D9E75','amber':'#BA7517','red':'#E24B4A',
    'navy':'#1A1A2E','grey':'#E9ECEF','lgrey':'#F8F9FA',
    'grndk':'#3B6D11','white':'#FFFFFF',
}

def _save(fig, W_cm, H_cm):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=W_cm*cm, height=H_cm*cm)

def _style(ax, title, xlabel='', ylabel='', grid_axis='y'):
    ax.set_title(title, fontsize=10, fontweight='bold', pad=10, color=C['navy'])
    if xlabel: ax.set_xlabel(xlabel, fontsize=8)
    if ylabel: ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#DEE2E6')
    ax.spines['bottom'].set_color('#DEE2E6')
    if grid_axis: ax.grid(axis=grid_axis, linestyle='--', linewidth=0.4, alpha=0.5, zorder=0)
    ax.set_facecolor('#FAFAFA')

def _shorten(labels, maxlen=18):
    return [str(l)[:maxlen]+'…' if len(str(l))>maxlen else str(l) for l in labels]

def bar_chart(labels, values, title, color=C['blue'],
              xlabel='', ylabel='', W=8, H=6, fmt=None, rotate=0):
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    short = _shorten(labels, 16)
    bars  = ax.bar(range(len(short)), values, color=color, width=0.55, zorder=3)
    ax.set_xticks(range(len(short)))
    ax.set_xticklabels(short, rotation=rotate, ha='right' if rotate else 'center', fontsize=7)
    maxv  = max(values) if values else 1
    for bar, val in zip(bars, values):
        if val > 0:
            lbl = fmt.format(val) if fmt else f'{val:,.1f}'
            ax.text(bar.get_x()+bar.get_width()/2,
                    bar.get_height()+maxv*0.02,
                    lbl, ha='center', va='bottom', fontsize=7, color=C['navy'])
    ax.set_ylim(0, maxv*1.18)
    _style(ax, title, xlabel, ylabel)
    fig.tight_layout(pad=1.0)
    return _save(fig, W, H)

def hbar_chart(labels, values, title, color=C['blue'],
               W=14, H=8, fmt=None, colormap=None):
    n   = len(labels)
    fig, ax = plt.subplots(figsize=(W/2.54, max(H, n*0.55)/2.54))
    short = _shorten(labels, 40)
    if colormap and values:
        norm  = plt.Normalize(min(values), max(values)+0.001)
        cmap  = plt.get_cmap(colormap)
        bcolors = [cmap(norm(v)) for v in values]
    else:
        bcolors = color
    bars = ax.barh(range(n), values, color=bcolors, height=0.55, zorder=3)
    ax.set_yticks(range(n))
    ax.set_yticklabels(short, fontsize=7)
    ax.invert_yaxis()
    maxv = max(values) if values else 1
    for bar, val in zip(bars, values):
        if val > 0:
            lbl = fmt.format(val) if fmt else f'{val:,.0f}'
            ax.text(bar.get_width()+maxv*0.01,
                    bar.get_y()+bar.get_height()/2,
                    lbl, va='center', fontsize=7, color=C['navy'])
    ax.set_xlim(0, maxv*1.15)
    _style(ax, title, grid_axis='x')
    fig.tight_layout(pad=1.0)
    return _save(fig, W, max(H, n*0.55))

def grouped_bar(labels, series_dict, title, W=14, H=6, rotate=30):
    colors = [C['blue'],C['pink'],C['teal'],C['amber'],C['green']]
    n      = len(labels)
    n_ser  = len(series_dict)
    width  = 0.65 / n_ser
    short  = _shorten(labels, 15)
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    for i,(name,vals) in enumerate(series_dict.items()):
        offsets = [j+(i-n_ser/2+0.5)*width for j in range(n)]
        ax.bar(offsets, vals, width=width*0.88, label=name,
               color=colors[i%len(colors)], zorder=3)
    ax.set_xticks(range(n))
    ax.set_xticklabels(short, rotation=rotate,
                       ha='right' if rotate else 'center', fontsize=7)
    ax.legend(fontsize=8, framealpha=0.6, loc='upper right')
    _style(ax, title)
    fig.tight_layout(pad=1.0)
    return _save(fig, W, H)

def pie_chart(labels, values, title, W=8, H=7):
    colors = [C['blue'],C['pink'],C['teal'],C['amber'],
              C['green'],C['red'],C['grndk']]
    short  = _shorten(labels, 22)
    # Filter zero values
    filtered = [(l,v,c) for l,v,c in zip(short,values,colors[:len(values)]) if v>0]
    if not filtered: filtered = list(zip(short,values,colors[:len(values)]))
    fl, fv, fc = zip(*filtered) if filtered else (short,values,colors[:len(values)])

    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    # Only show % label if slice > 5% to avoid overlap
    def autopct_fn(pct):
        return f'{pct:.1f}%' if pct > 5 else ''

    wedges, texts, autotexts = ax.pie(
        fv, labels=None,
        autopct=autopct_fn,
        colors=list(fc), startangle=140,
        pctdistance=0.82,
        wedgeprops={'linewidth':1.0,'edgecolor':'white'})
    for at in autotexts:
        at.set_fontsize(7.5)
        at.set_fontweight('bold')
    # Legend below chart with enough space
    ax.legend(wedges, fl,
              loc='upper center',
              bbox_to_anchor=(0.5, -0.08),
              ncol=min(3, len(fl)),
              fontsize=7, framealpha=0.5,
              handlelength=1.2, handleheight=0.8)
    ax.set_title(title, fontsize=10, fontweight='bold', color=C['navy'], pad=10)
    fig.tight_layout(pad=1.5)
    return _save(fig, W, H)

def scatter_chart(x, y, labels, title, hline=None, hline_label='',
                  colors_list=None, sizes=None, W=14, H=7,
                  xlabel='', ylabel=''):
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    dc = colors_list or [C['blue']]*len(x)
    sz = [max(40, s*4) for s in sizes] if sizes else 80
    ax.scatter(x, y, c=dc, s=sz, alpha=0.75, zorder=3, edgecolors='white', linewidth=0.5)
    if hline is not None:
        ax.axhline(y=hline, linestyle='--', color=C['amber'],
                   linewidth=1.2, label=hline_label, zorder=2)
        ax.legend(fontsize=8, framealpha=0.6)
    _style(ax, title, xlabel, ylabel, 'both')
    fig.tight_layout(pad=1.0)
    return _save(fig, W, H)

def funnel_chart(stages, values, title, color=C['pink'], W=14, H=9):
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    maxv = max(values) if max(values) > 0 else 1
    n    = len(stages)
    # Threshold: if bar is narrower than this, put text outside
    MIN_WIDTH_FOR_INSIDE = 0.25

    for i, (stage, val) in enumerate(zip(stages, values)):
        width = val / maxv
        left  = (1 - width) / 2
        alpha = max(0.35, 1.0 - i * 0.12)
        ax.barh(n-1-i, width, left=left, height=0.70,
                color=color, alpha=alpha, zorder=3,
                edgecolor='white', linewidth=0.8)
        pct  = f"{val/values[0]*100:.1f}%" if values[0] > 0 else "0%"
        text = f"{stage}: {val:,}  ({pct})"
        if width >= MIN_WIDTH_FOR_INSIDE:
            # Text inside bar — white
            ax.text(0.5, n-1-i, text,
                    ha='center', va='center',
                    fontsize=8, color='white', fontweight='bold',
                    zorder=4)
        else:
            # Bar too small — put text to the RIGHT of bar, dark colour
            ax.text(left + width + 0.02, n-1-i, text,
                    ha='left', va='center',
                    fontsize=8, color=C['navy'], fontweight='bold',
                    zorder=4)
            # Small coloured marker so bar is still visible
            ax.barh(n-1-i, max(width, 0.015), left=left, height=0.70,
                    color=color, alpha=0.9, zorder=5,
                    edgecolor='white', linewidth=0.8)

    ax.set_xlim(0, 1.05)
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_yticks([])
    ax.set_xticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(title, fontsize=10, fontweight='bold',
                 color=C['navy'], pad=10)
    ax.set_facecolor('#FAFAFA')
    fig.tight_layout(pad=1.2)
    return _save(fig, W, H)

def color_bar(labels, values, title, cmap_name='RdYlGn', W=14, H=6,
              fmt=None, rotate=0, low_good=False):
    """Auto-switches to horizontal bar when > 10 items to prevent label overlap."""
    vals  = np.array(values, dtype=float)
    n     = len(vals)
    if len(vals)>0 and vals.max()>vals.min():
        normed = (vals-vals.min())/(vals.max()-vals.min())
    else:
        normed = np.ones_like(vals)*0.5
    if low_good: normed = 1-normed
    cmap    = plt.get_cmap(cmap_name)
    bcolors = [cmap(nv) for nv in normed]
    maxv    = vals.max() if len(vals)>0 else 1

    # Auto horizontal for many items
    if n > 10:
        short  = _shorten(labels, 30)
        h_auto = max(H, n * 0.55)
        fig, ax = plt.subplots(figsize=(W/2.54, h_auto/2.54))
        bars = ax.barh(range(n), vals, color=bcolors, height=0.62, zorder=3)
        ax.set_yticks(range(n))
        ax.set_yticklabels(short, fontsize=7)
        ax.invert_yaxis()
        ax.set_xlim(0, maxv*1.18)
        for bar, val in zip(bars, vals):
            lbl = fmt.format(val) if fmt else f'{val:,.1f}'
            ax.text(bar.get_width()+maxv*0.01,
                    bar.get_y()+bar.get_height()/2,
                    lbl, va='center', fontsize=7, color=C['navy'])
        _style(ax, title, grid_axis='x')
        fig.tight_layout(pad=1.0)
        return _save(fig, W, h_auto)
    else:
        short  = _shorten(labels, 16)
        fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
        bars = ax.bar(range(n), vals, color=bcolors, width=0.55, zorder=3)
        ax.set_xticks(range(n))
        ax.set_xticklabels(short, rotation=rotate,
                           ha='right' if rotate else 'center', fontsize=7)
        for bar, val in zip(bars, vals):
            lbl = fmt.format(val) if fmt else f'{val:,.1f}'
            ax.text(bar.get_x()+bar.get_width()/2,
                    bar.get_height()+maxv*0.02,
                    lbl, ha='center', va='bottom', fontsize=7, color=C['navy'])
        ax.set_ylim(0, maxv*1.18)
        _style(ax, title)
        fig.tight_layout(pad=1.0)
        return _save(fig, W, H)

def hist_chart(values, title, color=C['blue'], vline=None,
               vline_label='', xlabel='', ylabel='Count',
               W=10, H=5, bins=20):
    fig, ax = plt.subplots(figsize=(W/2.54, H/2.54))
    ax.hist(values, bins=bins, color=color, edgecolor='white',
            alpha=0.85, zorder=3)
    if vline is not None:
        ax.axvline(x=vline, color=C['red'], linestyle='--',
                   linewidth=1.2, label=vline_label, zorder=4)
        ax.legend(fontsize=8, framealpha=0.6)
    _style(ax, title, xlabel, ylabel)
    fig.tight_layout(pad=1.0)
    return _save(fig, W, H)
