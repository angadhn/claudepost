"""
Three views of imperial rise and fall, in light and dark themes.

empires_cascade[_dark].png   - territorial extent ridgeline, 550 BCE -> today, shared scale
modern_power[_dark].png      - share of world GDP (PPP), 1500 -> 2026
empire_lifecycles[_dark].png - % of peak extent vs years since founding
empires_data.js              - data export for the interactive HTML version

Territorial data: approximations after Rein Taagepera, "Size and Duration of
Empires" (1978, 1979, 1997), million km^2. GDP shares: Angus Maddison project
estimates + IMF WEO (PPP) for recent years. All values approximate.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

OUT = os.path.dirname(os.path.abspath(__file__))

THEMES = {
    "light": dict(suffix="", bg="#faf9f5", fg="#33312c", grey="#8a857c",
                  grid="#e7e4dc", baseline="#cfccc4", mix=0.0),
    "dark":  dict(suffix="_dark", bg="#262624", fg="#e8e5de", grey="#a09a8e",
                  grid="#3a3833", baseline="#4d4a44", mix=0.38),
}

def lighten(hex_color, t):
    """Blend a hex colour toward white by t (0..1)."""
    if t <= 0:
        return hex_color
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    f = lambda v: int(round(v + (255 - v) * t))
    return f"#{f(r):02x}{f(g):02x}{f(b):02x}"

# ---------------------------------------------------------------- data
# (name, still-extant, family colour, [(year, extent Mkm^2)...])
EMPIRES = [
    ("Achaemenid Persia", False, "#5e7d4f", [(-550,0.5),(-539,2.0),(-525,3.5),(-500,5.5),(-480,5.5),
        (-450,5.0),(-400,4.6),(-350,4.5),(-334,4.0),(-330,0)]),
    ("Maurya (India)", False, "#b3873e", [(-322,0.5),(-300,3.5),(-260,5.0),(-230,4.0),(-200,1.5),(-185,0)]),
    ("Rome", False, "#54678a", [(-326,0.05),(-264,0.15),(-218,0.3),(-200,0.6),(-146,0.8),(-100,1.2),
        (-60,1.95),(-30,2.75),(14,3.5),(50,4.2),(117,5.0),(200,4.6),(300,4.4),(390,4.4),
        (420,3.0),(450,1.7),(476,0)]),
    ("Han China", False, "#9c453a", [(-206,1.5),(-180,3.0),(-120,4.5),(-100,6.0),(-50,6.0),(1,6.1),
        (50,5.8),(100,6.5),(150,6.0),(190,3.0),(220,0)]),
    ("Sasanian Persia", False, "#5e7d4f", [(224,2.8),(260,3.0),(400,3.3),(530,3.5),(580,3.3),
        (620,3.5),(636,2.5),(651,0)]),
    ("Byzantium", False, "#54678a", [(395,2.0),(450,1.6),(527,1.7),(555,2.7),(600,2.2),(640,1.5),
        (700,0.9),(750,0.75),(850,0.8),(950,1.0),(1025,1.35),(1080,0.6),(1143,0.65),
        (1180,0.7),(1204,0.25),(1261,0.35),(1350,0.1),(1453,0)]),
    ("Tang China", False, "#9c453a", [(618,3.0),(630,4.0),(660,5.0),(669,5.4),(715,5.4),(755,4.6),
        (763,3.8),(800,3.6),(860,3.3),(880,1.5),(907,0)]),
    ("Arab Caliphates", False, "#3e7d78", [(632,0.2),(642,3.0),(661,5.5),(690,7.5),(720,9.8),
        (750,11.1),(800,10.0),(861,7.5),(900,4.5),(945,1.5),(1000,0.8),(1055,0)]),
    ("Mongol Empire", False, "#6e5340", [(1206,1.0),(1218,3.5),(1227,13.5),(1241,16.5),(1259,19.0),
        (1279,23.0),(1294,23.5),(1310,24.0),(1330,21.0),(1350,14.0),(1368,4.0),(1380,0)]),
    ("Ottoman Empire", False, "#7b5e75", [(1299,0.05),(1360,0.4),(1389,0.7),(1451,0.9),(1453,1.0),
        (1481,1.2),(1520,2.2),(1566,4.3),(1620,4.8),(1683,5.2),(1739,4.6),(1800,4.0),
        (1830,3.4),(1878,2.9),(1900,2.6),(1914,1.8),(1918,1.0),(1922,0)]),
    ("Ming China", False, "#9c453a", [(1368,3.5),(1390,5.0),(1415,6.5),(1450,5.8),(1500,5.2),
        (1550,4.8),(1600,4.7),(1630,4.0),(1644,0)]),
    ("Spanish Empire", False, "#8a7d3a", [(1492,0.05),(1520,0.8),(1550,3.0),(1580,6.0),(1600,7.5),
        (1650,9.0),(1700,10.0),(1750,12.0),(1790,13.7),(1810,13.0),(1821,8.0),(1825,3.0),
        (1860,1.2),(1898,0.4),(1900,0)]),
    ("Mughal (India)", False, "#b3873e", [(1526,0.8),(1556,1.2),(1605,3.2),(1658,3.6),(1690,4.0),
        (1707,4.0),(1739,2.8),(1760,1.6),(1790,0.7),(1803,0.3),(1857,0)]),
    ("Russia – USSR – Russia", True, "#7d4f63", [(1547,2.8),(1600,5.0),(1650,10.0),(1700,14.5),
        (1750,15.5),(1800,16.5),(1850,20.0),(1866,22.8),(1895,22.8),(1905,22.4),
        (1917,20.0),(1922,21.7),(1945,22.4),(1991,22.4),(1992,17.1),(2026,17.1)]),
    ("British Empire", False, "#2e5e8a", [(1583,0.01),(1650,0.4),(1700,0.9),(1763,3.0),(1783,2.3),
        (1800,4.5),(1815,6.5),(1837,9.0),(1860,15.0),(1880,25.0),(1900,30.0),(1920,35.5),
        (1936,34.5),(1945,33.0),(1947,21.0),(1957,15.0),(1960,10.0),(1965,3.0),
        (1980,0.7),(1997,0.05),(2000,0)]),
    ("French Empire", False, "#6f8fae", [(1605,0.02),(1663,0.3),(1680,2.0),(1754,3.0),(1763,0.6),
        (1812,2.1),(1815,0.6),(1830,0.7),(1860,1.2),(1880,3.5),(1900,9.0),(1920,11.5),
        (1939,11.0),(1945,10.5),(1954,9.5),(1960,8.0),(1962,0.5),(1980,0)]),
    ("Qing China", False, "#9c453a", [(1644,5.5),(1660,7.0),(1700,9.0),(1720,11.0),(1760,13.1),
        (1790,14.7),(1820,14.0),(1860,13.0),(1880,11.5),(1900,11.0),(1912,0)]),
    ("United States", True, "#2e6b4f", [(1776,0.9),(1783,2.3),(1803,4.6),(1845,5.5),(1848,7.7),
        (1853,7.8),(1867,9.3),(1898,9.7),(1912,9.8),(2026,9.8)]),
    ("India (Republic)", True, "#b3873e", [(1947,3.2),(1961,3.29),(2026,3.29)]),
    ("China (PRC)", True, "#9c453a", [(1949,9.3),(1951,9.6),(2026,9.6)]),
]

def year_fmt(y, _pos=None):
    if y < 0:
        return f"{int(-y)} BCE"
    if y == 1:
        return "1 CE"
    return f"{int(y)}"

# ---------------------------------------------------------------- fig 1: cascade
def fig_cascade(th):
    spacing = 8.0  # million km^2 between baselines -> shared scale across rows
    n = len(EMPIRES)
    fig, ax = plt.subplots(figsize=(13.5, 21))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])

    for gx in (-500, 1, 500, 1000, 1500, 2000):
        ax.axvline(gx, color=th["grid"], lw=0.8, zorder=0)

    for i, (name, extant, col, pts) in enumerate(EMPIRES):
        col = lighten(col, th["mix"])
        base = (n - 1 - i) * spacing
        xs = np.array([p[0] for p in pts], float)
        ys = np.array([p[1] for p in pts], float)
        z = 2 + i  # later empires drawn in front (joyplot occlusion)
        ax.fill_between(xs, base, base + ys, color=col, alpha=0.14, zorder=z, lw=0)
        ax.plot(xs, ys + base, color=col, lw=1.6 if extant else 1.2,
                zorder=z + 0.1, solid_capstyle="round")
        ax.plot([xs[0], xs[-1]], [base, base], color=th["baseline"], lw=0.6, zorder=z)
        if extant:
            ax.plot(xs[-1], base + ys[-1], "o", ms=4, color=col, zorder=z + 0.2)

        ax.text(xs[0] - 25, base + 0.6, name, ha="right", va="bottom",
                fontsize=9.5, color=col, zorder=60, fontweight="medium")

        k = int(np.argmax(ys))
        ax.annotate(f"{ys[k]:.1f}", (xs[k], base + ys[k]),
                    xytext=(0, 2), textcoords="offset points",
                    ha="center", va="bottom", fontsize=7, color=col, zorder=61)

    # height key: calibrates curve height (vertical row offsets carry no value)
    kx = -1060
    ax.plot([kx, kx], [0, 20], color=th["grey"], lw=1.0, zorder=50)
    for v in (0, 10, 20):
        ax.plot([kx - 14, kx], [v, v], color=th["grey"], lw=1.0, zorder=50)
        ax.text(kx - 30, v, str(v), ha="right", va="center", fontsize=7.5,
                color=th["grey"], zorder=50)
    ax.text(kx + 26, 10, "curve height,\nmillion km²\n(same scale\nin every row)",
            ha="left", va="center", fontsize=7.5, color=th["grey"], zorder=50,
            linespacing=1.5)

    ax.set_xlim(-1150, 2090)
    ax.set_ylim(-2, (n - 1) * spacing + 40)
    ax.set_xticks([-500, 1, 500, 1000, 1500, 2000])
    ax.xaxis.set_major_formatter(FuncFormatter(year_fmt))
    ax.tick_params(axis="x", labelsize=10, length=0, pad=6)
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    ax.set_title("The cascade of empires, 550 BCE – today",
                 fontsize=17, loc="left", pad=18, fontweight="bold", color=th["fg"])
    ax.text(0, 1.005, "Curve height = land ruled, million km² (see key, lower left) — "
            "one shared scale, so heights are comparable across all rows. A row's "
            "vertical position only orders empires by date of rise. Number marks each "
            "peak; dot = still on the map today. One colour per civilisation.",
            transform=ax.transAxes, fontsize=10, color=th["grey"], va="bottom")
    ax.text(0, -0.035, "Rows ordered by date of rise. Areas approximate, after "
            "R. Taagepera, “Size and Duration of Empires” (1978–1997).",
            transform=ax.transAxes, fontsize=8.5, color=th["grey"])

    fig.savefig(f"{OUT}/empires_cascade{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# ---------------------------------------------------------------- fig 2: modern power
GDP_YEARS = [1500, 1600, 1700, 1820, 1870, 1913, 1950, 1973, 1990, 2000, 2010, 2026]
GDP = {  # % of world GDP, PPP
    "China":        [24.9, 29.0, 22.3, 32.9, 17.1,  8.8,  4.5,  4.6,  7.8, 11.8, 16.5, 19.4],
    "India":        [24.4, 22.4, 24.4, 16.0, 12.1,  7.5,  4.2,  3.1,  4.0,  5.2,  6.6,  8.4],
    "United States":[ 0.3,  0.2,  0.1,  1.8,  8.8, 18.9, 27.3, 22.1, 21.5, 21.4, 16.8, 14.7],
    "Britain":      [ 1.1,  1.8,  2.9,  5.2,  9.0,  8.2,  6.5,  4.2,  3.4,  3.2,  2.6,  2.1],
    "Russia/USSR":  [ 3.4,  3.5,  4.4,  5.4,  7.5,  8.5,  9.6,  9.4,  7.0,  3.3,  3.5,  3.4],
    "Japan":        [ 3.1,  2.9,  4.1,  3.0,  2.3,  2.6,  3.0,  7.8,  8.6,  7.2,  5.0,  3.3],
}
GDP_STYLE = {
    "China":         ("#a03522", 2.0),
    "India":         ("#c08a3e", 1.6),
    "United States": ("#1f4e79", 2.0),
    "Britain":       ("#666666", 1.4),
    "Russia/USSR":   ("#7a6a8a", 1.4),
    "Japan":         ("#999999", 1.2),
}

def fig_modern(th):
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])
    for gy in (10, 20, 30):
        ax.axhline(gy, color=th["grid"], lw=0.8, zorder=0)

    ends = []
    for name, vals in GDP.items():
        c, lw = GDP_STYLE[name]
        c = lighten(c, th["mix"])
        ax.plot(GDP_YEARS, vals, color=c, lw=lw, zorder=3, solid_capstyle="round")
        ends.append([name, vals[-1], c])

    # spread right-edge labels to avoid collisions
    ends.sort(key=lambda e: e[1])
    min_gap = 1.6
    for j in range(1, len(ends)):
        if ends[j][1] - ends[j - 1][1] < min_gap:
            ends[j][1] = ends[j - 1][1] + min_gap
    for name, ly, c in ends:
        ax.text(2034, ly, f"{name}  {GDP[name][-1]:.0f}%", va="center",
                fontsize=9.5, color=c, fontweight="medium")

    us_c = lighten(GDP_STYLE["United States"][0], th["mix"])
    cn_c = lighten(GDP_STYLE["China"][0], th["mix"])
    ax.plot([1950], [27.3], "o", ms=4, color=us_c, zorder=4)
    ax.annotate("U.S. peak: 27% of world output, 1950", (1950, 27.3),
                xytext=(1565, 31.2), fontsize=8.5, color=us_c,
                arrowprops=dict(arrowstyle="-", color=us_c, lw=0.6))
    ax.plot([2014], [16.6], "o", ms=4, color=cn_c, zorder=4)
    ax.annotate("China re-passes the U.S. (PPP), ~2014", (2014, 16.6),
                xytext=(1918, 12.4), fontsize=8.5, color=cn_c,
                arrowprops=dict(arrowstyle="-", color=cn_c, lw=0.6))
    ax.annotate("Industrial Revolution:\nthe great divergence", (1820, 0.5),
                xytext=(1700, -5.6), fontsize=8.5, color=th["grey"], ha="center",
                annotation_clip=False,
                arrowprops=dict(arrowstyle="-", color=th["grey"], lw=0.6))

    ax.set_xlim(1500, 2032)
    ax.set_ylim(0, 35)
    ax.set_xticks([1500, 1600, 1700, 1820, 1870, 1913, 1950, 2026])
    ax.set_yticks([0, 10, 20, 30])
    ax.set_yticklabels(["0", "10", "20", "30%"])
    ax.tick_params(labelsize=9.5, length=0, pad=6)
    for s in ax.spines.values():
        s.set_visible(False)

    ax.set_title("Modern empires are economic: share of world GDP, 1500 – 2026",
                 fontsize=15, loc="left", pad=16, fontweight="bold", color=th["fg"])
    ax.text(0, 1.01, "Percent of world output (purchasing-power parity). "
            "Maddison Project estimates; IMF for recent decades.",
            transform=ax.transAxes, fontsize=9.5, color=th["grey"], va="bottom")

    fig.savefig(f"{OUT}/modern_power{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# ---------------------------------------------------------------- fig 3: life cycles
LIFECYCLE = [  # name, highlight colour or None
    ("Achaemenid Persia", None), ("Rome", "#1a1a1a"), ("Han China", None),
    ("Arab Caliphates", None), ("Mongol Empire", "#a03522"),
    ("Ottoman Empire", None), ("Spanish Empire", None), ("Qing China", None),
    ("British Empire", "#1f4e79"), ("Russia – USSR – Russia", "#7d4f63"),
    ("United States", "#2e6b4f"),
]

def fig_lifecycles(th):
    data = {name: pts for name, _x, _c, pts in EMPIRES}
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])
    for gy in (50, 100):
        ax.axhline(gy, color=th["grid"], lw=0.8, zorder=0)

    for name, hi in LIFECYCLE:
        pts = data[name]
        xs = np.array([p[0] for p in pts], float)
        ys = np.array([p[1] for p in pts], float)
        t = xs - xs[0]
        pct = 100 * ys / ys.max()
        if hi:
            c = lighten("#e8e5de" if hi == "#1a1a1a" and th["suffix"] else hi,
                        0 if hi == "#1a1a1a" else th["mix"])
            if hi == "#1a1a1a" and not th["suffix"]:
                c = hi
        else:
            c = "#4d4a44" if th["suffix"] else "#c8c5bf"
        lw = 1.8 if hi else 1.1
        ax.plot(t, pct, color=c, lw=lw, zorder=3 if hi else 2,
                solid_capstyle="round")
        if hi:
            short = name.split(" (")[0].split(" –")[0]
            if name == "United States":
                ax.plot(t[-1], pct[-1], "o", ms=5, color=c, zorder=4)
                ax.annotate(f"{short} — year 250 (today), at peak",
                            (t[-1], pct[-1]), xytext=(8, 6),
                            textcoords="offset points", fontsize=9, color=c)
            elif name.startswith("Russia"):
                ax.plot(t[-1], pct[-1], "o", ms=5, color=c, zorder=4)
                ax.annotate("Russia — year 479 (today), 75% of peak",
                            (t[-1], pct[-1]), xytext=(8, 0),
                            textcoords="offset points", fontsize=9, color=c)
            else:
                ax.annotate(short, (t[-1], pct[-1]), xytext=(4, 3),
                            textcoords="offset points", fontsize=9, color=c)

    ax.set_xlim(0, 830)
    ax.set_ylim(0, 108)
    ax.set_xticks([0, 100, 200, 300, 400, 500, 600, 700, 800])
    ax.set_yticks([0, 50, 100])
    ax.set_yticklabels(["0", "50", "100%"])
    ax.tick_params(labelsize=9.5, length=0, pad=6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlabel("Years since founding", fontsize=10, color=th["fg"])

    ax.set_title("Every empire on its own clock: extent as % of its peak",
                 fontsize=15, loc="left", pad=16, fontweight="bold", color=th["fg"])
    ax.text(0, 1.01, "Grey: Achaemenid, Han, Caliphates, Ottoman, Spanish, Qing. "
            "All curves share the same clock (years since founding) "
            "and the same vertical scale (% of own peak).",
            transform=ax.transAxes, fontsize=9.5, color=th["grey"], va="bottom")

    fig.savefig(f"{OUT}/empire_lifecycles{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# ---------------------------------------------------------------- JS data export
def export_js():
    rows = []
    for name, extant, col, pts in EMPIRES:
        rows.append(dict(name=name, extant=extant,
                         color=col, colorDark=lighten(col, 0.38),
                         pts=[[int(y), v] for y, v in pts]))
    with open(f"{OUT}/empires_data.js", "w") as f:
        f.write("// Generated by make_empire_plots.py — do not edit by hand.\n")
        f.write("const EMPIRES = " + json.dumps(rows, ensure_ascii=False) + ";\n")

for theme in THEMES.values():
    plt.rcParams.update({
        "font.family": "Helvetica Neue",
        "text.color": theme["fg"],
        "xtick.color": theme["fg"],
        "ytick.color": theme["fg"],
        "svg.fonttype": "none",
    })
    fig_cascade(theme)
    fig_modern(theme)
    fig_lifecycles(theme)
export_js()
print("done")
