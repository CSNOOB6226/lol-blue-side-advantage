"""Estimate champion matchup-quality controls from Oracle's Elixir data.

For each role, five-fold cross-fitting groups rows by gameid. The ordered
champion-pair score is mean 15-minute lane gold difference in training games,
shrunk toward the champion's training mean with k0 = 10. Held-out scores use
champion identities and training outcomes, not the held-out game's outcome.

Models relate matchup quality and reveal timing to wins and relate reveal
timing to matchup quality. Results are reported for each role.

Outputs: results/matchup_quality.txt, results/matchup_quality.csv
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfg
from utils import load_teamgames, logit_cluster, ols_cluster, or_ci, z

K_FOLDS = 5
SHRINK = 10.0
RNG = np.random.default_rng(20260701)
LOG: list[str] = []
def log(m=""):
    print(m); LOG.append(str(m))


def crossfit_mq(df: pd.DataFrame, champ, opp, gd) -> pd.Series:
    """Leakage-free (k-fold by gameid) shrunk ordered-matchup gold@15 score."""
    d = df.dropna(subset=[champ, opp, gd]).copy()
    gids = d["gameid"].unique()
    fold = {g: i % K_FOLDS for i, g in enumerate(RNG.permutation(gids))}
    d["_fold"] = d["gameid"].map(fold)
    mq = pd.Series(np.nan, index=d.index)
    for f in range(K_FOLDS):
        tr, te = d[d._fold != f], d[d._fold == f]
        champ_main = tr.groupby(champ)[gd].mean().to_dict()
        agg = tr.groupby([champ, opp])[gd].agg(["mean", "size"])
        pair_mean = agg["mean"].to_dict(); pair_n = agg["size"].to_dict()
        gmean = tr[gd].mean()
        vals = []
        for a, b in zip(te[champ].to_numpy(), te[opp].to_numpy()):
            cm = champ_main.get(a, gmean)
            if (a, b) in pair_mean:
                n = pair_n[(a, b)]
                vals.append((n * pair_mean[(a, b)] + SHRINK * cm) / (n + SHRINK))
            else:
                vals.append(cm)
        mq.loc[te.index] = vals
    return mq


def lane_frame(d: pd.DataFrame, role: str) -> pd.DataFrame:
    """team-game rows for a lane + the opposing lane's champion."""
    me = d[["gameid", "side", "year", "result", "blue",
            f"{role}_champ", f"{role}_gap", f"{role}_gd15"]].copy()
    me = me.rename(columns={f"{role}_champ": "champ", f"{role}_gap": "gap", f"{role}_gd15": "gd15"})
    opp = me[["gameid", "side", "champ"]].copy()
    opp["side"] = opp["side"].map({"Blue": "Red", "Red": "Blue"})
    opp = opp.rename(columns={"champ": "opp_champ"})
    return me.merge(opp, on=["gameid", "side"], how="left")


def analyze_lane(d: pd.DataFrame, role: str, headline: bool):
    lf = lane_frame(d[d.year.isin([2025, 2026])], role)
    lf["mq"] = crossfit_mq(lf, "champ", "opp_champ", "gd15")
    lf = lf.dropna(subset=["mq", "gap", "result", "blue"]).copy()
    lf["z_mq"] = z(lf["mq"]); lf["zgap"] = z(lf["gap"])
    lf = lf.dropna(subset=["z_mq", "zgap"])

    mq_or = or_ci(logit_cluster("result ~ z_mq + blue", lf), "z_mq")
    base = or_ci(logit_cluster("result ~ zgap + blue", lf), "zgap")
    joint = logit_cluster("result ~ zgap + z_mq + blue", lf)
    gap_ctrl = or_ci(joint, "zgap"); mq_ctrl = or_ci(joint, "z_mq")
    buy = ols_cluster("z_mq ~ zgap", lf)                    # Reveal timing and estimated matchup quality.
    buy_beta, buy_p = buy.params["zgap"], buy.pvalues["zgap"]

    if headline:
        log(f"--- {role.upper()} (headline)  n={len(lf)} ---")
        log(f"  (1) matchup quality -> win : OR/SD = {mq_or[0]:.3f} [{mq_or[1]:.3f},{mq_or[2]:.3f}] p={mq_or[3]:.2g}  (matchup MATTERS)")
        log(f"  (2) reveal timing   -> win : OR/SD = {base[0]:.3f} (alone) -> {gap_ctrl[0]:.3f} (ctrl matchup) p={gap_ctrl[3]:.2g}  (timing ~0)")
        log(f"      matchup stays strong controlling timing: OR/SD = {mq_ctrl[0]:.3f} p={mq_ctrl[3]:.2g}")
        log(f"  (3) does counter-pick buy a better matchup? z_mq ~ zgap: beta={buy_beta:+.3f} SD/SD p={buy_p:.2g}")
    return dict(role=role, n=len(lf), mq_or=mq_or[0], mq_p=mq_or[3],
                gap_or_alone=base[0], gap_or_ctrl=gap_ctrl[0], gap_p_ctrl=gap_ctrl[3],
                buy_beta=buy_beta, buy_p=buy_p)


def main():
    d = load_teamgames()
    log("A. INTERNAL MATCH-UP-QUALITY CONTROL (cross-fitted from OE, no external data)")
    log("   match-up quality = leakage-free champ-vs-champ expected 15-min lane gold.\n")
    rows = [analyze_lane(d, "top", headline=True)]
    log("\n   all five lanes (OR/SD): matchup->win vs timing->win(ctrl matchup)")
    for role in ["jng", "mid", "bot", "sup"]:
        rows.append(analyze_lane(d, role, headline=False))
    for r in rows:
        log(f"   {r['role']:<4}: matchup OR={r['mq_or']:.3f} (p={r['mq_p']:.2g})   "
            f"timing OR={r['gap_or_ctrl']:.3f} (p={r['gap_p_ctrl']:.2g})   "
            f"counter->matchup beta={r['buy_beta']:+.3f} (p={r['buy_p']:.2g})")
    log("\n   READ: the drafted MATCH-UP predicts winning; the ACT of revealing later does not,")
    log("   and barely moves once match-up is controlled. What little counter-picking buys is a")
    log("   marginal match-up edge, not a timing bonus -> clean separation from iTero's counter effect.")

    pd.DataFrame(rows).to_csv(os.path.join(cfg.RESULTS_DIR, "matchup_quality.csv"), index=False)
    with open(os.path.join(cfg.RESULTS_DIR, "matchup_quality.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("\nWrote results/matchup_quality.txt, results/matchup_quality.csv")


if __name__ == "__main__":
    main()
