"""
How early could a rocket have reached orbit? Three figures, light and dark.

rocket_wall[_dark].png        - total delta-v attainable vs number of stages, by
                                propellant/structure era ("the wall")
rocket_price[_dark].png       - minimum gross liftoff mass to orbit a 10 kg
                                satellite, by era, against real vehicles
rocket_ingredients[_dark].png - arrival dates of every enabling technology,
                                1550-1980 ("the ingredient list")

The model is the ideal multi-stage rocket equation and nothing else:

  per-stage payload fraction   lam = (exp(-dv_s/ve) - eps) / (1 - eps)
  N equal stages               lam_tot = lam^N,   m0 = m_pay / lam_tot

where ve is effective exhaust velocity (averaged over the ascent), eps the
structural fraction of each stage (casing, nozzle, fins as a share of stage
mass), and dv_s = DV_REQ/N (equal split is optimal for identical stages).
DV_REQ = 9.4 km/s: ~7.8 km/s orbital speed at ~200 km plus ~1.6 km/s of
gravity, drag and steering losses.

Era parameters are deliberately round and defended in the post's Method
section. The model is an idealised *floor*: real vehicles (Lambda-4S, Scout)
come out 1.5-4x heavier, which is stated and drawn.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

THEMES = {
    "light": dict(suffix="", bg="#faf9f5", fg="#33312c", grey="#8a857c",
                  grid="#e7e4dc", band="#e7e4dc",
                  cols=dict(bp="#9c453a", smk="#b3873e", cmp="#2f629c",
                            liq="#2d7d52", hist="#8a857c")),
    "dark":  dict(suffix="_dark", bg="#262624", fg="#e8e5de", grey="#a09a8e",
                  grid="#3a3833", band="#33322e",
                  cols=dict(bp="#c25a3c", smk="#b98a2c", cmp="#5b8ed8",
                            liq="#3ba26b", hist="#a09a8e")),
}

G0 = 9.80665
DV_REQ = 9.4          # km/s to a low orbit, losses included

# (key, label, Isp_eff s, eps, dashed)
ERAS = [
    ("bp",  "Black powder, period casings (1800)",   70, 0.45, False),
    ("bpx", "Black powder, perfect casings",          80, 0.10, True),
    ("smk", "Smokeless powder + steel (1890s)",      210, 0.18, False),
    ("cmp", "Composite solid (1960)",                250, 0.11, False),
    ("liq", "Kerosene–LOX liquid (1957)",       280, 0.08, False),
]

def ve_of(isp):
    return isp * G0 / 1000.0            # km/s

def dv_total(isp, eps, N, lam_tot):
    """Max total delta-v (km/s) of N equal stages carrying overall payload
    fraction lam_tot."""
    ve = ve_of(isp)
    lam = lam_tot ** (1.0 / N)          # per-stage payload fraction
    mf_frac = eps + (1 - eps) * lam     # per-stage final/initial mass
    if mf_frac >= 1:
        return 0.0
    return N * ve * np.log(1.0 / mf_frac)

def payload_fraction(isp, eps, N, dv=DV_REQ):
    """Overall payload fraction of N equal stages delivering dv; None if the
    structure alone already weighs too much."""
    ve = ve_of(isp)
    lam = (np.exp(-dv / (N * ve)) - eps) / (1 - eps)
    if lam <= 0:
        return None
    return lam ** N

def min_gross(isp, eps, m_pay=10.0, n_max=24, dv=DV_REQ):
    """(best N, minimum gross mass in tonnes) over 1..n_max stages."""
    best = None
    for N in range(1, n_max + 1):
        lt = payload_fraction(isp, eps, N, dv)
        if lt is None:
            continue
        m0 = m_pay / lt / 1000.0        # tonnes
        if best is None or m0 < best[1]:
            best = (N, m0)
    return best

# ------------------------------------------------------------- console table
print(f"{'era':38s} {'ve km/s':>8s} {'eps':>5s} {'best N':>7s} {'m0 (t) for 10 kg':>18s}")
for key, label, isp, eps, _ in ERAS:
    b = min_gross(isp, eps, n_max=200 if key == "bp" else 24)
    asym = np.exp(-DV_REQ / (ve_of(isp) * (1 - eps)))
    print(f"{label:38s} {ve_of(isp):8.2f} {eps:5.2f} "
          + (f"{b[0]:7d} {b[1]:18,.1f}" if b else f"{'-':>7s} {'impossible':>18s}")
          + f"   (infinite-stage floor {10/asym/1000:,.0f} t)")

# ---------------------------------------------------------------- fig 1: wall
def fig_wall(th):
    fig, ax = plt.subplots(figsize=(13, 6.8))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])
    Ns = np.arange(1, 17)
    LAM = 1e-3                          # a 10 kg satellite on a 10 t rocket
    ax.axhspan(9.0, 9.7, color=th["band"], zorder=0)
    ax.text(15.9, 9.62, "low Earth orbit, losses included",
            fontsize=8.5, color=th["grey"], ha="right", va="top")
    for gy in (2, 4, 6, 8, 10, 12):
        ax.axhline(gy, color=th["grid"], lw=0.7, zorder=0)
    for key, label, isp, eps, dashed in ERAS:
        col = th["cols"]["bp" if key == "bpx" else key]
        ys = np.array([dv_total(isp, eps, int(N), LAM) for N in Ns])
        ax.plot(Ns, ys, color=col, lw=1.9, ls=(0, (5, 3)) if dashed else "-",
                solid_capstyle="round", zorder=3)
        short = {"bp": "black powder, period casings",
                 "bpx": "black powder, perfect casings",
                 "smk": "smokeless powder + steel, 1890s",
                 "cmp": "composite solid, 1960",
                 "liq": "kerosene–LOX, 1957"}[key]
        if ys[-1] <= 12.4:              # label at the line's right end
            ax.text(16.25, ys[-1], short, fontsize=9, color=col, va="center")
        elif key == "liq":              # lines exit the top: label at the exit
            xc = float(np.interp(11.6, ys, Ns))
            ax.text(xc - 0.15, 11.6, short, fontsize=9, color=col,
                    ha="right", va="center")
        else:
            xc = float(np.interp(12.3, ys, Ns))
            ax.text(xc + 0.18, 12.3, short, fontsize=9, color=col,
                    ha="left", va="center")
    ax.set_xlim(1, 16)
    ax.set_ylim(0, 13)
    ax.set_xticks([1, 2, 4, 6, 8, 10, 12, 14, 16])
    ax.set_yticks([0, 2, 4, 6, 8, 10, 12])
    ax.set_yticklabels(["0", "2", "4", "6", "8", "10", "12 km/s"])
    ax.set_xlabel("number of stages", fontsize=10, color=th["grey"])
    ax.tick_params(labelsize=9.5, length=0, pad=6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("The wall: total velocity attainable vs number of stages",
                 fontsize=15, loc="left", pad=16, fontweight="bold", color=th["fg"])
    ax.text(0, 1.012, "Ideal staged rockets carrying a 10 kg satellite on a 10-tonne "
            "vehicle (payload fraction 10⁻³), eq. (3.5). Black powder saturates far "
            "below orbit no matter how many stages; smokeless powder crosses the line "
            "at four.", transform=ax.transAxes, fontsize=9.5, color=th["grey"],
            va="bottom")
    fig.savefig(f"{OUT}/rocket_wall{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# --------------------------------------------------------------- fig 2: price
REFS = [  # (mass t, label)
    (9.4,    "Lambda-4S, 1970"),
    (21.5,   "Scout, 1961"),
    (267,    "R-7 / Sputnik, 1957"),
    (7300,   "Eiffel Tower"),
    (18120,  "HMS Dreadnought"),
]

def fig_price(th):
    rows = [
        ("smk", "Smokeless powder + steel — buildable 1890s", 210, 0.18, 5),
        ("cmp", "Composite solid — 1960",                     250, 0.11, 5),
        ("liq", "Kerosene–LOX liquid — 1957",            280, 0.08, 3),
        ("bp",  "Black powder, perfect casings",               80, 0.10, 24),
    ]
    fig, ax = plt.subplots(figsize=(13, 6.2))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])
    ax.set_xscale("log")
    for m, lab in REFS:
        ax.axvline(m, color=th["grid"], lw=0.9, zorder=0)
        ax.text(m * 0.93, 4.55, lab, fontsize=8, color=th["grey"], rotation=90,
                ha="right", va="top")
    ys = np.arange(len(rows))[::-1]
    for (key, label, isp, eps, nmax), y in zip(rows, ys):
        col = th["cols"]["bp" if key == "bp" else key]
        N, m0 = min_gross(isp, eps, n_max=nmax)
        ax.plot([m0, 4 * m0], [y, y], color=col, lw=7, alpha=0.30,
                solid_capstyle="butt", zorder=2)
        ax.plot(m0, y, "o", ms=8, color=col, zorder=4)
        ax.text(m0, y - 0.38, f"{m0:,.0f} t floor · {N} stages"
                if m0 >= 100 else f"{m0:,.1f} t floor · {N} stages",
                fontsize=8.5, color=col, ha="center", va="top", zorder=5)
        ax.text(0.42, y + 0.30, label, fontsize=10, color=col, ha="left",
                va="bottom", fontweight="medium")
    ax.set_xlim(0.4, 60000)
    ax.set_ylim(-0.85, 4.6)
    ax.set_yticks([])
    ax.set_xticks([1, 10, 100, 1000, 10000])
    ax.set_xticklabels(["1 t", "10 t", "100 t", "1,000 t", "10,000 t"])
    ax.tick_params(labelsize=9.5, length=0, pad=6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("The price of orbit: liftoff mass to put 10 kg in orbit, by chemistry",
                 fontsize=15, loc="left", pad=16, fontweight="bold", color=th["fg"])
    ax.text(0, 1.015, "Dot: idealised floor from eq. (3.5); band: ×1–4, the range real "
            "vehicles land in (Scout flew at ×1.5 its floor, Lambda-4S at ×2.5–4). Grey "
            "verticals: real objects for scale. Black powder in period casings never "
            "reaches orbit at any mass — its floor is ~650,000,000 t.",
            transform=ax.transAxes, fontsize=9.5, color=th["grey"], va="bottom")
    fig.savefig(f"{OUT}/rocket_price{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# --------------------------------------------------------- fig 3: ingredients
# (year, label, group)  groups: T theory, H hardware, C chemistry, W what happened
EVENTS = [
    (1556, "Staged rockets drawn (Conrad Haas ms.)",            "T"),
    (1650, "Staging in print (Siemienowicz)",                   "T"),
    (1687, "Orbit shown to be a speed (Newton)",                "T"),
    (1780, "Iron-cased war rockets (Mysore)",                   "H"),
    (1813, "Rocket equation (Moore, Woolwich)",                 "T"),
    (1844, "Spin stabilisation (Hale)",                         "H"),
    (1846, "Nitrocellulose (Schönbein)",                   "C"),
    (1847, "Nitroglycerine (Sobrero)",                          "C"),
    (1852, "Gyroscope (Foucault)",                              "H"),
    (1856, "Cheap steel (Bessemer)",                            "H"),
    (1884, "Smokeless powder (Vieille)",                        "C"),
    (1887, "Ballistite — double-base (Nobel)",                  "C"),
    (1888, "Supersonic nozzle (de Laval)",                      "H"),
    (1889, "Cordite (Abel & Dewar)",                            "C"),
    (1895, "Gyroscopic autopilot (Obry)",                       "H"),
    (1896, "Radio (Marconi)",                                   "H"),
    (1903, "Full theory of spaceflight (Tsiolkovsky)",          "T"),
    (1926, "First liquid-fuel flight (Goddard)",                "W"),
    (1944, "First object in space (V-2, liquid)",               "W"),
    (1957, "Sputnik (R-7, liquid)",                             "W"),
    (1961, "First all-solid orbit (Scout)",                     "W"),
    (1970, "All-solid, no guidance (Lambda-4S)",                "W"),
]
GROUP_NAMES = {"T": "the idea", "H": "the hardware", "C": "the chemistry",
               "W": "what actually happened"}

def fig_ingredients(th):
    gcol = {"T": th["cols"]["cmp"], "H": th["cols"]["bp"],
            "C": th["cols"]["smk"], "W": th["cols"]["hist"]}
    n = len(EVENTS)
    fig, ax = plt.subplots(figsize=(13, 9.2))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])
    X0, X1 = 1535, 1992
    ax.axvspan(1884, 1896, color=th["band"], zorder=0)
    ax.text(1881, -1.05, "the ingredient decade:", fontsize=8.5,
            color=th["grey"], ha="right", va="center", style="italic")
    for gx in (1600, 1700, 1800, 1900):
        ax.axvline(gx, color=th["grid"], lw=0.7, zorder=0)
    ax.axvline(1957, color=th["grey"], lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.text(1954.5, -1.15, "Sputnik", fontsize=8.5, color=th["grey"],
            ha="right", va="bottom")
    for i, (yr, label, g) in enumerate(EVENTS):
        y = n - 1 - i
        c = gcol[g]
        ax.plot([X0, yr], [y, y], color=th["grid"], lw=0.6, zorder=1)
        ax.plot(yr, y, "o", ms=6.5, color=c, zorder=4)
        side = -1 if yr > 1725 else 1
        ax.text(yr + side * 6, y, f"{label} · {yr}", fontsize=9, color=c,
                ha="right" if side < 0 else "left", va="center", zorder=5,
                bbox=dict(facecolor=th["bg"], edgecolor="none", pad=1.2))
    # the gap arrow
    ax.annotate("", xy=(1957, -1.7), xytext=(1896, -1.7),
                arrowprops=dict(arrowstyle="<->", color=th["grey"], lw=1))
    ax.text(1926.5, -2.35, "61 years: every physical ingredient in hand, "
            "no one who believed and no one who paid",
            fontsize=9, color=th["grey"], ha="center", style="italic")
    # legend
    for j, g in enumerate(["T", "H", "C", "W"]):
        x = 1548 + j * 108
        ax.plot(x, n + 0.9, "o", ms=6, color=gcol[g], clip_on=False)
        ax.text(x + 5, n + 0.9, GROUP_NAMES[g], fontsize=9, color=gcol[g],
                va="center")
    ax.set_xlim(X0, X1)
    ax.set_ylim(-2.9, n + 1.4)
    ax.set_yticks([])
    ax.set_xticks([1550, 1600, 1650, 1700, 1750, 1800, 1850, 1900, 1950])
    ax.tick_params(labelsize=9.5, length=0, pad=6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("The ingredient list: when each prerequisite for orbit arrived",
                 fontsize=15, loc="left", pad=16, fontweight="bold", color=th["fg"])
    ax.text(0, 1.008, "Every technology needed for an all-solid satellite launcher, "
            "by date of arrival. The list completes in 1896 — sixty-one years before "
            "anyone used it.", transform=ax.transAxes, fontsize=9.5,
            color=th["grey"], va="bottom")
    fig.savefig(f"{OUT}/rocket_ingredients{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

for theme in THEMES.values():
    plt.rcParams.update({
        "font.family": "Helvetica Neue",
        "text.color": theme["fg"],
        "xtick.color": theme["fg"],
        "ytick.color": theme["fg"],
    })
    fig_wall(theme)
    fig_price(theme)
    fig_ingredients(theme)
print("done")
