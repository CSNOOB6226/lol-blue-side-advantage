"""Run two one-sided equivalence tests for selected draft and side associations.

The primary odds-ratio bounds are [1/1.10, 1.10]; the stricter bounds are
[0.95, 1.05]. At alpha = 0.05, equivalence requires the 90% confidence interval
for the log odds ratio to lie inside the bounds. The reported TOST p-value is
the larger of the two one-sided p-values.

Tests cover first-pick priority, ten role/year reveal-gap associations, and blue
side. Conclusions apply only to these associations and the specified bounds.

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

    log(" TESTED DRAFT ASSOCIATIONS:")
    th, se = fit_logor("result ~ firstPick + blue",
                       d26.dropna(subset=["firstPick", "blue", "result"]), "firstPick")
    recs.append(row("First pick (2026)", th, se))
    for y in (2025, 2026):
        for role in cfg.ROLES:
            s = d[d.year == y].dropna(subset=[f"{role}_gap", "result", "blue"]).copy()
            s["zgap"] = z(s[f"{role}_gap"]); s = s.dropna(subset=["zgap"])
            th, se = fit_logor("result ~ zgap + blue", s, "zgap")
            recs.append(row(f"Counterpick {role} {y}", th, se))

    log("\n CONTRAST — blue side:")
    th, se = fit_logor("result ~ blue", d26.dropna(subset=["blue", "result"]), "blue")
    recs.append(row("Blue side (2026)", th, se))

    fam = pd.DataFrame(recs)
    reveal = fam[fam.param.str.startswith("Counterpick ")]
    log(f"\n  SUMMARY: {int(reveal.equivalent_10.sum())}/{len(reveal)} tested reveal-gap associations")
    log("  meet equivalence within primary OR bounds [1/1.10, 1.10]; this is not a claim")
    log("  about all draft decisions or effects outside the measured reveal-gap contrasts.")
    first_equiv = fam.set_index("param").loc["First pick (2026)", "equivalent_10"]
    log("  First-pick priority " + ("passes" if first_equiv else "does not pass") + " equivalence at these bounds.")
    blue_equiv = fam.set_index("param").loc["Blue side (2026)", "equivalent_10"]
    log("  Blue side " + ("passes" if blue_equiv else "does not pass") + " equivalence at these bounds.")

    fam.to_csv(os.path.join(cfg.RESULTS_DIR, "equivalence_tost.csv"), index=False)
    with open(os.path.join(cfg.RESULTS_DIR, "equivalence_tost.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("\nWrote results/equivalence_tost.txt, results/equivalence_tost.csv")


if __name__ == "__main__":
    main()
