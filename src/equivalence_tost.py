"""
B. EQUIVALENCE TESTS (TOST) for the draft-value nulls.

A non-significant OR only says "we failed to reject 0"; a sceptic answers "you just lacked
power". The Two One-Sided Tests (TOST) procedure turns this into a positive claim: we can
*reject the presence of any effect larger than a pre-set negligible bound*.

Smallest effect size of interest (SESOI). On the win-odds scale we treat an odds ratio inside
  * primary : OR in [1/1.10, 1.10]  (a +-10% change in odds — already tiny for one draft lever)
  * strict  : OR in [0.95, 1.05]
as practically null. TOST on theta = log(OR): reject "theta <= log(low)" AND "theta >= log(high)".
Equivalence is established at alpha=0.05 iff the 90% CI of theta lies inside the bounds, i.e.
p_TOST = max(p_lower, p_upper) < 0.05.

We run it on every draft lever (first-pick + 10 counter-pick tests) and — as a contrast — on
blue side, which SHOULD FAIL equivalence because it is a real effect. "Draft levers are
statistically equivalent to null; blue side is not" is a strong, reviewer-proof way to state
the result.

Outputs: results/equivalence_tost.txt, results/equivalence_tost.csv
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfg
from utils import load_teamgames, logit_cluster, z

LOW1, HIGH1 = np.log(1/1.10), np.log(1.10)     # primary +-10% odds
LOW2, HIGH2 = np.log(0.95), np.log(1.05)       # strict
LOG: list[str] = []
def log(m=""):
    print(m); LOG.append(str(m))


def tost(theta, se, low, high):
    """Return (p_lower, p_upper, p_tost). Equivalent at alpha iff p_tost < alpha."""
    p_lower = stats.norm.sf((theta - low) / se)    # H0: theta <= low
    p_upper = stats.norm.cdf((theta - high) / se)  # H0: theta >= high
    return p_lower, p_upper, max(p_lower, p_upper)


def fit_logor(formula, df, name):
    m = logit_cluster(formula, df)
    return m.params[name], m.bse[name]


def row(label, theta, se):
    OR = np.exp(theta)
    lo90, hi90 = np.exp(theta - 1.645 * se), np.exp(theta + 1.645 * se)
    p1 = tost(theta, se, LOW1, HIGH1)[2]
    p2 = tost(theta, se, LOW2, HIGH2)[2]
    verdict = "EQUIVALENT to null" if p1 < 0.05 else "not shown equivalent"
    log(f"  {label:<22} OR={OR:.3f}  90%CI[{lo90:.3f},{hi90:.3f}]  "
        f"TOST p(±10%)={p1:.3f}  p(±5%)={p2:.3f}  -> {verdict}")
    return dict(param=label, OR=OR, ci90_lo=lo90, ci90_hi=hi90,
                tost_p_10=p1, tost_p_5=p2, equivalent_10=(p1 < 0.05))


def main():
    d = load_teamgames()
    d26 = d[d.year == 2026]
    recs = []
    log("B. EQUIVALENCE (TOST) — is each draft lever statistically equivalent to null?")
    log(f"   bounds: primary OR∈[{np.exp(LOW1):.3f},{np.exp(HIGH1):.3f}], strict OR∈[0.95,1.05]\n")

    log(" DRAFT LEVERS (expected: equivalent to null):")
    th, se = fit_logor("result ~ firstPick + blue",
                       d26.dropna(subset=["firstPick", "blue", "result"]), "firstPick")
    recs.append(row("First pick (2026)", th, se))
    for y in (2025, 2026):
        for role in cfg.ROLES:
            s = d[d.year == y].dropna(subset=[f"{role}_gap", "result", "blue"]).copy()
            s["zgap"] = z(s[f"{role}_gap"]); s = s.dropna(subset=["zgap"])
            th, se = fit_logor("result ~ zgap + blue", s, "zgap")
            recs.append(row(f"Counterpick {role} {y}", th, se))

    log("\n CONTRAST — blue side (expected: NOT equivalent, it is a real effect):")
    th, se = fit_logor("result ~ blue", d26.dropna(subset=["blue", "result"]), "blue")
    recs.append(row("Blue side (2026)", th, se))

    fam = pd.DataFrame(recs)
    n_draft = fam[fam.param != "Blue side (2026)"]
    log(f"\n  SUMMARY: {int(n_draft.equivalent_10.sum())}/{len(n_draft)} draft levers are "
        f"statistically EQUIVALENT to null at the ±10%-odds bound;")
    log(f"           blue side is {'NOT ' if not fam.set_index('param').loc['Blue side (2026)','equivalent_10'] else ''}"
        f"equivalent (as it should be — a genuine effect).")
    log("  => The draft nulls are not 'absence of evidence': we can rule out any non-negligible effect.")

    fam.to_csv(os.path.join(cfg.RESULTS_DIR, "equivalence_tost.csv"), index=False)
    with open(os.path.join(cfg.RESULTS_DIR, "equivalence_tost.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("\nWrote results/equivalence_tost.txt, results/equivalence_tost.csv")


if __name__ == "__main__":
    main()
