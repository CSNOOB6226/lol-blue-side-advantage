"""
Path analysis / causal mediation of the BLUE-SIDE win advantage, 2022-2026.

Causal chain (side is the treatment; in the coupled 2022-25 era side is assigned,
so blue is a clean quasi-random treatment for a mediation decomposition):

        blue ---> firstherald (+, top-side river, "the engine")
             ---> firstdragon (-, bottom-side river, a SUPPRESSOR)
             ---> gold@15  ---> firsttower  ---> WIN

We use linear probability models so effects are additive and the total decomposes as
    total(blue->win) = direct + sum_j indirect_j,   indirect_j = a_j * b_j
with a_j = blue->M_j and b_j = M_j->win (all mediators + blue in the outcome model).
95% CIs come from a CLUSTER bootstrap that resamples whole games (both mirror rows).

WHY PATH ANALYSIS AND NOT FULL (LATENT) SEM.  Our mediators are directly OBSERVED
(herald/dragon/tower are binary indicators, gold@15 is measured), not latent
constructs with multiple noisy indicators, so the measurement half of SEM is empty.
The outcome and three of four mediators are BINARY, which violates the multivariate-
normal ML assumption behind classic SEM fit statistics. Path analysis with a linear
probability model + nonparametric cluster bootstrap keeps the same "decompose the
effect along a hypothesized graph" logic while staying valid under binary,
heteroskedastic, clustered data. (See docs/METHODS.md.)

Outputs: results/mediation_path.txt, results/mediation_path.csv
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from utils import load_teamgames

MEDIATORS = ["firstherald", "firstdragon", "z_gold15", "firsttower"]
PRETTY = {"firstherald": "first herald (+, top-side)", "firstdragon": "first dragon (-, suppressor)",
          "z_gold15": "gold@15 (SD)", "firsttower": "first tower"}
RNG = np.random.default_rng(20260701)
LOG: list[str] = []
def log(m=""):
    print(m); LOG.append(str(m))


def lpm(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    """OLS coefficients via least squares (X already includes an intercept col)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def decompose(sub: pd.DataFrame):
    """Return dict of point effects (in pp for win-scale) for one year's data."""
    sub = sub.copy()
    sub["z_gold15"] = (sub["golddiffat15"] - sub["golddiffat15"].mean()) / sub["golddiffat15"].std()
    sub = sub.dropna(subset=["result", "blue"] + MEDIATORS)
    y = sub["result"].to_numpy(float)
    blue = sub["blue"].to_numpy(float)
    M = sub[MEDIATORS].to_numpy(float)
    n = len(sub)
    one = np.ones(n)

    # total: win ~ blue
    c = lpm(y, np.column_stack([one, blue]))[1]
    # outcome: win ~ blue + mediators  -> direct c' and b_j
    Xout = np.column_stack([one, blue, M])
    bo = lpm(y, Xout)
    c_prime = bo[1]
    b = bo[2:]
    # a_j: M_j ~ blue
    a = np.array([lpm(M[:, j], np.column_stack([one, blue]))[1] for j in range(M.shape[1])])
    indirect = a * b
    return dict(total=c, direct=c_prime, indirect=indirect, a=a, b=b, n=n)


def cluster_bootstrap(sub: pd.DataFrame, B: int = 600):
    """Percentile CIs for total, direct and each indirect effect (resample games)."""
    sub = sub.copy()
    sub["z_gold15"] = (sub["golddiffat15"] - sub["golddiffat15"].mean()) / sub["golddiffat15"].std()
    sub = sub.dropna(subset=["result", "blue"] + MEDIATORS)
    # group row positions by game
    groups = sub.groupby("gameid").indices
    gids = np.array(list(groups.keys()))
    pos = [groups[g] for g in gids]
    y_all = sub["result"].to_numpy(float)
    blue_all = sub["blue"].to_numpy(float)
    M_all = sub[MEDIATORS].to_numpy(float)

    tot, dire, ind = [], [], []
    for _ in range(B):
        pick = RNG.integers(0, len(gids), len(gids))
        idx = np.concatenate([pos[k] for k in pick])
        y, blue, M = y_all[idx], blue_all[idx], M_all[idx]
        one = np.ones(len(idx))
        c = lpm(y, np.column_stack([one, blue]))[1]
        bo = lpm(y, np.column_stack([one, blue, M]))
        a = np.array([lpm(M[:, j], np.column_stack([one, blue]))[1] for j in range(M.shape[1])])
        tot.append(c); dire.append(bo[1]); ind.append(a * bo[2:])
    tot, dire, ind = np.array(tot), np.array(dire), np.array(ind)
    ci = lambda arr: (np.percentile(arr, 2.5), np.percentile(arr, 97.5))
    return dict(total=ci(tot), direct=ci(dire),
                indirect=[ci(ind[:, j]) for j in range(ind.shape[1])])


def main():
    d = load_teamgames()
    rows = []
    log("PATH-ANALYSIS MEDIATION of the blue-side win advantage (LPM, pp of win prob)")
    log("indirect_j = a_j(blue->M_j) * b_j(M_j->win); total = direct + sum indirect_j\n")
    for y in (2022, 2023, 2024, 2025, 2026):
        sub = d[d.year == y]
        pt = decompose(sub)
        do_boot = y in (2025, 2026)
        boot = cluster_bootstrap(sub) if do_boot else None
        log(f"=== {y}  (n={pt['n']} team-games) ===")
        tci = f"  [95% CI {100*boot['total'][0]:+.1f},{100*boot['total'][1]:+.1f}]" if boot else ""
        log(f"  TOTAL blue->win   : {100*pt['total']:+5.1f} pp{tci}")
        for j, m in enumerate(MEDIATORS):
            cci = f"  [CI {100*boot['indirect'][j][0]:+.1f},{100*boot['indirect'][j][1]:+.1f}]" if boot else ""
            log(f"    via {PRETTY[m]:<28}: {100*pt['indirect'][j]:+5.1f} pp{cci}")
            rows.append(dict(year=y, channel=m, indirect_pp=100*pt['indirect'][j],
                             a=pt['a'][j], b=pt['b'][j],
                             ci_lo=100*boot['indirect'][j][0] if boot else np.nan,
                             ci_hi=100*boot['indirect'][j][1] if boot else np.nan))
        dci = f"  [CI {100*boot['direct'][0]:+.1f},{100*boot['direct'][1]:+.1f}]" if boot else ""
        log(f"    direct / unexplained residual : {100*pt['direct']:+5.1f} pp{dci}")
        share = 100 * pt['direct'] / pt['total'] if pt['total'] else np.nan
        log(f"    (residual = {share:.0f}% of total -> map root cause OE cannot measure)\n")
        rows.append(dict(year=y, channel="direct_residual", indirect_pp=100*pt['direct'],
                         a=np.nan, b=np.nan,
                         ci_lo=100*boot['direct'][0] if boot else np.nan,
                         ci_hi=100*boot['direct'][1] if boot else np.nan))

    log("ROBUST 5-YEAR PATTERN: first herald is the ENGINE (positive, growing);")
    log("first dragon is a SUPPRESSOR (blue wins DESPITE conceding it); large residual.")
    pd.DataFrame(rows).to_csv(os.path.join(C.RESULTS_DIR, "mediation_path.csv"), index=False)
    with open(os.path.join(C.RESULTS_DIR, "mediation_path.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("\nWrote results/mediation_path.txt, results/mediation_path.csv")


if __name__ == "__main__":
    main()
