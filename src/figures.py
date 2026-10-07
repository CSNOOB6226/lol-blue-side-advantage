"""
Publication figures. Reads results/*.csv (and the derived table for the by-year blue
ORs) and writes PNGs to figures/. Bilingual (中文 + English) titles.

  fig1_forest_draft_value.png   core result: every draft lever hugs OR=1; only blue departs
  fig2_blue_or_by_year.png      5-year stability of the blue OR (no 2026 structural break)
  fig3_did_eventstudy.png       DiD event study + parallel-trends check
  fig4_mediation_channels.png   blue-side edge decomposed by channel (2026, bootstrap CI)
  fig5_herald_engine_trend.png  herald (engine, +) vs dragon (suppressor, -) over 2022-2026
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
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

import config as cfg
from utils import load_teamgames, logit_cluster, or_ci

RES, FIG = cfg.RESULTS_DIR, cfg.FIGURES_DIR
RED, DARK, GREY, BLUE = "#c0392b", "#2c3e50", "#95a5a6", "#2e86de"


def fig1_forest():
    r = pd.read_csv(os.path.join(RES, "draft_value_ORs.csv"))
    blue = r[r.group == "side_year"]                      # blue-only estimates
    fp = r[(r.label == "First pick priority")]
    cp = r[r.group == "draft"]
    order = ["Blue side (map)", "First pick priority",
             "Counterpick top", "Counterpick jng", "Counterpick mid",
             "Counterpick bot", "Counterpick sup"]
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    ypos, yt, yl = 0, [], []
    for lab in order:
        sub = pd.concat([blue, fp, cp])
        sub = sub[sub.label == lab]
        centers = []
        for _, row in sub.sort_values("year").iterrows():
            is_side = "Blue" in lab
            col = RED if is_side else (DARK if row.year == 2026 else GREY)
            mk = "o" if row.year == 2026 else "s"
            ax.plot([row.lo, row.hi], [ypos, ypos], color=col, lw=1.8, zorder=2)
            ax.scatter([row.OR], [ypos], color=col, marker=mk, s=52, zorder=3)
            centers.append(ypos)
            ypos -= 1
        yt.append(np.mean(centers)); yl.append(lab)
        ypos -= 0.5
    ax.axvline(1.0, color="k", ls="--", lw=1, zorder=1)
    ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=11)
    ax.set_xscale("log")
    ax.set_xticks([0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4])
    ax.set_xticklabels(["0.8", "0.9", "1.0", "1.1", "1.2", "1.3", "1.4"])
    ax.set_xlabel("胜率优势比 Win Odds Ratio (95% CI) — per SD later reveal / vs baseline", fontsize=11)
    ax.set_title("赢得BP ≠ 赢得比赛：选秀优势不转化为胜利，唯蓝色方(地图侧)有效\n"
                 "Winning the draft ≠ winning the game — non-China pro LoL 2025–2026\n"
                 "(counter-pick family: 0/10 significant, 0/10 survive FDR)", fontsize=11)
    from matplotlib.lines import Line2D
    leg = [Line2D([0], [0], marker="o", color="w", markerfacecolor=DARK, markersize=9, label="2026"),
           Line2D([0], [0], marker="s", color="w", markerfacecolor=GREY, markersize=9, label="2025"),
           Line2D([0], [0], marker="o", color="w", markerfacecolor=RED, markersize=9, label="Blue side (map)")]
    ax.legend(handles=leg, loc="lower right", fontsize=9, framealpha=0.9)
    ax.text(1.008, yt[0] + 0.4, "OR=1\n无效 no effect", fontsize=8, va="bottom")
    plt.tight_layout()
    _save(fig, "fig1_forest_draft_value.png")


def fig2_blue_by_year():
    d = load_teamgames()
    rows = []
    for y in sorted(d.year.unique()):
        s = d[d.year == y].dropna(subset=["result", "blue"])
        OR, lo, hi, p = or_ci(logit_cluster("result ~ blue", s), "blue")
        rows.append((y, OR, lo, hi))
    df = pd.DataFrame(rows, columns=["year", "OR", "lo", "hi"])
    df.to_csv(os.path.join(RES, "blue_or_by_year.csv"), index=False)
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.errorbar(df.year, df.OR, yerr=[df.OR - df.lo, df.hi - df.OR],
                fmt="o-", color=BLUE, ecolor=BLUE, capsize=4, lw=2, ms=8)
    ax.axhline(1.0, color="k", ls="--", lw=1)
    ax.axvspan(2025.5, 2026.5, color=RED, alpha=0.08)
    ax.text(2026, df.OR.min() - 0.02, "First Selection\n新规 (2026)", color=RED,
            ha="center", va="top", fontsize=9)
    for _, r in df.iterrows():
        ax.annotate(f"{r.OR:.2f}", (r.year, r.hi), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=9)
    ax.set_xticks(df.year.astype(int))
    ax.set_ylabel("蓝色方胜率优势比 Blue-side win OR", fontsize=11)
    ax.set_title("蓝色方优势跨五年稳定，2026新规后无结构性下降\n"
                 "Blue-side advantage is stable 2022–2026; no break after First Selection",
                 fontsize=11.5)
    plt.tight_layout()
    _save(fig, "fig2_blue_or_by_year.png")


def fig3_did():
    es = pd.read_csv(os.path.join(RES, "did_eventstudy.csv")).sort_values("year")
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    pre = es[es.year <= 2025]; post = es[es.year == 2026]
    ax.errorbar(pre.year, pre.coef, yerr=[pre.coef - pre.lo, pre.hi - pre.coef],
                fmt="s-", color=DARK, capsize=4, lw=1.8, ms=7, label="pre / reference")
    ax.errorbar(post.year, post.coef, yerr=[post.coef - post.lo, post.hi - post.coef],
                fmt="o", color=RED, capsize=4, ms=10, label="treatment year (2026)")
    ax.axhline(0.0, color="k", ls="--", lw=1)
    ax.set_xticks(es.year.astype(int))
    ax.set_ylabel("解耦×年 对蓝方优势的影响 (pp)\nDiD coef: decoupling × year on blue adv.", fontsize=10)
    ax.set_title("First Selection 的DiD事件研究：2026无削弱效应(甚至为正)\n"
                 "Did First Selection reduce blue advantage? DiD event study — no (point estimate +)\n"
                 "note: 2024 already elevated ⇒ imperfect parallel trends, read as suggestive",
                 fontsize=10.5)
    ax.legend(fontsize=9, loc="upper left")
    plt.tight_layout()
    _save(fig, "fig3_did_eventstudy.png")


def fig4_mediation_channels():
    m = pd.read_csv(os.path.join(RES, "mediation_path.csv"))
    m26 = m[m.year == 2026].copy()
    label_map = {"firstherald": "首先锋 herald\n(engine +)", "firstdragon": "首龙 dragon\n(suppressor −)",
                 "z_gold15": "15min经济 gold", "firsttower": "首塔 tower",
                 "direct_residual": "残差 direct\n(map, unmeasured)"}
    m26 = m26[m26.channel.isin(label_map)]
    m26["lab"] = m26.channel.map(label_map)
    order = ["firstherald", "firstdragon", "z_gold15", "firsttower", "direct_residual"]
    m26 = m26.set_index("channel").loc[order].reset_index()
    cols = [RED if v < 0 else BLUE for v in m26.indirect_pp]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.bar(m26.lab, m26.indirect_pp, color=cols, alpha=0.85,
           yerr=[m26.indirect_pp - m26.ci_lo, m26.ci_hi - m26.indirect_pp],
           capsize=4)
    ax.axhline(0, color="k", lw=1)
    for i, v in enumerate(m26.indirect_pp):
        ax.text(i, v + (0.15 if v >= 0 else -0.15), f"{v:+.1f}", ha="center",
                va="bottom" if v >= 0 else "top", fontsize=9)
    ax.set_ylabel("对蓝方胜率优势的贡献 (pp)\ncontribution to blue win edge (pp)", fontsize=10)
    ax.set_title("蓝方优势的路径分解 (2026, 自助法95%CI)：先锋是引擎，龙是抑制器\n"
                 "Path decomposition of the blue-side edge (2026, bootstrap 95% CI)",
                 fontsize=11)
    plt.tight_layout()
    _save(fig, "fig4_mediation_channels.png")


def fig5_herald_trend():
    m = pd.read_csv(os.path.join(RES, "mediation_path.csv"))
    h = m[m.channel == "firstherald"].sort_values("year")
    dr = m[m.channel == "firstdragon"].sort_values("year")
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.plot(h.year, h.indirect_pp, "o-", color=BLUE, lw=2, ms=8, label="首先锋 herald (engine +)")
    ax.plot(dr.year, dr.indirect_pp, "s-", color=RED, lw=2, ms=8, label="首龙 dragon (suppressor −)")
    ax.axhline(0, color="k", ls="--", lw=1)
    ax.set_xticks(h.year.astype(int))
    ax.set_ylabel("间接贡献 indirect effect (pp)", fontsize=11)
    ax.set_title("首先锋(上半区)是引擎且逐年增强；首龙始终为负(抑制器)\n"
                 "Herald (top-side) is the engine and grows; dragon stays negative",
                 fontsize=11.5)
    ax.legend(fontsize=9)
    plt.tight_layout()
    _save(fig, "fig5_herald_engine_trend.png")


def fig6_equivalence():
    e = pd.read_csv(os.path.join(RES, "equivalence_tost.csv"))
    lo_b, hi_b = 1/1.10, 1.10
    # order: blue (contrast) at top, then first pick, then counterpicks
    e["ord"] = e.param.apply(lambda s: 0 if "Blue" in s else (1 if "First" in s else 2))
    e = e.sort_values(["ord", "param"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    ax.axvspan(lo_b, hi_b, color="#2ecc71", alpha=0.12, label="equivalence band (±10% odds)")
    ax.axvline(1.0, color="k", ls="--", lw=1)
    for i, r in e.iterrows():
        is_blue = "Blue" in r.param
        col = RED if is_blue else (DARK if r.equivalent_10 else "#e67e22")
        ax.plot([r.ci90_lo, r.ci90_hi], [i, i], color=col, lw=2, zorder=3)
        ax.scatter([r.OR], [i], color=col, s=46, zorder=4)
    ax.set_yticks(range(len(e))); ax.set_yticklabels(e.param, fontsize=9)
    ax.invert_yaxis()
    ax.set_xscale("log"); ax.set_xticks([0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3])
    ax.set_xticklabels(["0.85", "0.9", "0.95", "1.0", "1.05", "1.1", "1.2", "1.3"])
    ax.set_xlabel("Win OR with 90% CI (TOST)  — inside green band ⇒ equivalent to null", fontsize=10)
    ax.set_title("等价检验：选秀杠杆的90%CI落在±10%无效带内(证明可忽略)，唯蓝方越界\n"
                 "Equivalence (TOST): draft levers fall inside the negligibility band; blue side does not",
                 fontsize=11)
    ax.legend(loc="lower right", fontsize=9)
    plt.tight_layout()
    _save(fig, "fig6_equivalence_tost.png")


def fig7_matchup():
    m = pd.read_csv(os.path.join(RES, "matchup_quality.csv"))
    order = ["top", "jng", "mid", "bot", "sup"]
    m = m.set_index("role").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    y = np.arange(len(m))
    ax.scatter(m.mq_or, y + 0.12, color=BLUE, s=70, zorder=3, label="drafted match-up → win (OR/SD)")
    ax.scatter(m.gap_or_ctrl, y - 0.12, color="#e67e22", marker="s", s=60, zorder=3,
               label="reveal timing → win, ctrl match-up (OR/SD)")
    ax.axvline(1.0, color="k", ls="--", lw=1)
    ax.set_yticks(y); ax.set_yticklabels(order); ax.invert_yaxis()
    ax.set_xlabel("Win Odds Ratio per SD", fontsize=11)
    ax.set_title("对位质量能预测胜负，后手时机不能（控制对位后仍≈1）\n"
                 "Match-up quality predicts wins; counter-pick timing does not (internal OE control)",
                 fontsize=11)
    ax.legend(fontsize=9, loc="lower right")
    plt.tight_layout()
    _save(fig, "fig7_matchup_vs_timing.png")


def _save(fig, name):
    out = os.path.join(FIG, name)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", os.path.relpath(out, cfg.REPO_ROOT))


def main():
    fig1_forest()
    fig2_blue_by_year()
    fig3_did()
    fig4_mediation_channels()
    fig5_herald_trend()
    fig6_equivalence()
    fig7_matchup()
    print("All figures written to figures/")


if __name__ == "__main__":
    main()
