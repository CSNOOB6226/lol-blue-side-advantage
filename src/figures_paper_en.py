"""
English, publication-quality figures for the MIT Sloan SSAC paper submission.

Two figures, chosen to tell the whole story within SSAC's 2-figure abstract limit:
  fig_en1  blue-side odds ratio by season -> the advantage is stable and the 2026
           reform year shows no structural break
  fig_en2  path decomposition with bootstrap CIs -> the herald engine / dragon
           suppressor asymmetry plus the unexplained residual

Palette is the validated default (blue #2a78d6 / red #e34948): CVD-checked with
scripts/validate_palette.js (worst-pair protan ΔE 21.6, normal-vision ΔE 32.3,
both well above the gates). Blue/red here encode POLARITY (positive vs negative
contribution), not category.

Output: figures/en/*.png at 300 dpi.
"""
from __future__ import annotations
import os, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime import configure_matplotlib_env

configure_matplotlib_env(Path(__file__).resolve().parents[1])

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config as cfg
from utils import load_teamgames, logit_cluster, or_ci

OUT = os.path.join(cfg.FIGURES_DIR, "en")
os.makedirs(OUT, exist_ok=True)

BLUE, RED = "#2a78d6", "#e34948"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8985"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.8,
    "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 300, "savefig.dpi": 300,
})


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", os.path.relpath(p, cfg.REPO_ROOT))


def fig1_or_by_season():
    d = load_teamgames()
    rows = []
    for y in sorted(d.year.unique()):
        s = d[d.year == y].dropna(subset=["result", "blue"])
        OR, lo, hi, p = or_ci(logit_cluster("result ~ blue", s), "blue")
        rows.append((int(y), OR, lo, hi, s.gameid.nunique()))
    df = pd.DataFrame(rows, columns=["year", "OR", "lo", "hi", "games"])

    fig, ax = plt.subplots(figsize=(7.2, 4.3))

    # reform-year band, recessive
    ax.axvspan(2025.55, 2026.45, color=MUTED, alpha=0.10, lw=0, zorder=0)
    ax.axhline(1.0, color=MUTED, ls=(0, (4, 3)), lw=1, zorder=1)
    ax.text(2021.72, 1.006, "no advantage (OR = 1)", fontsize=8.5, color=MUTED,
            va="bottom", ha="left")

    ax.errorbar(df.year, df.OR, yerr=[df.OR - df.lo, df.hi - df.OR],
                fmt="o-", color=BLUE, ecolor=BLUE, elinewidth=1.6,
                capsize=3.5, capthick=1.2, lw=2, ms=8, zorder=3,
                markeredgecolor="white", markeredgewidth=1.2)

    # selective direct labels: endpoints + the reform year
    for _, r in df.iterrows():
        emph = r.year in (2022, 2026)
        ax.annotate(f"{r.OR:.2f}", (r.year, r.hi), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9.5 if emph else 9,
                    color=INK if emph else INK2,
                    fontweight="bold" if emph else "normal")

    ax.annotate("“First Selection” reform\n(side choice decoupled\nfrom draft priority)",
                xy=(2026, df.lo.iloc[-1]), xytext=(2025.4, 1.075),
                fontsize=8.8, color=INK2, ha="center", va="top",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9,
                                connectionstyle="arc3,rad=0.2"))

    ax.set_xticks(df.year)
    ax.set_xlim(2021.6, 2026.6)
    ax.set_ylim(0.98, 1.50)
    ax.set_ylabel("Blue-side win odds ratio\n(95% CI, SE clustered by game)", fontsize=10.5)
    ax.set_xlabel("Season", fontsize=10.5)
    ax.set_title("The blue-side advantage is stable across five seasons —\n"
                 "and the 2026 reform year shows no structural break",
                 fontsize=12, color=INK, loc="left", pad=12)
    ax.grid(axis="y", color=MUTED, alpha=0.18, lw=0.7)
    ax.set_axisbelow(True)
    fig.text(0.125, -0.035,
             f"n = {df.games.sum():,} games, 80 non-Chinese leagues (Oracle's Elixir). "
             "All five odds ratios p < 0.001.",
             fontsize=8.5, color=MUTED, ha="left")
    save(fig, "fig_en1_blue_or_by_season.png")
    return df


def fig2_path_decomposition():
    m = pd.read_csv(os.path.join(cfg.RESULTS_DIR, "mediation_path.csv"))
    m = m[m.year == 2026]
    order = ["firstherald", "firstdragon", "z_gold15", "firsttower", "direct_residual"]
    # identity carried by the labels themselves (direct labeling beats a legend box):
    # sign is encoded three ways — side of zero, signed value, and colour.
    labels = {
        "firstherald": "First herald\n(top side) — helps blue",
        "firstdragon": "First dragon\n(bottom side) — suppressor",
        "z_gold15": "Gold lead\nat 15 min — helps blue",
        "firsttower": "First tower\n— helps blue",
        "direct_residual": "Unexplained\nresidual",
    }
    m = m.set_index("channel").loc[order].reset_index()

    fig, ax = plt.subplots(figsize=(7.6, 4.5))
    y = np.arange(len(m))[::-1]
    colors = [RED if v < 0 else BLUE for v in m.indirect_pp]

    ax.barh(y, m.indirect_pp, height=0.58, color=colors, zorder=3,
            edgecolor="white", linewidth=1.2)
    ax.errorbar(m.indirect_pp, y,
                xerr=[m.indirect_pp - m.ci_lo, m.ci_hi - m.indirect_pp],
                fmt="none", ecolor=INK2, elinewidth=1.3, capsize=3.5,
                capthick=1.1, zorder=4)
    ax.axvline(0, color=INK, lw=1, zorder=5)

    for yi, v, lo, hi in zip(y, m.indirect_pp, m.ci_lo, m.ci_hi):
        off = 0.16 if v >= 0 else -0.16
        ax.text(hi + off if v >= 0 else lo + off, yi,
                f"{v:+.1f} pp".replace("-", "−"), va="center",
                ha="left" if v >= 0 else "right",
                fontsize=9.5, color=INK, fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels([labels[c] for c in m.channel], fontsize=9.5)
    ax.set_xlabel("Contribution to blue-side win probability (percentage points)\n"
                  "with 95% cluster-bootstrap CI", fontsize=10.5)
    ax.set_xlim(-3.4, 4.6)
    ax.set_title("Blue wins through the top side — while conceding the bottom side\n"
                 "Path decomposition of the +5.2 pp blue-side edge (2026)",
                 fontsize=12, color=INK, loc="left", pad=12)
    ax.grid(axis="x", color=MUTED, alpha=0.18, lw=0.7)
    ax.set_axisbelow(True)

    fig.text(0.125, -0.04,
             "Blue concedes the first dragon (−1.9 pp) yet still nets +5.2 pp. "
             "The residual persists when the full pre-15-minute state is added.",
             fontsize=8.5, color=MUTED, ha="left")
    save(fig, "fig_en2_path_decomposition.png")


def fig3_forest_draft_levers():
    """Forest plot: every draft lever against the blue-side benchmark."""
    r = pd.read_csv(os.path.join(cfg.RESULTS_DIR, "draft_value_ORs.csv"))
    by_year = pd.read_csv(os.path.join(cfg.RESULTS_DIR, "blue_or_by_year.csv"))
    rows = []
    for _, x in by_year.sort_values("year").iterrows():
        rows.append((f"Blue side ({int(x.year)})", x.OR, x.lo, x.hi, "side"))
    fp = r[r.label == "First pick priority"].iloc[0]
    rows.append(("First-pick priority (2026)", fp.OR, fp.lo, fp.hi, "draft"))
    cp = r[(r.group == "draft") & (r.label.str.startswith("Counterpick"))]
    for _, x in cp.sort_values(["year", "label"]).iterrows():
        role = x.label.replace("Counterpick ", "")
        rows.append((f"Counter-pick {role} ({int(x.year)})", x.OR, x.lo, x.hi, "draft"))
    df = pd.DataFrame(rows, columns=["label", "OR", "lo", "hi", "grp"])

    fig, ax = plt.subplots(figsize=(7.4, 6.6))
    y = np.arange(len(df))[::-1]
    for yi, (_, x) in zip(y, df.iterrows()):
        col = BLUE if x.grp == "side" else INK2
        ax.plot([x.lo, x.hi], [yi, yi], color=col, lw=1.7, solid_capstyle="round", zorder=3)
        ax.scatter([x.OR], [yi], color=col, s=34, zorder=4,
                   marker="o" if x.grp == "side" else "s",
                   edgecolor="white", linewidth=0.8)
    ax.axvline(1.0, color=MUTED, ls=(0, (4, 3)), lw=1, zorder=1)
    ax.set_yticks(y); ax.set_yticklabels(df.label, fontsize=9.5)
    ax.set_xscale("log")
    ticks = [0.85, 0.9, 0.95, 1.0, 1.1, 1.2, 1.3, 1.45]
    ax.set_xticks(ticks); ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.set_xticks([], minor=True)          # log minor ticks would overprint the labels
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlim(0.82, 1.5)
    ax.set_xlabel("Win odds ratio (95% CI, log scale)\n"
                  "draft levers: per SD of reveal gap · side: blue vs red", fontsize=10)
    ax.set_title("Draft-timing levers cluster at OR = 1; only map side departs from it",
                 fontsize=11.5, color=INK, loc="left", pad=10)
    ax.grid(axis="x", color=MUTED, alpha=0.16, lw=0.7); ax.set_axisbelow(True)
    fig.text(0.125, -0.03,
             "Blue-side estimates in blue circles; draft levers in dark squares. "
             "SE clustered by game.", fontsize=8.5, color=MUTED, ha="left")
    save(fig, "fig_en3_forest_draft_levers.png")


def fig4_tost():
    """Equivalence bands: draft levers inside the ±10% odds region, side outside it."""
    e = pd.read_csv(os.path.join(cfg.RESULTS_DIR, "equivalence_tost.csv"))
    e["ord"] = e.param.apply(lambda s: 0 if "Blue" in s else (1 if "First" in s else 2))
    e = e.sort_values(["ord", "param"]).reset_index(drop=True)
    lo_b, hi_b = 1 / 1.10, 1.10

    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    ax.axvspan(lo_b, hi_b, color=BLUE, alpha=0.07, lw=0, zorder=0)
    ax.axvline(1.0, color=MUTED, ls=(0, (4, 3)), lw=1, zorder=1)
    y = np.arange(len(e))[::-1]
    for yi, (_, x) in zip(y, e.iterrows()):
        col = RED if not x.equivalent_10 else INK2
        ax.plot([x.ci90_lo, x.ci90_hi], [yi, yi], color=col, lw=1.7,
                solid_capstyle="round", zorder=3)
        ax.scatter([x.OR], [yi], color=col, s=34, zorder=4,
                   edgecolor="white", linewidth=0.8)
    ax.set_yticks(y); ax.set_yticklabels(e.param, fontsize=9.5)
    ax.set_xscale("log")
    ticks = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.35]
    ax.set_xticks(ticks); ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.set_xticks([], minor=True)
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlim(0.82, 1.42)
    ax.set_xlabel("Odds ratio with 90% CI (log scale)\n"
                  "shaded band = pre-specified ±10% practical-equivalence region", fontsize=10)
    ax.set_title("Equivalence tests: ten counter-pick estimates fall inside the\n"
                 "negligibility band; first-pick and map side do not",
                 fontsize=11.5, color=INK, loc="left", pad=10)
    ax.grid(axis="x", color=MUTED, alpha=0.16, lw=0.7); ax.set_axisbelow(True)
    fig.text(0.125, -0.035,
             "Red = not shown equivalent (TOST p > 0.05). A 90% CI lying entirely inside the "
             "band establishes equivalence at α = 0.05.", fontsize=8.5, color=MUTED, ha="left")
    save(fig, "fig_en4_equivalence_tost.png")


def fig5_did_event_study():
    es = pd.read_csv(os.path.join(cfg.RESULTS_DIR, "did_eventstudy.csv")).sort_values("year")
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    pre, post = es[es.year <= 2025], es[es.year == 2026]
    ax.errorbar(pre.year, pre.coef, yerr=[pre.coef - pre.lo, pre.hi - pre.coef],
                fmt="s-", color=INK2, ecolor=INK2, elinewidth=1.4, capsize=3.5,
                lw=1.6, ms=7, zorder=3, markeredgecolor="white", markeredgewidth=1)
    ax.errorbar(post.year, post.coef, yerr=[post.coef - post.lo, post.hi - post.coef],
                fmt="o", color=RED, ecolor=RED, elinewidth=1.6, capsize=3.5,
                ms=9, zorder=4, markeredgecolor="white", markeredgewidth=1.1)
    ax.axhline(0, color=MUTED, ls=(0, (4, 3)), lw=1, zorder=1)
    ax.annotate("reference\nseason", xy=(2025, 0), xytext=(2025, -6.4),
                fontsize=8.5, color=MUTED, ha="center", va="top")
    ax.annotate("post-reform", xy=(2026, post.coef.iloc[0]), xytext=(2026, 15.5),
                fontsize=8.8, color=RED, ha="center", va="bottom")
    ax.annotate("pre-period coefficient already\nelevated in 2024",
                xy=(2024, es[es.year == 2024].coef.iloc[0]), xytext=(2022.75, 13.0),
                fontsize=8.5, color=INK2, ha="left", va="bottom",
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.9,
                                connectionstyle="arc3,rad=-0.25"))
    ax.set_xticks(es.year.astype(int))
    ax.set_ylim(-9.5, 18.5)
    ax.set_ylabel("Adoption intensity × season\n(pp of blue-side advantage)", fontsize=10)
    ax.set_xlabel("Season", fontsize=10.5)
    ax.set_title("Event study: no reduction after the reform, and pre-trends are not flat",
                 fontsize=11.5, color=INK, loc="left", pad=10)
    ax.grid(axis="y", color=MUTED, alpha=0.16, lw=0.7); ax.set_axisbelow(True)
    fig.text(0.125, -0.035,
             "League × season panel, 24 leagues, 109 league-years; league and season fixed "
             "effects; SE clustered by league.", fontsize=8.5, color=MUTED, ha="left")
    save(fig, "fig_en5_did_event_study.png")


def main():
    df = fig1_or_by_season()
    print(df.to_string(index=False))
    fig2_path_decomposition()
    fig3_forest_draft_levers()
    fig4_tost()
    fig5_did_event_study()
    print(f"\nEnglish paper figures written to {os.path.relpath(OUT, cfg.REPO_ROOT)}/")


if __name__ == "__main__":
    main()
