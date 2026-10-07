"""
Data-integrity gate for the derived team-game table. Run after build_dataset.py.

Hard checks (exit non-zero on failure) verify the structural invariants every model
relies on; soft checks print informative diagnostics. Keeping this in the repo makes the
"is the data correct?" question answerable by anyone, and fails loudly if a future data
refresh breaks an assumption.

    python src/audit_data.py
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfg

FAILS = 0
def hard(name, cond, detail=""):
    global FAILS
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}   {detail}")
    if not cond:
        FAILS += 1
def soft(name, detail=""):
    print(f"  [info] {name}   {detail}")


def main():
    d = pd.read_csv(cfg.DERIVED_TEAMGAMES, low_memory=False)
    print(f"AUDIT  {cfg.DERIVED_TEAMGAMES}\n  rows={len(d):,}  cols={d.shape[1]}  games={d.gameid.nunique():,}\n")

    print(" STRUCTURAL (must pass):")
    hard("each gameid maps to exactly one season", (d.groupby('gameid').year.nunique() == 1).all())
    rc = d.groupby("gameid").size()
    hard("exactly 2 team-rows per game", (rc == 2).all(), f"(bad={int((rc != 2).sum())})")
    hard("no duplicate (gameid, side)", not d.duplicated(["gameid", "side"]).any())
    sd = d.groupby("gameid").side.apply(lambda s: sorted(s) == ["Blue", "Red"])
    hard("each game is exactly Blue + Red", sd.all(), f"(bad={int((~sd).sum())})")
    rs = d.groupby("gameid").result.agg(lambda s: (s == 1).sum() == 1 and (s == 0).sum() == 1)
    hard("exactly one win + one loss per game", rs.all(), f"(bad={int((~rs).sum())})")
    hard("result is binary {0,1}", set(pd.unique(d.result.dropna())) <= {0, 1})
    hard("blue flag matches side", (d.blue == (d.side == "Blue").astype(int)).all())
    hard("no China (LPL/LDL) leagues", not any(cfg.is_china(l) for l in d.league.unique()))
    for col in ["top_gap", "golddiffat15"]:
        piv = d.pivot_table(index="gameid", columns="side", values=col, aggfunc="first").dropna()
        frac = np.isclose(piv["Blue"], -piv["Red"], atol=1).mean()
        hard(f"{col} is mirror-symmetric (blue = -red)", frac > 0.999, f"(frac={frac:.4f})")

    print("\n DIAGNOSTICS (informational):")
    soft("firstPick blue-share by year",
         {int(y): round(d[(d.year == y) & (d.firstPick == 1)].blue.mean(), 3) for y in sorted(d.year.unique())})
    soft("games per season", {int(y): int((d.year == y).sum() // 2) for y in sorted(d.year.unique())})
    soft("clean-reconstruction share", round(d.clean_reconstruction.mean(), 3))
    extreme = int((d.golddiffat15.abs() > 15000).sum())
    soft("games with |golddiff@15| > 15k (rare blowouts, kept)", extreme)

    print()
    if FAILS:
        sys.exit(f"❌ AUDIT FAILED: {FAILS} structural check(s) failed.")
    print("✅ AUDIT PASSED: all structural invariants hold.")


if __name__ == "__main__":
    main()
