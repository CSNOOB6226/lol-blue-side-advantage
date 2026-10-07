"""
Core draft-value models (the paper's three headline results):

  (1) First-pick priority has no independent win value once map side is controlled.
  (2) Blue side has a real, cross-year win advantage.
  (3) Counter-picking (revealing a lane later) does not convert to wins, in any of
      the five roles, in either 2025 or 2026.

Improvements over the pilot:
  * McFadden pseudo-R^2 and a likelihood-ratio test for every model.
  * Benjamini-Hochberg FDR correction across the 10-test counter-pick family
    (5 roles x 2 years) so we are not fooled by multiple comparisons.

Outputs:
  results/draft_value_ORs.csv   (forest-plot data: OR / CI / raw p / FDR p)
  results/core_models.txt       (readable log)
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from utils import load_teamgames, logit_cluster, or_ci, bh_fdr, z

LOG: list[str] = []
def log(msg=""):
    print(msg); LOG.append(str(msg))


def firstpick_vs_side(d26: pd.DataFrame):
    t = d26.dropna(subset=["firstPick", "blue", "result"]).copy()
    share_blue = t.loc[t.firstPick == 1, "blue"].mean()
    m = logit_cluster("result ~ firstPick + blue", t)
    fp = or_ci(m, "firstPick"); bl = or_ci(m, "blue")
    log("\n(1) FIRST-PICK vs MAP SIDE  (2026, decoupled regime)")
    log(f"    firstPick==1 is Blue {100*share_blue:.1f}% of the time (natural variation)")
    log(f"    firstPick  OR={fp[0]:.3f}  95%CI[{fp[1]:.3f},{fp[2]:.3f}]  p={fp[3]:.3g}")
    log(f"    blue side  OR={bl[0]:.3f}  95%CI[{bl[1]:.3f},{bl[2]:.3f}]  p={bl[3]:.3g}")
    log(f"    McFadden pseudo-R^2={m.prsquared:.4f}  LR chi2={m.llr:.1f} (df={int(m.df_model)}) p={m.llr_pvalue:.3g}")
    rows = [("First pick priority", "draft", 2026, *fp, t["result"].notna().sum())]
    rows.append(("Blue side (map)", "side", 2026, *bl, t["result"].notna().sum()))
    return rows


def blue_by_year(d: pd.DataFrame):
    log("\n(2) BLUE-SIDE ADVANTAGE by year  (result ~ blue, cluster SE)")
    rows = []
    for y in sorted(d["year"].unique()):
        s = d[d.year == y].dropna(subset=["result", "blue"])
        m = logit_cluster("result ~ blue", s)
        bl = or_ci(m, "blue")
        raw_wr = s.loc[s.blue == 1, "result"].mean()
        log(f"    {y}: blue OR={bl[0]:.3f}  95%CI[{bl[1]:.3f},{bl[2]:.3f}]  p={bl[3]:.2g}"
            f"   (raw blue WR={raw_wr:.3f}, n={len(s)//2} games)")
        if y in (2025, 2026):
            rows.append((f"Blue side (map)", "side_year", y, *bl, len(s)))
    return rows


def counterpick_family(d: pd.DataFrame):
    log("\n(3) COUNTER-PICK by lane x year  (result ~ z(reveal_gap) + blue, cluster SE)")
    log("    reveal_gap>0 = my lane revealed later than opponent's (more information).")
    recs = []
    for y in (2025, 2026):
        for role in C.ROLES:
            gap, cp, gd = f"{role}_gap", f"{role}_cp", f"{role}_gd15"
            s = d[(d.year == y)].dropna(subset=[gap, "result", "blue"]).copy()
            s["zgap"] = z(s[gap])
            s = s.dropna(subset=["zgap"])
            m = logit_cluster("result ~ zgap + blue", s)
            OR, lo, hi, p = or_ci(m, "zgap")
            cp_gold = s.loc[s[cp] == 1, gd].mean()
            bp_gold = s.loc[s[cp] == 0, gd].mean()
            recs.append(dict(role=role, year=y, OR=OR, lo=lo, hi=hi, p=p,
                             cp_gold=cp_gold, bp_gold=bp_gold, n=len(s)))
    fam = pd.DataFrame(recs)
    fam["p_fdr"] = bh_fdr(fam["p"].values)      # BH across the whole 10-test family
    for _, r in fam.iterrows():
        log(f"    {int(r.year)} {r.role:<4} OR={r.OR:.3f} 95%CI[{r.lo:.3f},{r.hi:.3f}] "
            f"p={r.p:.3g} p_FDR={r.p_fdr:.3g}  laneGold cp/bp={r.cp_gold:+.0f}/{r.bp_gold:+.0f}")
    n_sig_raw = int((fam.p < 0.05).sum())
    n_sig_fdr = int((fam.p_fdr < 0.05).sum())
    log(f"    -> {n_sig_raw}/10 tests significant at raw p<.05; {n_sig_fdr}/10 survive FDR.")
    log(f"    -> all 10 ORs in [{fam.OR.min():.3f}, {fam.OR.max():.3f}] (i.e. hugging OR=1).")
    rows = [(f"Counterpick {r.role}", "draft", int(r.year), r.OR, r.lo, r.hi, r.p, r.n)
            for _, r in fam.iterrows()]
    return rows, fam


def main():
    d = load_teamgames()
    d26 = d[d.year == 2026]

    forest = []
    forest += firstpick_vs_side(d26)
    forest += blue_by_year(d)
    cp_rows, fam = counterpick_family(d)

    # assemble forest table (blue + firstpick get p_fdr = p; counterpicks get family FDR)
    base = pd.DataFrame(
        [(lab, grp, yr, OR, lo, hi, p, p, n) for (lab, grp, yr, OR, lo, hi, p, n) in forest],
        columns=["label", "group", "year", "OR", "lo", "hi", "p", "p_fdr", "n"])
    cp = pd.DataFrame(
        [(lab, grp, yr, OR, lo, hi, p, n) for (lab, grp, yr, OR, lo, hi, p, n) in cp_rows],
        columns=["label", "group", "year", "OR", "lo", "hi", "p", "n"])
    cp["p_fdr"] = bh_fdr(cp["p"].values)
    out = pd.concat([base, cp], ignore_index=True)[
        ["label", "group", "year", "OR", "lo", "hi", "p", "p_fdr", "n"]]
    out.to_csv(os.path.join(C.RESULTS_DIR, "draft_value_ORs.csv"), index=False)
    fam.to_csv(os.path.join(C.RESULTS_DIR, "counterpick_family.csv"), index=False)

    with open(os.path.join(C.RESULTS_DIR, "core_models.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log(f"\nWrote results/draft_value_ORs.csv, results/counterpick_family.csv, results/core_models.txt")


if __name__ == "__main__":
    main()
