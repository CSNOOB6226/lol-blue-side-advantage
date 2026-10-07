"""
Descriptive tables required by the manuscript that are not already produced by the
analysis scripts. This script only READS the derived table; it does not alter any
existing analysis.

Outputs (results/):
  paper_sample_by_year.csv     sample composition, coverage window, blue win rate
  paper_side_early_outcomes.csv  blue -> early-state differences (mechanism inputs)
  paper_firstpick_crosstab.csv   2026 side x first-pick cells with win rates
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfg
from utils import load_teamgames, ols_cluster, logit_cluster

pd.set_option("display.width", 200)


def sample_by_year(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["dt"] = pd.to_datetime(d["date"], errors="coerce")
    rows = []
    for y in sorted(d.year.unique()):
        s = d[d.year == y]
        b = s[s.blue == 1]
        rows.append(dict(
            season=int(y),
            games=s.gameid.nunique(),
            team_games=len(s),
            leagues=s.league.nunique(),
            first_date=s.dt.min().date().isoformat(),
            last_date=s.dt.max().date().isoformat(),
            blue_win_rate=round(100 * b.result.mean(), 2),
            clean_reconstruction=round(100 * s.clean_reconstruction.mean(), 1),
        ))
    tot = pd.DataFrame(rows)
    tot.loc[len(tot)] = dict(
        season="All", games=d.gameid.nunique(), team_games=len(d),
        leagues=d.league.nunique(),
        first_date=d.dt.min().date().isoformat(), last_date=d.dt.max().date().isoformat(),
        blue_win_rate=round(100 * d[d.blue == 1].result.mean(), 2),
        clean_reconstruction=round(100 * d.clean_reconstruction.mean(), 1))
    return tot


def side_early_outcomes(d: pd.DataFrame) -> pd.DataFrame:
    """OLS of each early-state variable on `blue`, cluster SE by game (pooled sample)."""
    specs = [
        ("First herald", "firstherald", "pp"),
        ("First dragon", "firstdragon", "pp"),
        ("First tower", "firsttower", "pp"),
        ("First blood", "firstblood", "pp"),
        ("Void grubs (count, 2024+)", "void_grubs", "count"),
        ("Gold difference at 10 min", "golddiffat10", "gold"),
        ("Gold difference at 15 min", "golddiffat15", "gold"),
        ("XP difference at 15 min", "xpdiffat15", "xp"),
        ("Team vision score", "team_vision", "points"),
    ]
    rows = []
    for label, col, unit in specs:
        if col not in d:
            continue
        s = d.dropna(subset=[col, "blue"]).copy()
        if s[col].nunique() < 2:
            continue
        m = ols_cluster(f"{col} ~ blue", s)
        b, se, p = m.params["blue"], m.bse["blue"], m.pvalues["blue"]
        scale = 100.0 if unit == "pp" else 1.0
        sd = s[col].std()
        rows.append(dict(outcome=label, unit=unit, n=len(s),
                         blue_effect=round(b * scale, 2),
                         ci_lo=round((b - 1.96 * se) * scale, 2),
                         ci_hi=round((b + 1.96 * se) * scale, 2),
                         p_value=p,
                         std_effect=round(b / sd, 3) if sd else np.nan))
    return pd.DataFrame(rows)


def firstpick_crosstab(d: pd.DataFrame) -> pd.DataFrame:
    s = d[(d.year == 2026)].dropna(subset=["firstPick", "result"])
    rows = []
    for side in ["Blue", "Red"]:
        for fp in [1, 0]:
            c = s[(s.side == side) & (s.firstPick == fp)]
            rows.append(dict(side=side, first_pick=("yes" if fp == 1 else "no"),
                             team_games=len(c),
                             win_rate=round(100 * c.result.mean(), 1) if len(c) else np.nan))
    return pd.DataFrame(rows)


def main():
    d = load_teamgames()

    t1 = sample_by_year(d)
    t1.to_csv(os.path.join(cfg.RESULTS_DIR, "paper_sample_by_year.csv"), index=False)
    print("== Sample by season ==\n", t1.to_string(index=False), "\n")

    t2 = side_early_outcomes(d)
    t2.to_csv(os.path.join(cfg.RESULTS_DIR, "paper_side_early_outcomes.csv"), index=False)
    print("== Blue-side differences in early-state variables (pooled) ==\n",
          t2.to_string(index=False), "\n")

    t3 = firstpick_crosstab(d)
    t3.to_csv(os.path.join(cfg.RESULTS_DIR, "paper_firstpick_crosstab.csv"), index=False)
    print("== 2026 side x first-pick ==\n", t3.to_string(index=False), "\n")

    # a few scalars the manuscript quotes
    s26 = d[(d.year == 2026)].dropna(subset=["firstPick"])
    print("2026 first-pick teams that are blue: %.1f%%" % (100 * s26[s26.firstPick == 1].blue.mean()))
    for y in sorted(d.year.unique()):
        sy = d[(d.year == y)].dropna(subset=["firstPick"])
        print("  %d: first-pick-is-blue share = %.3f" % (y, sy[sy.firstPick == 1].blue.mean()))
    print("\nWrote results/paper_*.csv")


if __name__ == "__main__":
    main()
