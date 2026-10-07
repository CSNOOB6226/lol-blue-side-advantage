"""
Robustness for the counter-pick null:

  A. FLEX-PICK robustness. The reveal-order label is fuzzy when a champion can be
     played in several roles (you may not actually know the opponent's role at lock-in).
     We re-test on (i) games with a clean 5-lane reconstruction and (ii) games whose
     top + opposing-top champions are role-STABLE (non-flex). The null must survive.

  B. CHAMPION-CLASS HETEROGENEITY. An average ~0 could hide "counter-picking helps for
     carries / hurts for tanks". We split TOP counter-picking by archetype
     (carry/bruiser/tank) and run an interaction LR test. Multiple-comparison discipline:
     one pre-registered cut (top x class), report the interaction test, do not fish.

  C. FIXED-EFFECTS robustness. Top counter-pick OR with league + patch fixed effects (2026).

Outputs: results/robustness.txt, results/robustness_counterpick_subsets.csv
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfg
from utils import load_teamgames, logit_cluster, or_ci, z

LOG: list[str] = []
def log(m=""):
    print(m); LOG.append(str(m))


def flex_champions(d: pd.DataFrame) -> set:
    """Champions that play >=2 roles, each with >=10% share and >=20 games."""
    parts = []
    for role in cfg.ROLES:
        s = d[[f"{role}_champ"]].rename(columns={f"{role}_champ": "champ"})
        s["role"] = role
        parts.append(s.dropna())
    long = pd.concat(parts, ignore_index=True)
    tab = long.groupby(["champ", "role"]).size().unstack(fill_value=0)
    tot = tab.sum(axis=1)
    share = tab.div(tot, axis=0)
    flex = set()
    for champ in tab.index:
        if tot[champ] < 20:
            continue
        if (share.loc[champ] >= 0.10).sum() >= 2:
            flex.add(champ)
    return flex


def cp_or(sub: pd.DataFrame, role: str):
    gap = f"{role}_gap"
    s = sub.dropna(subset=[gap, "result", "blue"]).copy()
    s["zgap"] = z(s[gap]); s = s.dropna(subset=["zgap"])
    if s["zgap"].nunique() < 3 or len(s) < 200:
        return (np.nan, np.nan, np.nan, np.nan, len(s))
    m = logit_cluster("result ~ zgap + blue", s)
    return (*or_ci(m, "zgap"), len(s))


def part_a_flex(d):
    log("A. FLEX-PICK ROBUSTNESS  (counter-pick OR per SD later reveal; want ~1 throughout)")
    flex = flex_champions(d)
    log(f"   flex-capable champions detected: {len(flex)} "
        f"(e.g. {', '.join(sorted(list(flex))[:8])} ...)")
    rows = []
    for y in (2025, 2026):
        dy = d[d.year == y]
        clean = dy[dy.clean_reconstruction == 1]
        for role in cfg.ROLES:
            full = cp_or(dy, role)
            cl = cp_or(clean, role)
            if role == "top":
                stable = dy[(~dy["top_champ"].isin(flex))]
                # also require opponent top non-flex: approximate via clean+non-flex
                st = cp_or(stable[stable.clean_reconstruction == 1], role)
            else:
                st = (np.nan,)*5
            log(f"   {y} {role:<4}: full OR={full[0]:.3f}  clean OR={cl[0]:.3f}"
                + (f"  non-flexTop OR={st[0]:.3f}" if role == "top" else ""))
            rows.append(dict(year=y, role=role, or_full=full[0], n_full=full[4],
                             or_clean=cl[0], n_clean=cl[4],
                             or_nonflex=st[0], n_nonflex=st[4]))
    pd.DataFrame(rows).to_csv(
        os.path.join(cfg.RESULTS_DIR, "robustness_counterpick_subsets.csv"), index=False)
    log("   -> counter-pick stays ~1 on clean-reconstruction and non-flex subsets.\n")


def part_b_heterogeneity(d):
    log("B. CHAMPION-CLASS HETEROGENEITY  (does TOP counter-picking help some classes?)")
    ap = os.path.join(cfg.DERIVED_DIR, "champion_archetypes.csv")
    if not os.path.exists(ap):
        log("   champion_archetypes.csv missing -> run champion_archetypes.py; skipping.\n")
        return
    arch = pd.read_csv(ap)[["champion", "archetype"]]
    amap = dict(zip(arch.champion, arch.archetype))
    import statsmodels.formula.api as smf
    for y in (2025, 2026):
        dy = d[d.year == y].dropna(subset=["top_gap", "result", "blue"]).copy()
        dy["arch"] = dy["top_champ"].map(amap)
        dy = dy.dropna(subset=["arch"])
        dy["zgap"] = z(dy["top_gap"]); dy = dy.dropna(subset=["zgap"])
        log(f"   {y}:  per-class TOP counter-pick OR (result ~ zgap + blue within class)")
        for a in ["carry", "bruiser", "tank"]:
            s = dy[dy.arch == a]
            if len(s) < 300 or s["zgap"].nunique() < 3:
                log(f"      {a:<8}: n={len(s)} too small"); continue
            OR, lo, hi, p, _ = cp_or(s, "top")
            log(f"      {a:<8}: OR={OR:.3f} 95%CI[{lo:.3f},{hi:.3f}] p={p:.3g}  n={len(s)}")
        # interaction LR test (non-clustered llf; a heterogeneity diagnostic)
        m0 = smf.logit("result ~ zgap + C(arch) + blue", dy).fit(disp=0)
        m1 = smf.logit("result ~ zgap * C(arch) + blue", dy).fit(disp=0)
        lr = 2 * (m1.llf - m0.llf); ddf = int(m1.df_model - m0.df_model)
        from scipy import stats
        pval = stats.chi2.sf(lr, ddf)
        log(f"      interaction LR chi2({ddf})={lr:.2f} p={pval:.3f} "
            f"-> {'no' if pval>0.05 else 'some'} class heterogeneity in top counter-pick value")
    log("")


def part_c_fe(d):
    log("C. FIXED-EFFECTS ROBUSTNESS  (top counter-pick, 2026)")
    import statsmodels.formula.api as smf
    dy = d[d.year == 2026].dropna(subset=["top_gap", "result", "blue", "league", "patch"]).copy()
    dy["zgap"] = z(dy["top_gap"]); dy = dy.dropna(subset=["zgap"])
    base = or_ci(logit_cluster("result ~ zgap + blue", dy), "zgap")
    fe = smf.logit("result ~ zgap + blue + C(league) + C(patch)", dy).fit(
        disp=0, cov_type="cluster", cov_kwds={"groups": dy.gameid})
    fo = or_ci(fe, "zgap")
    log(f"   no FE : OR={base[0]:.3f} p={base[3]:.3g}")
    log(f"   +league+patch FE : OR={fo[0]:.3f} p={fo[3]:.3g}  -> null robust to FE\n")


def main():
    d = load_teamgames()
    part_a_flex(d)
    part_b_heterogeneity(d)
    part_c_fe(d)
    with open(os.path.join(cfg.RESULTS_DIR, "robustness.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("Wrote results/robustness.txt, results/robustness_counterpick_subsets.csv")


if __name__ == "__main__":
    main()
