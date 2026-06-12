"""
Four models of imperial power, one ensemble index, in light and dark themes.

power_lenses[_dark].png    - the same empires under four lenses (small multiples)
power_ensemble[_dark].png  - equal-weight geometric-mean index, with model-disagreement bands
power_today[_dark].png     - 2026 through each lens (slope chart), British 1913 as ghost
power_data.js              - data export for the interactive weighted index

Every series is a SHARE of the contemporaneous world (percent), which is what makes
epochs comparable: power is relational, so it is always measured against rivals who
held the same technology and the same world.

  p  share of world population under direct rule
       (after McEvedy & Jones; Maddison Project)
  y  share of world gross product, PPP
       (Maddison Project; IMF WEO for recent decades;
        before ~1500 set equal to p: near-subsistence economies produce
        in proportion to their people)
  m  share of world military capacity
       (manpower estimates pre-1900, after P. Kennedy and the Correlates
        of War project; blended toward share of world military spending,
        SIPRI, in the 20th century)
  n  share of world population inside the sphere of influence
       (vassals, tributaries, formal allies, monetary/linguistic orbit -
        the softest numbers on this page, estimated to one significant figure)

Ensemble: P = (p * y * m * n)^(1/4)  (equal-weight geometric mean).
All values approximate; the interactive lets the reader reweight everything.
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
    if t <= 0:
        return hex_color
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    f = lambda v: int(round(v + (255 - v) * t))
    return f"#{f(r):02x}{f(g):02x}{f(b):02x}"

MODELS = ["p", "y", "m", "n"]
MODEL_TITLES = {
    "p": "Population ruled",
    "y": "Economic output",
    "m": "Military capacity",
    "n": "Network / sphere of influence",
}
MODEL_SUBTITLES = {
    "p": "% of world population under direct rule",
    "y": "% of world gross product (PPP); pre-1500 ≈ population share",
    "m": "% of world military manpower, later spending",
    "n": "% of world population in the wider sphere: tribute, alliance, money, language",
}

# (name, extant, colour, {model: [(year, % of world)...]})
# 'y': None means y = p (agrarian, near-subsistence era).
EMPIRES = [
    ("Achaemenid Persia", False, "#5e7d4f", {
        "p": [(-550,5),(-520,22),(-480,30),(-450,28),(-400,25),(-350,22),(-330,8)],
        "y": None,
        "m": [(-550,6),(-520,28),(-480,35),(-450,25),(-400,20),(-350,18),(-330,6)],
        "n": [(-550,6),(-520,26),(-480,35),(-450,32),(-400,28),(-350,24),(-330,8)],
    }),
    ("Rome", False, "#54678a", {
        "p": [(-200,3),(-100,8),(-30,18),(14,21),(117,26),(165,28),(250,24),(350,20),(410,14),(476,2)],
        "y": None,
        "m": [(-200,4),(-100,10),(-30,20),(117,25),(165,25),(250,22),(350,16),(410,9),(476,1)],
        "n": [(-200,4),(-100,12),(-30,22),(117,30),(165,31),(250,26),(350,21),(410,14),(476,2)],
    }),
    ("Han China", False, "#9c453a", {
        "p": [(-206,12),(-150,18),(-100,22),(2,26),(105,25),(157,26),(190,14),(220,4)],
        "y": None,
        "m": [(-206,12),(-120,24),(2,28),(105,24),(157,24),(190,10),(220,3)],
        "n": [(-206,12),(-100,26),(2,30),(105,29),(157,28),(190,12),(220,4)],
    }),
    ("Arab Caliphates", False, "#3e7d78", {
        "p": [(632,1),(661,8),(700,13),(750,18),(800,20),(861,16),(900,11),(945,5)],
        "y": None,
        "m": [(632,2),(661,14),(700,20),(750,22),(800,18),(861,13),(900,8),(945,3)],
        "n": [(632,1),(661,10),(700,17),(750,24),(800,30),(861,24),(900,16),(945,7)],
    }),
    ("Mongol Empire", False, "#6e5340", {
        "p": [(1206,1),(1227,8),(1241,14),(1260,20),(1279,25),(1294,26),(1330,22),(1368,6)],
        "y": None,
        "m": [(1206,4),(1227,20),(1241,30),(1260,38),(1279,40),(1294,38),(1330,26),(1368,7)],
        "n": [(1206,1),(1227,10),(1241,18),(1260,26),(1279,33),(1294,35),(1330,26),(1368,7)],
    }),
    ("Ming China", False, "#9c453a", {
        "p": [(1368,22),(1450,25),(1500,25),(1600,29),(1644,26)],
        "y": [(1368,23),(1500,25),(1600,29),(1644,26)],
        "m": [(1368,26),(1420,30),(1500,22),(1600,19),(1644,8)],
        "n": [(1368,24),(1420,33),(1450,30),(1500,28),(1600,26),(1644,12)],
    }),
    ("Ottoman Empire", False, "#7b5e75", {
        "p": [(1299,0.2),(1400,1),(1453,2),(1520,4),(1600,5.5),(1683,5),(1750,4.5),(1800,4),(1850,2.5),(1914,1.5),(1922,1)],
        "y": [(1299,0.2),(1453,2.5),(1520,4.5),(1600,5),(1700,4.5),(1820,3),(1870,2),(1913,1.2),(1922,0.8)],
        "m": [(1299,0.5),(1453,8),(1520,12),(1600,10),(1683,8),(1750,5),(1800,4),(1850,3),(1914,2.5),(1922,0.5)],
        "n": [(1299,0.3),(1453,5),(1520,9),(1600,9),(1683,7),(1800,5),(1900,3),(1922,1)],
    }),
    ("Spanish Empire", False, "#8a7d3a", {
        "p": [(1492,1.5),(1550,4),(1600,5),(1650,4.5),(1700,4.5),(1790,5),(1810,4.5),(1825,1.5),(1898,1)],
        "y": [(1492,1.8),(1550,4.5),(1600,5.5),(1650,4.5),(1700,4),(1790,4.5),(1825,1.5),(1898,0.8)],
        "m": [(1492,3),(1550,8),(1600,9),(1650,5),(1700,3),(1790,3),(1825,1),(1898,0.3)],
        "n": [(1492,2),(1550,8),(1600,12),(1650,10),(1700,8),(1790,6),(1825,2),(1898,0.5)],
    }),
    ("Mughal (India)", False, "#b3873e", {
        "p": [(1526,4),(1560,12),(1600,20),(1650,22),(1700,24),(1739,20),(1760,12),(1803,4),(1857,0.5)],
        "y": [(1526,5),(1600,22),(1700,24),(1739,20),(1760,11),(1803,3),(1857,0.4)],
        "m": [(1526,8),(1560,14),(1600,18),(1700,20),(1739,12),(1760,7),(1803,2),(1857,0.2)],
        "n": [(1526,5),(1600,21),(1700,25),(1739,18),(1760,9),(1803,3),(1857,0.3)],
    }),
    ("Qing China", False, "#9c453a", {
        "p": [(1644,22),(1700,23),(1750,30),(1800,36),(1850,35),(1880,30),(1900,26),(1912,24)],
        "y": [(1644,22),(1700,22),(1750,28),(1820,33),(1870,17),(1900,11),(1912,9)],
        "m": [(1644,22),(1700,25),(1760,28),(1800,25),(1850,14),(1880,8),(1900,4),(1912,2)],
        "n": [(1644,24),(1700,27),(1760,32),(1800,30),(1850,16),(1880,10),(1900,5),(1912,3)],
    }),
    ("British Empire", False, "#2e5e8a", {
        "p": [(1600,1),(1700,1.5),(1763,2.5),(1800,4),(1820,12),(1870,16),(1913,23),(1938,22),(1947,7),(1960,2),(1965,1.3)],
        "y": [(1600,1.8),(1700,3.5),(1763,5),(1820,13),(1870,21),(1913,20),(1938,17),(1947,7),(1960,3),(1965,2.5)],
        "m": [(1600,1.5),(1700,4),(1763,8),(1815,16),(1870,15),(1913,12),(1941,15),(1947,6),(1960,3),(1965,2.5)],
        "n": [(1600,1.5),(1700,4),(1763,8),(1820,18),(1870,30),(1913,36),(1938,30),(1947,14),(1960,7),(1965,5)],
    }),
    ("Russia – USSR – Russia", True, "#7d4f63", {
        "p": [(1547,1.5),(1600,2),(1700,3),(1800,6),(1850,7),(1900,8),(1950,7.1),(1989,5.5),(1992,2.6),(2026,1.7)],
        "y": [(1547,2),(1700,4),(1820,5.4),(1870,7.5),(1913,8.5),(1950,9.6),(1973,9.4),(1989,8),(2000,3.3),(2026,3.4)],
        "m": [(1547,2),(1700,8),(1815,20),(1870,15),(1900,14),(1950,30),(1975,35),(1989,28),(2000,4),(2026,8)],
        "n": [(1547,1.5),(1700,4),(1815,12),(1900,9),(1950,16),(1975,19),(1989,12),(2000,3),(2026,4)],
    }),
    ("United States", True, "#2e6b4f", {
        "p": [(1776,0.3),(1850,1.9),(1900,4.6),(1950,6.0),(1990,4.7),(2026,4.1)],
        "y": [(1776,0.4),(1820,1.8),(1870,8.8),(1913,18.9),(1950,27.3),(1973,22.1),(2000,21.4),(2026,14.7)],
        "m": [(1776,0.3),(1850,2),(1898,6),(1918,18),(1925,8),(1945,45),(1955,32),(1975,28),(1990,35),(2010,42),(2026,37)],
        "n": [(1776,0.3),(1850,2),(1900,6),(1918,12),(1945,35),(1950,42),(1975,35),(1991,46),(2010,42),(2026,33)],
    }),
    ("China (PRC)", True, "#9c453a", {
        "p": [(1949,22),(1980,22.3),(2000,20.7),(2026,17.1)],
        "y": [(1949,4.5),(1980,5),(2000,11.8),(2014,16.6),(2026,19.4)],
        "m": [(1949,15),(1965,12),(1980,10),(2000,6),(2026,13)],
        "n": [(1949,9),(1960,7),(1980,5),(2000,8),(2013,12),(2026,20)],
    }),
    ("India (Republic)", True, "#b3873e", {
        "p": [(1947,14.5),(1980,15.5),(2000,17),(2026,17.7)],
        "y": [(1947,4.2),(1980,3.3),(2000,5.2),(2026,8.4)],
        "m": [(1947,3),(1980,3),(2000,3),(2026,3.5)],
        "n": [(1947,6),(1961,7),(1980,5),(2000,5),(2026,8)],
    }),
]

def series(e, k):
    s = e[3][k]
    return e[3]["p"] if s is None else s

def interp(pts, t):
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    return np.interp(t, xs, ys)

def lifespan(e):
    t0 = min(series(e, k)[0][0] for k in MODELS)
    t1 = max(series(e, k)[-1][0] for k in MODELS)
    return t0, t1

def ensemble(e, step=2):
    """Equal-weight geometric mean of the four model shares, on a year grid."""
    t0, t1 = lifespan(e)
    t = np.arange(t0, t1 + 1, step, dtype=float)
    prod = np.ones_like(t)
    lo = np.full_like(t, np.inf)
    hi = np.zeros_like(t)
    for k in MODELS:
        v = np.maximum(interp(series(e, k), t), 0.05)
        prod *= v
        lo = np.minimum(lo, v)
        hi = np.maximum(hi, v)
    return t, prod ** 0.25, lo, hi

def year_fmt(y, _pos=None):
    if y < 0:
        return f"{int(-y)} BCE"
    if y == 1:
        return "1 CE"
    return f"{int(y)}"

XT = [-500, 1, 500, 1000, 1500, 2000]
XLIM = (-620, 2080)

# which curves get a direct label in each lens panel, with nudges (dx, dy, ha)
PANEL_LABELS = {
    "p": {"Achaemenid Persia": (0, 1, "center"), "Rome": (0, 1, "center"),
          "Qing China": (0, 1, "center"), "Mongol Empire": (0, 1, "center"),
          "British Empire": (-30, 1.2, "right"), "China (PRC)": (8, 2.2, "center"),
          "India (Republic)": (-31, -6.4, "center")},
    "y": {"Han China": (0, 1, "center"), "Qing China": (-40, 1, "center"),
          "Mughal (India)": (-140, -7, "center"), "United States": (0, 1.2, "center"),
          "China (PRC)": (40, 0, "left"), "Ming China": (-120, 1, "center")},
    "m": {"Achaemenid Persia": (0, 1, "center"), "Mongol Empire": (0, 1, "center"),
          "United States": (0, 1.2, "center"), "Russia – USSR – Russia": (-10, 2.5, "right"),
          "Qing China": (0, 1, "center")},
    "n": {"Achaemenid Persia": (0, 1, "center"), "Arab Caliphates": (0, 1, "center"),
          "Mongol Empire": (0, 1, "center"), "British Empire": (-30, 1.2, "right"),
          "Qing China": (0, 1, "center"), "United States": (0, 1.2, "center")},
}

def peak_of(pts):
    k = max(range(len(pts)), key=lambda j: pts[j][1])
    return pts[k]

# -------------------------------------------------- fig 1: four lenses
def fig_lenses(th):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.6), sharex=True, sharey=True)
    fig.patch.set_facecolor(th["bg"])
    for ax, k in zip(axes.flat, MODELS):
        ax.set_facecolor(th["bg"])
        for gy in (10, 20, 30, 40):
            ax.axhline(gy, color=th["grid"], lw=0.7, zorder=0)
        for e in EMPIRES:
            name, extant, col, _ = e
            c = lighten(col, th["mix"])
            pts = series(e, k)
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            ax.plot(xs, ys, color=c, lw=1.5 if name in PANEL_LABELS[k] else 0.9,
                    alpha=1.0 if name in PANEL_LABELS[k] else 0.55,
                    zorder=3 if name in PANEL_LABELS[k] else 2,
                    solid_capstyle="round")
            if name in PANEL_LABELS[k]:
                dx, dy, ha = PANEL_LABELS[k][name]
                px, pv = peak_of(pts)
                short = name.replace(" Empire", "").replace(" (India)", "") \
                            .replace(" – USSR – Russia", "/USSR").replace(" China", "")
                if name == "China (PRC)":
                    short = "PRC"
                if name == "India (Republic)":
                    short = "India"
                if name == "United States":
                    short = "US"
                if name == "Qing China":
                    short = "Qing"
                if name == "Han China":
                    short = "Han"
                if name == "Ming China":
                    short = "Ming"
                ax.text(px + dx, pv + dy, short, fontsize=8, color=c,
                        ha=ha, va="bottom", fontweight="medium", zorder=5)
        ax.set_xlim(*XLIM)
        ax.set_ylim(0, 50)
        ax.set_xticks(XT)
        ax.xaxis.set_major_formatter(FuncFormatter(year_fmt))
        ax.set_yticks([0, 10, 20, 30, 40])
        ax.set_yticklabels(["0", "10", "20", "30", "40%"])
        ax.tick_params(labelsize=8.5, length=0, pad=4)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(MODEL_TITLES[k], fontsize=12, loc="left",
                     fontweight="bold", color=th["fg"], pad=14)
        ax.text(0, 1.012, MODEL_SUBTITLES[k], transform=ax.transAxes,
                fontsize=8, color=th["grey"], va="bottom")
    fig.suptitle("Four lenses on the same empires, 550 BCE – 2026",
                 fontsize=16, x=0.065, ha="left", fontweight="bold", color=th["fg"])
    fig.text(0.065, 0.945, "Each panel is a share of the contemporaneous world, so every era is "
             "measured against its own rivals. The lenses agree about antiquity and "
             "disagree violently about the present.", fontsize=9.5, color=th["grey"])
    fig.subplots_adjust(top=0.885, bottom=0.05, left=0.065, right=0.98,
                        hspace=0.3, wspace=0.08)
    fig.savefig(f"{OUT}/power_lenses{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# -------------------------------------------------- fig 2: ensemble
ENSEMBLE_SET = ["Achaemenid Persia", "Rome", "Han China", "Arab Caliphates",
                "Mongol Empire", "Qing China", "British Empire",
                "United States", "China (PRC)"]
ENSEMBLE_LBL = {  # (dx, dy, ha)
    "Achaemenid Persia": (0, 0.8, "center"), "Rome": (0, 0.8, "center"),
    "Han China": (40, 0.8, "left"), "Arab Caliphates": (0, 0.8, "center"),
    "Mongol Empire": (0, 0.8, "center"), "Qing China": (0, 0.8, "center"),
    "British Empire": (-25, 0.9, "right"), "United States": (0, 1.4, "center"),
    "China (PRC)": (35, -1.2, "left"),
}

def fig_ensemble(th):
    fig, ax = plt.subplots(figsize=(13, 6.8))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])
    for gy in (10, 20, 30):
        ax.axhline(gy, color=th["grid"], lw=0.7, zorder=0)
    data = {e[0]: e for e in EMPIRES}
    for name in ENSEMBLE_SET:
        e = data[name]
        c = lighten(e[2], th["mix"])
        t, P, lo, hi = ensemble(e)
        ax.fill_between(t, lo, hi, color=c, alpha=0.10, lw=0, zorder=2)
        ax.plot(t, P, color=c, lw=1.7 if e[1] else 1.4, zorder=3,
                solid_capstyle="round")
        if e[1]:
            ax.plot(t[-1], P[-1], "o", ms=4, color=c, zorder=4)
        kpk = int(np.argmax(P))
        dx, dy, ha = ENSEMBLE_LBL[name]
        short = name.replace(" Empire", "").replace(" Persia", "") \
                    .replace(" China", "").replace(" (PRC)", " (PRC)")
        if name == "Arab Caliphates":
            short = "Caliphates"
        if name == "United States":
            short = "US"
        ax.text(t[kpk] + dx, P[kpk] + dy, short, fontsize=8.5, color=c,
                ha=ha, va="bottom", fontweight="medium", zorder=5)
    ax.set_xlim(*XLIM)
    ax.set_ylim(0, 38)
    ax.set_xticks(XT)
    ax.xaxis.set_major_formatter(FuncFormatter(year_fmt))
    ax.set_yticks([0, 10, 20, 30])
    ax.set_yticklabels(["0", "10", "20", "30%"])
    ax.tick_params(labelsize=9.5, length=0, pad=6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("One index: the equal-weight ensemble, 550 BCE – 2026",
                 fontsize=15, loc="left", pad=16, fontweight="bold", color=th["fg"])
    ax.text(0, 1.012, "Line: geometric mean of the four lenses. Shaded band: the span "
            "between the empire's friendliest and harshest lens — wide bands mean the "
            "verdict depends on your theory of power. Dot = still on the map.",
            transform=ax.transAxes, fontsize=9.5, color=th["grey"], va="bottom")
    fig.savefig(f"{OUT}/power_ensemble{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# -------------------------------------------------- fig 3: today, by lens
TODAY = {  # 2026 values under each lens
    "United States":  dict(p=4.1,  y=14.7, m=37.0, n=33.0, c="#2e6b4f"),
    "China (PRC)":    dict(p=17.1, y=19.4, m=13.0, n=20.0, c="#9c453a"),
    "India":          dict(p=17.7, y=8.4,  m=3.5,  n=8.0,  c="#b3873e"),
    "Russia":         dict(p=1.7,  y=3.4,  m=8.0,  n=4.0,  c="#7d4f63"),
}
GHOST = dict(name="British Empire, 1913", p=23.0, y=20.0, m=12.0, n=36.0)

def fig_today(th):
    fig, ax = plt.subplots(figsize=(11.5, 6.6))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])
    xs = range(4)
    gv = [GHOST[k] for k in MODELS]
    ax.plot(xs, gv, color=th["grey"], lw=1.1, ls=(0, (4, 3)), zorder=2)
    for x, v in zip(xs, gv):
        ax.plot(x, v, "o", ms=3.5, color=th["grey"], zorder=2)
    ax.text(3.08, gv[-1], GHOST["name"], fontsize=8.5, color=th["grey"],
            va="center", style="italic")
    name_y = {"United States": 4.1, "China (PRC)": 14.8, "India": 20.3, "Russia": 1.7}
    val_off = {("China (PRC)", 0): (0, -13), ("India", 0): (0, 6)}
    for name, d in TODAY.items():
        c = lighten(d["c"], th["mix"])
        vals = [d[k] for k in MODELS]
        ax.plot(xs, vals, color=c, lw=2.0, zorder=3, solid_capstyle="round")
        for x, v in zip(xs, vals):
            ax.plot(x, v, "o", ms=4.5, color=c, zorder=4)
            dx, dy = val_off.get((name, x), (0, 5))
            ax.annotate(f"{v:.0f}" if v >= 3 else f"{v:.1f}", (x, v),
                        xytext=(dx, dy), textcoords="offset points",
                        ha="center", fontsize=8, color=c, zorder=5)
        ax.text(-0.08, name_y[name], name, fontsize=10, color=c, ha="right",
                va="center", fontweight="medium")
    ax.set_xlim(-0.85, 4.05)
    ax.set_ylim(0, 42)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([MODEL_TITLES[k] for k in MODELS], fontsize=10.5)
    ax.set_yticks([])
    ax.tick_params(length=0, pad=10)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("2026 through each lens: pick your theory of power, pick your winner",
                 fontsize=15, loc="left", pad=16, fontweight="bold", color=th["fg"])
    ax.text(0, 1.012, "Share of the 2026 world under each model, percent. The dashed "
            "grey line is the British Empire in 1913, for calibration.",
            transform=ax.transAxes, fontsize=9.5, color=th["grey"], va="bottom")
    fig.savefig(f"{OUT}/power_today{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# -------------------------------------------------- JS export
def export_js():
    rows = []
    for name, extant, col, _ in EMPIRES:
        e = next(x for x in EMPIRES if x[0] == name)
        rows.append(dict(
            name=name, extant=extant, color=col, colorDark=lighten(col, 0.38),
            series={k: [[int(t), v] for t, v in series(e, k)] for k in MODELS}))
    payload = dict(models=MODEL_TITLES, subtitles=MODEL_SUBTITLES, empires=rows)
    with open(f"{OUT}/power_data.js", "w") as f:
        f.write("// Generated by make_power_models.py — do not edit by hand.\n")
        f.write("const POWER = " + json.dumps(payload, ensure_ascii=False) + ";\n")

for theme in THEMES.values():
    plt.rcParams.update({
        "font.family": "Helvetica Neue",
        "text.color": theme["fg"],
        "xtick.color": theme["fg"],
        "ytick.color": theme["fg"],
    })
    fig_lenses(theme)
    fig_ensemble(theme)
    fig_today(theme)
export_js()
print("done")
