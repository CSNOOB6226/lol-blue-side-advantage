"""
Associational match-state benchmark for the blue-side win contrast.

Compare the residual blue coefficient after adjustment for four path variables
with a broader match-state benchmark. Some objective counts are not strictly
time-stamped before 15:00, so this is not a complete pre-15-minute information set.
Unmeasured factors, including map geometry, may be consistent with a remaining
association but cannot be identified from these data.

  parsimonious variables: firstherald, firstdragon, gold@15, firsttower           (4)
  benchmark variables: + firstblood, void_grubs, gold@10, xp@10, xp@15            (9)

The residual is the adjusted blue coefficient in a linear probability model.
Confidence intervals resample whole games. Individual channel splits in the
broader model are collinear and are not interpreted as causal effects.

Outputs: results/mediation_full.txt, results/mediation_full.csv
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfg
from utils import load_teamgames

PARS = ["firstherald", "firstdragon", "z_gold15", "firsttower"]
FULL = ["firstblood", "firstherald", "firstdragon", "void_grubs", "firsttower",
        "z_gold10", "z_xp10", "z_gold15", "z_xp15"]
RNG = np.random.default_rng(20260701)
LOG: list[str] = []
def log(m=""):
    print(m); LOG.append(str(m))


def prep(sub: pd.DataFrame):
    """Return (clean subframe, full mediators AVAILABLE this year).
    void_grubs only exists from 2024, so the full set is year-adaptive; the parsimonious
    and full residuals are then compared on the SAME (full-available) sample."""
    sub = sub.copy()
    for raw, zc in [("golddiffat10", "z_gold10"), ("xpdiffat10", "z_xp10"),
                    ("golddiffat15", "z_gold15"), ("xpdiffat15", "z_xp15")]:
        sub[zc] = (sub[raw] - sub[raw].mean()) / sub[raw].std()
    full_avail = [c for c in FULL if c in sub and sub[c].notna().mean() > 0.5]
    need = ["result", "blue"] + sorted(set(PARS + full_avail))
    return sub.dropna(subset=[c for c in need if c in sub]), full_avail


def direct(y, blue, M):
    """Adjusted blue coefficient controlling variables M (LPM via lstsq)."""
    X = np.column_stack([np.ones(len(y)), blue, M])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta[1]


def total(y, blue):
    X = np.column_stack([np.ones(len(y)), blue])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta[1]


def boot_ci(sub, cols, B=500):
    groups = sub.groupby("gameid").indices
    gids = np.array(list(groups.keys())); pos = [groups[g] for g in gids]
    y = sub["result"].to_numpy(float); blue = sub["blue"].to_numpy(float)
    M = sub[cols].to_numpy(float)
    out = []
    for _ in range(B):
        pick = RNG.integers(0, len(gids), len(gids))
        idx = np.concatenate([pos[k] for k in pick])
        out.append(direct(y[idx], blue[idx], M[idx]))
    return np.percentile(out, 2.5), np.percentile(out, 97.5)


def main():
    d = load_teamgames()
    log("C. MATCH-STATE BENCHMARK — adjusted blue association (LPM, pp of win prob)")
    log("   parsimonious (4 variables) vs match-state benchmark (up to 9 variables).\n")
    log("   Some objective counts are not strictly time-stamped before 15:00.\n")
    rows = []
    for y in (2022, 2023, 2024, 2025, 2026):
        sub, full_avail = prep(d[d.year == y])
        yy = sub["result"].to_numpy(float); bl = sub["blue"].to_numpy(float)
        tot = total(yy, bl)
        res_p = direct(yy, bl, sub[PARS].to_numpy(float))
        res_f = direct(yy, bl, sub[full_avail].to_numpy(float))
        ci = boot_ci(sub, full_avail) if y in (2025, 2026) else (np.nan, np.nan)
        cistr = f"  [95% CI {100*ci[0]:+.1f},{100*ci[1]:+.1f}]" if y in (2025, 2026) else ""
        note = "" if "void_grubs" in full_avail else "  (no grubs pre-2024)"
        log(f"  {y} (n={len(sub)}): total {100*tot:+.1f}pp | "
            f"residual parsimonious {100*res_p:+.1f}pp ({100*res_p/tot:.0f}%) -> "
            f"FULL {100*res_f:+.1f}pp ({100*res_f/tot:.0f}%){cistr}{note}")
        rows.append(dict(year=y, total_pp=100*tot, resid_pars_pp=100*res_p,
                         resid_full_pp=100*res_f, resid_full_share=res_f/tot,
                         ci_lo=100*ci[0], ci_hi=100*ci[1]))
    recent = [r["resid_full_share"] for r in rows if r["year"] >= 2024]
    log(f"\n  With the match-state benchmark, {100*min(recent):.0f}-{100*max(recent):.0f}% of")
    log("  the blue-side contrast (2024-26) remains as an adjusted residual association.")
    changes = [r["resid_full_pp"] - r["resid_pars_pp"] for r in rows if r["year"] >= 2024]
    log(f"  Benchmark minus parsimonious residual: {min(changes):+.2f} to {max(changes):+.2f} pp.")
    log("  This is consistent with factors not recorded in Oracle's Elixir, e.g. map geometry;")
    log("  their contributions are not identifiable with these data. These are associations,")
    log("  and the objective counts do not all refer strictly to the state before 15:00.")

    pd.DataFrame(rows).to_csv(os.path.join(cfg.RESULTS_DIR, "mediation_full.csv"), index=False)
    with open(os.path.join(cfg.RESULTS_DIR, "mediation_full.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("\nWrote results/mediation_full.txt, results/mediation_full.csv")


if __name__ == "__main__":
    main()
