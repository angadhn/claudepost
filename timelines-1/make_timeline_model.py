"""
A pocket cliodynamics engine: technology arrival as a dependency graph.

Model
-----
Each technology i has:
  - prerequisite groups: AND of ORs — every group must be satisfied, a group is
    satisfied when ANY of its members has arrived (substitutability lives here)
  - a calibrated base lag L0_i = (real arrival year) - (year its last
    prerequisite group was historically satisfied)
  - arrival in a rollout:  t_i = gate_i + L0_i * exp(sigma*Z) / (V_i * C_i)
    where gate_i = max over groups (min over members), Z ~ N(0,1), and V
    (vision) and C (customer) are multipliers from the scenario's named rules,
    evaluated at gate time.

Scenario A applies no multipliers, so it reproduces real history by
construction (medians = real years); the counterfactuals differ from A only
through explicit, arguable rules. No global "progress speeds up" term: every
acceleration must be a named program or spillover you can dispute.

Scenarios
---------
A  as it happened (calibration)
B  the Victorian satellite (ch. 3): great-power rocket program from 1890
C  the sugar rocket (Angadh's draft): vision event 1250 — rocket candy
   conceived as a motor in the Mamluk/Song world; program + spillovers
D  scenario C with every steam node deleted (the "no steam engine" question)

Also modelled: the Essonne disaster (1788) as a coin-flip per rollout — heads,
chlorate fear triples the composite-propellant lag (history); tails, a
Woolwich composite appears decades early (fragility on the margins).

Outputs: timelines_data.js (the full graph + lags for the in-page simulator),
two static figures (arrival distributions; ablation criticality), and a
console table quoted in the essay.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)

SIGMA = 0.14
N_ROLL = 400
T0 = 1000
NEVER = 9999

THEMES = {
    "light": dict(suffix="", bg="#faf9f5", fg="#33312c", grey="#8a857c",
                  grid="#e7e4dc",
                  sc=dict(A="#8a857c", B="#9c453a", C="#2f629c", D="#2d7d52")),
    "dark":  dict(suffix="_dark", bg="#262624", fg="#e8e5de", grey="#a09a8e",
                  grid="#3a3833",
                  sc=dict(A="#a09a8e", B="#c25a3c", C="#5b8ed8", D="#3ba26b")),
}

BRANCHES = {
    "K": "knowledge & institutions", "P": "power", "M": "materials",
    "C": "chemistry", "F": "fabrication & precision",
    "I": "instruments & signals", "R": "rockets & flight",
}

# (id, label, branch, real year, prereq groups (AND of OR-lists), steam?)
NODES = [
    # start nodes: arrive at their year unconditionally
    ("fire_arrows",  "Fire arrows / war rockets (Song)",       "R", 950,  None, False),
    ("black_powder", "Black powder",                           "C", 950,  None, False),
    ("saltpetre",    "Saltpetre refining",                     "C", 1000, None, False),
    ("sugar",        "Industrial sugar refining",              "C", 1000, None, False),
    ("waterpower",   "Improved water/wind power",              "P", 1000, None, False),
    # rooted nodes (no prereqs; lag runs from T0)
    ("clocks",       "Mechanical clocks",                      "F", 1300, [], False),
    ("acids",        "Distilled mineral acids (alchemy)",      "C", 1300, [["saltpetre"]], False),
    ("blast_furnace","Blast furnace iron (Europe)",            "M", 1400, [], False),
    ("printing",     "Printing press",                         "K", 1450, [], False),
    ("telescope",    "Telescope",                              "I", 1608, [], False),
    # the lattice
    ("sci_method",   "Scientific method & societies",          "K", 1660, [["printing"]], False),
    ("glauber_acid", "Concentrated nitric acid (Glauber)",     "C", 1648, [["acids"]], False),
    ("clockwork",    "Precision clockwork (pendulum)",         "F", 1657, [["clocks"]], False),
    ("calculus",     "Calculus & Newtonian mechanics",         "K", 1687, [["sci_method"]], False),
    ("coke_iron",    "Coke-smelted iron",                      "M", 1709, [["blast_furnace"]], False),
    ("newcomen",     "Atmospheric steam engine (Newcomen)",    "P", 1712, [["barometer"], ["blast_furnace"]], True),
    ("crucible",     "Crucible steel",                         "M", 1740, [["coke_iron"]], False),
    ("lead_chamber", "Industrial acids (lead chamber)",        "C", 1746, [["acids"], ["sci_method"]], False),
    ("watt",         "Watt steam engine",                      "P", 1776, [["newcomen"], ["clockwork"]], True),
    ("chlorine",     "Chlorine isolated",                      "C", 1774, [["lead_chamber"]], False),
    ("mil_rockets",  "Iron-cased military rockets (Mysore)",   "R", 1780, [["fire_arrows"], ["blast_furnace"]], False),
    ("machine_tools","Machine tools (Maudslay)",               "F", 1800, [["crucible"], ["clockwork"]], False),
    ("hp_steam",     "High-pressure steam",                    "P", 1804, [["watt"], ["coke_iron"]], True),
    ("rocket_eq",    "Rocket equation (Moore)",                "R", 1813, [["calculus"], ["mil_rockets"]], False),
    ("perchlorate",  "Perchlorates isolated (Stadion)",        "C", 1816, [["chlorine"]], False),
    ("interchange",  "Interchangeable parts",                  "F", 1820, [["machine_tools"]], False),
    ("telegraph",    "Electric telegraph",                     "I", 1840, [["sci_method"], ["clockwork"]], False),
    ("spin",         "Spin stabilisation (Hale)",              "R", 1844, [["mil_rockets"]], False),
    ("nitrocell",    "Nitrocellulose",                         "C", 1846, [["lead_chamber"], ["sci_method"]], False),
    ("gauges",       "Precision gauges & micrometry",          "F", 1848, [["machine_tools"]], False),
    ("thermo",       "Thermodynamics",                         "K", 1850, [["calculus"], ["hp_steam", "sounding"]], False),
    ("gyroscope",    "Gyroscope (Foucault)",                   "I", 1852, [["clockwork"], ["machine_tools"]], False),
    ("bessemer",     "Cheap steel (Bessemer)",                 "M", 1856, [["coke_iron"], ["watt", "waterpower"]], False),
    ("electricity",  "Generators & electric power",            "P", 1870, [["sci_method"], ["machine_tools"]], False),
    ("ice",          "Internal combustion engine",             "P", 1876, [["machine_tools"], ["lead_chamber"]], False),
    ("smokeless",    "Smokeless powder (double-base)",         "C", 1884, [["nitrocell"]], False),
    ("delaval",      "Supersonic (de Laval) nozzle",           "R", 1888, [["hp_steam", "rocket_candy", "composite"]], False),
    ("gyro_auto",    "Gyroscopic autopilot (Obry)",            "I", 1895, [["gyroscope"], ["interchange"]], False),
    ("liquefaction", "Gas liquefaction (LOX)",                 "C", 1895, [["thermo"], ["gauges"], ["hp_steam", "ice"]], False),
    ("radio",        "Radio",                                  "I", 1896, [["telegraph"]], False),
    ("liquid_eng",   "Liquid rocket engine (Goddard)",         "R", 1926, [["liquefaction"], ["delaval"], ["gauges"]], False),
    ("sounding",     "High-altitude sounding rockets",         "R", 1933, [["smokeless", "composite", "rocket_candy"], ["delaval"], ["spin"]], False),
    ("composite",    "Castable composite propellant (Parsons)","C", 1942, [["perchlorate"], ["machine_tools"]], False),
    ("rocket_candy", "Rocket candy (sugar + saltpetre motor)", "C", 1943, [["sugar"], ["saltpetre"], ["fire_arrows"]], False),
    ("orbit",        "First satellite in orbit",               "R", 1957, [["sounding"], ["rocket_eq"], ["smokeless", "composite", "liquid_eng"], ["gyro_auto", "spin"], ["radio"]], False),
]
# barometer folded in late to keep the list tidy
NODES.insert(10, ("barometer", "Barometer & pressure science", "I", 1643, [["telescope"]], False))

IDX = {n[0]: n for n in NODES}
STEAM = [n[0] for n in NODES if n[5]]

def real(nid):
    return IDX[nid][3]

def gate_real(nid):
    """Year the node's last prerequisite group was historically satisfied."""
    _, _, _, yr, groups, _ = IDX[nid]
    if groups is None:
        return yr
    if not groups:
        return T0
    return max(min(real(m) for m in g) for g in groups)

L0 = {n[0]: max(real(n[0]) - gate_real(n[0]), 1) for n in NODES if n[4] is not None}

# ---------------------------------------------------------------- scenarios
# rule: dict(trigger=year | node id, targets=[branches and/or node ids], V, C)
SCENARIOS = {
    "A": dict(label="A · as it happened", rules=[], block=[]),
    "B": dict(label="B · the Victorian satellite (1890 program)", block=[],
              rules=[dict(trigger=1890, targets=["R"], V=4, C=3),
                     dict(trigger=1890, targets=["C"], V=1, C=1.5)]),
    "C": dict(label="C · the sugar rocket (1250 vision)", block=[],
              rules=[dict(trigger=1250, targets=["rocket_candy"], V=6, C=3),
                     dict(trigger="rocket_candy", targets=["R"], V=3, C=2),
                     dict(trigger="sounding", targets=["C"], V=1.5, C=2),
                     dict(trigger="sounding", targets=["F"], V=1, C=1.5),
                     dict(trigger="sounding", targets=["I"], V=1, C=1.5)]),
    "D": dict(label="D · sugar rocket, steam deleted", block=list(STEAM),
              rules=None),  # filled below: same rules as C
}
SCENARIOS["D"]["rules"] = SCENARIOS["C"]["rules"]

def arrival_time(nid, gate, work, active):
    """Integrate progress from `gate`: base rate 1, multiplied while programs
    that target this node are active. `active` = [(start_year, rule), ...]."""
    br = IDX[nid][2]
    starts = sorted(s for s, r in active
                    if s > gate and (br in r["targets"] or nid in r["targets"]))
    def rate_at(tt):
        v = 1.0
        for s, r in active:
            if s <= tt and (br in r["targets"] or nid in r["targets"]):
                v *= r["V"] * r["C"]
        return v
    t, remaining = gate, work
    for s in starts:
        seg = (s - t) * rate_at(t)
        if seg >= remaining:
            return t + remaining / rate_at(t)
        remaining -= seg
        t = s
    return t + remaining / rate_at(t)

def simulate(scenario, rng, essonne_luck=False, lags=None):
    """One rollout. Returns dict id -> arrival year (NEVER if unreachable)."""
    lags = lags or L0
    rules = scenario["rules"]
    blocked = set(scenario["block"])
    t = {}
    for nid, label, br, yr, groups, _ in NODES:
        if groups is None and nid not in blocked:
            t[nid] = yr
    pending = {n[0] for n in NODES if n[4] is not None and n[0] not in blocked}
    z = {nid: rng.standard_normal() for nid in pending}   # one draw per node
    # Essonne coin flip: tails -> chlorate fear never sets in, composite lag /3
    essonne_ok = essonne_luck and rng.random() < 0.5
    active = [(r["trigger"], r) for r in rules
              if isinstance(r["trigger"], (int, float))]
    fired = set()
    while True:
        best = None
        for nid in pending:
            groups = IDX[nid][4]
            gates = []
            ok = True
            for g in groups or []:
                opts = [t[m] for m in g if m in t]
                if not opts:
                    ok = False
                    break
                gates.append(min(opts))
            if not ok:
                continue
            gate = max(gates) if gates else T0
            work = lags[nid] * np.exp(SIGMA * z[nid])
            if nid == "composite" and essonne_ok:
                work /= 3.0
            arr = arrival_time(nid, gate, work, active)
            if best is None or arr < best[1]:
                best = (nid, arr)
        if best is None:
            break
        nid, arr = best
        t[nid] = arr
        pending.discard(nid)
        if nid not in fired:
            for r in rules:
                if r["trigger"] == nid:
                    active.append((arr, r))
            fired.add(nid)
    for nid in pending:
        t[nid] = NEVER
    return t

# ------------------------------------------------- calibrate lags iteratively
# Chained max() over noisy gates drifts arrivals late; shrink each lag until
# the baseline scenario's MEDIAN arrival matches the real year.
CAL = dict(L0)
for _ in range(14):
    rr = np.random.default_rng(3)
    runs = [simulate(SCENARIOS["A"], rr, lags=CAL) for _ in range(500)]
    for nid in CAL:
        med = float(np.median([t[nid] for t in runs]))
        target, gate = real(nid), gate_real(nid)
        if med > gate + 1:
            CAL[nid] = max(CAL[nid] * (target - gate) / (med - gate), 1.0)

def _run_collect(scn, n, essonne_luck):
    rr = np.random.default_rng(11)
    out = {nid: np.empty(n) for nid in IDX}
    for k in range(n):
        t = simulate(scn, rr, essonne_luck, lags=CAL)
        for nid, v in t.items():
            out[nid][k] = v
    return out

def q(a, p):
    a = a[a < NEVER]
    return float(np.quantile(a, p)) if len(a) else float("nan")

# ---------------------------------------------------------------- console
MARQUEE = ["rocket_candy", "delaval", "sounding", "smokeless", "radio", "orbit"]
RESULTS = {k: _run_collect(SCENARIOS[k], N_ROLL, False) for k in "ABCD"}
print(f"{'node':14s}" + "".join(f"{k:>16s}" for k in "ABCD"))
for nid in MARQUEE:
    row = f"{nid:14s}"
    for k in "ABCD":
        a = RESULTS[k][nid]
        alive = a[a < NEVER]
        row += (f"{q(a,.5):8.0f} ({q(a,.25):.0f}–{q(a,.75):.0f})"[:16].rjust(16)
                if len(alive) else f"{'never':>16s}")
    print(row)

# ---------------------------------------------- fig 1: arrival distributions
def fig_dist(th):
    fig, axes = plt.subplots(1, len(MARQUEE), figsize=(13, 5.4), sharey=True)
    fig.patch.set_facecolor(th["bg"])
    names = {"rocket_candy": "rocket candy", "delaval": "de Laval nozzle",
             "sounding": "sounding rockets", "smokeless": "smokeless powder",
             "radio": "radio", "orbit": "ORBIT"}
    for ax, nid in zip(axes, MARQUEE):
        ax.set_facecolor(th["bg"])
        for gy in (1200, 1400, 1600, 1800):
            ax.axhline(gy, color=th["grid"], lw=0.7, zorder=0)
        ax.axhline(real(nid), color=th["grey"], lw=0.8, ls=(0, (3, 3)), zorder=1)
        for x, k in enumerate("ABCD"):
            a = RESULTS[k][nid]
            alive = a[a < NEVER]
            col = th["sc"][k]
            if not len(alive):
                ax.text(x, 1080, "×", fontsize=13, color=col, ha="center")
                continue
            lo, mid, hi = q(a, .1), q(a, .5), q(a, .9)
            ax.plot([x, x], [lo, hi], color=col, lw=2.2, solid_capstyle="round")
            ax.plot([x, x], [q(a, .25), q(a, .75)], color=col, lw=5.5,
                    alpha=.45, solid_capstyle="butt")
            ax.plot(x, mid, "o", ms=6.5, color=col)
            left = k in ("A", "C")
            ax.annotate(f"{mid:.0f}", (x, mid), xytext=(-8 if left else 8, 0),
                        textcoords="offset points", fontsize=8, color=col,
                        va="center", ha="right" if left else "left")
        ax.set_xlim(-0.7, 3.9)
        ax.set_ylim(2010, 1040)          # time flows downward: earlier = higher
        ax.set_xticks(range(4))
        ax.set_xticklabels(list("ABCD"), fontsize=9)
        ax.set_title(names[nid], fontsize=10.5, color=th["fg"],
                     fontweight="bold" if nid == "orbit" else "normal", pad=8)
        ax.tick_params(labelsize=8.5, length=0, pad=4)
        for s in ax.spines.values():
            s.set_visible(False)
    axes[0].set_yticks([1100, 1300, 1500, 1700, 1900, 2000])
    fig.suptitle("When each milestone arrives, by timeline (400 rollouts each)",
                 fontsize=15, x=0.065, ha="left", fontweight="bold", color=th["fg"])
    fig.text(0.065, 0.905, "Dot: median · thick bar: middle half of rollouts · thin bar: 10th–90th "
             "percentile · dashed grey: what actually happened. A calibrated; B Victorian "
             "program (1890); C sugar-rocket vision (1250); D = C with no steam engine, ever.",
             fontsize=9.5, color=th["grey"])
    fig.subplots_adjust(top=0.82, bottom=0.06, left=0.065, right=0.985, wspace=0.12)
    fig.savefig(f"{OUT}/timeline_dist{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# --------------------------------------------------- fig 2: ablation study
ABLATE = [
    ("printing",      "printing press"),
    ("calculus",      "calculus & Newton"),
    ("blast_furnace", "blast furnace"),
    ("machine_tools", "machine tools"),
    ("lead_chamber",  "industrial acids"),
    ("smokeless",     "smokeless powder"),
    ("delaval",       "de Laval nozzle"),
    ("gyro_auto",     "gyro autopilot"),
    ("radio",         "radio"),
    ("STEAM",         "steam engines (all)"),
]

def fig_ablate(th):
    base = q(RESULTS["A"]["orbit"], .5)
    rows = []
    for nid, label in ABLATE:
        extra = STEAM if nid == "STEAM" else [nid]
        res = _run_collect(dict(SCENARIOS["A"], block=extra), 200, False)
        a = res["orbit"]
        alive = a[a < NEVER]
        rows.append((label, q(a, .5) - base if len(alive) else None))
    fig, ax = plt.subplots(figsize=(13, 5.8))
    fig.patch.set_facecolor(th["bg"])
    ax.set_facecolor(th["bg"])
    ys = np.arange(len(rows))[::-1]
    for gx in (50, 100, 150):
        ax.axvline(gx, color=th["grid"], lw=0.7, zorder=0)
    for (label, d), y in zip(rows, ys):
        if d is None:
            ax.text(4, y, f"{label} — orbit never arrives", fontsize=10,
                    color=th["sc"]["B"], va="center", fontweight="medium")
        else:
            d = max(d, 0)
            ax.barh(y, max(d, 0.8), height=0.52, color=th["sc"]["C"], alpha=0.85)
            ax.text(max(d, 0.8) + 3, y, f"{label} · +{d:.0f} yr", fontsize=10,
                    color=th["fg"], va="center")
    ax.set_xlim(0, 185)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_yticks([])
    ax.set_xticks([0, 50, 100, 150])
    ax.set_xticklabels(["0", "+50 yr", "+100 yr", "+150 yr"])
    ax.tick_params(labelsize=9.5, length=0, pad=6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Delete one technology from real history: how late is the first satellite?",
                 fontsize=15, loc="left", pad=16, fontweight="bold", color=th["fg"])
    ax.text(0, 1.015, "Median delay of ORBIT vs the calibrated 1957, when the named node is "
            "removed and every substitute path (eq. 4.1's OR groups) must carry the load. "
            "Nodes in red have no substitute in the model at all.",
            transform=ax.transAxes, fontsize=9.5, color=th["grey"], va="bottom")
    fig.savefig(f"{OUT}/timeline_ablate{th['suffix']}.png", dpi=200,
                bbox_inches="tight", facecolor=th["bg"])
    plt.close(fig)

# ---------------------------------------------------------------- JS export
def export_js():
    nodes = []
    for nid, label, br, yr, groups, steam in NODES:
        nodes.append(dict(id=nid, label=label, br=br, real=yr,
                          groups=groups, steam=steam,
                          L0=round(CAL[nid], 2) if nid in CAL else None,
                          start=groups is None))
    payload = dict(T0=T0, NEVER=NEVER, sigma=SIGMA, branches=BRANCHES,
                   nodes=nodes, steam=STEAM,
                   scenarios={k: dict(label=v["label"], rules=v["rules"],
                                      block=v["block"])
                              for k, v in SCENARIOS.items()})
    with open(f"{OUT}/timelines_data.js", "w") as f:
        f.write("// Generated by make_timeline_model.py — do not edit by hand.\n")
        f.write("const TL = " + json.dumps(payload, ensure_ascii=False) + ";\n")

for theme in THEMES.values():
    plt.rcParams.update({
        "font.family": "Helvetica Neue",
        "text.color": theme["fg"],
        "xtick.color": theme["fg"],
        "ytick.color": theme["fg"],
    })
    fig_dist(theme)
    fig_ablate(theme)
export_js()
print("done")
