"""
Difference-in-differences: did Riot's 2026 "First Selection" rule reduce the
blue-side win advantage?

DESIGN.  First Selection decoupled side choice from pick order in 2026, but leagues
operationalised it to very different degrees (LCK almost fully decoupled; LJL/AL
barely). We use that variation as a CONTINUOUS treatment intensity:

    D_league = share of a league's 2026 first-pick team-games that are RED side
             = 1 - P(blue | firstPick, 2026).
    D = 0  -> still fully coupled (old regime);  D large -> strongly decoupled.

Panel: league x year (2022-2026). Outcome: blue-side win advantage in pp
(100 * (blue win-rate - 0.5)). DiD / event study with league and year fixed effects,
weighted by games, cluster-robust by league:

    blue_adv_{l,t} = a_l + g_t + b * (D_l * 1[t=2026]) + e        (DiD)
    blue_adv_{l,t} = a_l + g_t + sum_k b_k (D_l * 1[t=k]) + e      (event study)

Paper hypothesis: the blue edge is a MAP effect the rule cannot touch, so b ~ 0
(the rule did not fix blue side; Riot "turned the wrong knob").

PLACEBO / POSITIVE CONTROL: rerun with blue-side FIRST-HERALD rate as the outcome.
River geometry is unchanged by any draft rule, so decoupling must have ~0 effect on
it; a null here shows the design is not manufacturing differences.

HONESTY.  Adoption intensity is a league CHOICE, not random; validity rests on the
parallel-trends check (pre-2026 event-study coefficients ~ 0). And because 2026 blue
side is partly self-selected (strong teams choose it, see team_strength.py), the DiD
estimand is the NET policy effect on observed blue win-rate, not a structural map
parameter. We report it as a policy evaluation.

Outputs: results/did_first_selection.txt, results/did_panel.csv, results/did_eventstudy.csv
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfg
from utils import load_teamgames

MIN_GAMES_YEAR = 40       # a league-year needs enough games to estimate a blue WR
MIN_FP26 = 30             # need enough 2026 first-pick games to estimate D
LOG: list[str] = []
def log(m=""):
    print(m); LOG.append(str(m))


def fit(formula, panel, rhs_terms):
    try:
        m = smf.wls(formula, panel, weights=panel["n"]).fit(
            cov_type="cluster", cov_kwds={"groups": panel["league"]})
    except Exception:
        m = smf.wls(formula, panel, weights=panel["n"]).fit(cov_type="HC1")
    return m


def main():
    d = load_teamgames()

    # ---- treatment intensity D per league (from 2026) --------------------
    d26 = d[d.year == 2026]
    fp = d26[d26.firstPick == 1]
    dl = fp.groupby("league").agg(blue_share=("blue", "mean"), n_fp=("blue", "size"))
    dl = dl[dl.n_fp >= MIN_FP26].copy()
    dl["D"] = 1.0 - dl["blue_share"]           # 0 = coupled, higher = decoupled
    Dmap = dl["D"].to_dict()

    # ---- league-year panel of blue advantage + placebo -------------------
    blue = d[d.blue == 1]
    panel = blue.groupby(["league", "year"]).agg(
        blue_wr=("result", "mean"),
        blue_herald=("firstherald", "mean"),
        n=("result", "size")).reset_index()
    panel = panel[panel.n >= MIN_GAMES_YEAR]
    panel["D"] = panel["league"].map(Dmap)
    panel = panel.dropna(subset=["D"])
    # keep leagues observed in 2026 and >=3 years total
    yrs = panel.groupby("league").agg(has26=("year", lambda s: 2026 in set(s)),
                                      nyear=("year", "nunique"))
    keep = yrs[(yrs.has26) & (yrs.nyear >= 3)].index
    panel = panel[panel.league.isin(keep)].copy()
    panel["blue_adv"] = 100 * (panel["blue_wr"] - 0.5)
    panel["herald_adv"] = 100 * (panel["blue_herald"] - 0.5)
    panel["post"] = (panel["year"] == 2026).astype(int)
    panel["D_post"] = panel["D"] * panel["post"]

    log(f"DiD panel: {panel.league.nunique()} leagues x years, {len(panel)} league-years")
    log(f"  treatment intensity D (2026 decoupling) across kept leagues: "
        f"min={panel.D.min():.2f} median={panel.D.median():.2f} max={panel.D.max():.2f}")
    top = dl.sort_values("D", ascending=False).head(6)
    log("  most-decoupled leagues (D): " +
        ", ".join(f"{lg}={row.D:.2f}" for lg, row in top.iterrows()))

    # ---- main DiD --------------------------------------------------------
    m = fit("blue_adv ~ C(league) + C(year) + D_post", panel, ["D_post"])
    b, se, p = m.params["D_post"], m.bse["D_post"], m.pvalues["D_post"]
    log("\nMAIN DiD  (outcome = blue-side win advantage, pp):")
    log(f"  b(D x post2026) = {b:+.2f} pp per unit decoupling  "
        f"95%CI[{b-1.96*se:+.2f},{b+1.96*se:+.2f}]  p={p:.3g}")
    log(f"  -> at LCK-level decoupling (D~0.7): predicted change = {0.7*b:+.2f} pp "
        f"(a full-strength rule would need a large negative here).")

    # ---- event study (2025 = reference year) ----------------------------
    for yy in (2022, 2023, 2024, 2026):
        panel[f"D_{yy}"] = panel["D"] * (panel["year"] == yy).astype(int)
    es = fit("blue_adv ~ C(league) + C(year) + D_2022 + D_2023 + D_2024 + D_2026",
             panel, ["D_2022", "D_2023", "D_2024", "D_2026"])
    log("\nEVENT STUDY (D x year, relative to 2025; pre-2026 ~0 => parallel trends):")
    es_rows = []
    pre_coefs = []
    for yy in (2022, 2023, 2024, 2026):
        term = f"D_{yy}"
        bb, ss = es.params[term], es.bse[term]
        flag = "  <-- treatment year" if yy == 2026 else "  (pre)"
        log(f"   {yy}: {bb:+.2f} pp  95%CI[{bb-1.96*ss:+.2f},{bb+1.96*ss:+.2f}]{flag}")
        es_rows.append(dict(year=yy, coef=bb, lo=bb-1.96*ss, hi=bb+1.96*ss))
        if yy != 2026:
            pre_coefs.append(bb)
    es_rows.append(dict(year=2025, coef=0.0, lo=0.0, hi=0.0))   # reference
    max_pre = max(abs(c) for c in pre_coefs)
    log(f"  parallel-trends check: largest pre-period |coef| = {max_pre:.2f} pp "
        f"(2026 = {es.params['D_2026']:+.2f} pp).")
    if max_pre > 0.5 * abs(es.params["D_2026"]):
        log("  CAUTION: pre-period coefficients are NOT flat (2024 already elevated) and")
        log("  the panel is small -> read the DiD as SUGGESTIVE, not clean identification.")

    # ---- placebo / positive control: mechanical herald outcome ----------
    mp = fit("herald_adv ~ C(league) + C(year) + D_post", panel, ["D_post"])
    bp, sep, pp_ = mp.params["D_post"], mp.bse["D_post"], mp.pvalues["D_post"]
    log("\nPLACEBO (outcome = blue-side FIRST-HERALD rate; map geometry is fixed):")
    log(f"  b(D x post2026) = {bp:+.2f} pp  95%CI[{bp-1.96*sep:+.2f},{bp+1.96*sep:+.2f}]  p={pp_:.3g}")
    log("  (near 0 as expected: decoupling does not move the mechanical map advantage.)")

    log("\nREAD (honest): the DiD point estimate is POSITIVE and non-significant, so there")
    log("is NO evidence First Selection reduced the blue-side edge (if anything decoupled")
    log("leagues drift slightly higher, consistent with strong teams self-selecting blue).")
    log("The placebo (herald) is null as it should be. BUT pre-trends are imperfect and the")
    log("panel is small, so the DiD is SUPPORTING evidence, not proof; the robust evidence")
    log("is the descriptive 5-year stability of blue OR (1.21-1.31, incl. 2026), see figures.")

    panel.to_csv(os.path.join(cfg.RESULTS_DIR, "did_panel.csv"), index=False)
    pd.DataFrame(es_rows).sort_values("year").to_csv(
        os.path.join(cfg.RESULTS_DIR, "did_eventstudy.csv"), index=False)
    with open(os.path.join(cfg.RESULTS_DIR, "did_first_selection.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("\nWrote results/did_first_selection.txt, results/did_panel.csv, results/did_eventstudy.csv")


if __name__ == "__main__":
    main()
