"""
Data-driven top-lane champion archetypes (tank <-> carry axis), matching the wider
project's method:  carry_index = z(damageshare) - z(damagemitigatedperminute),
pooled over top-laner games (non-China, all seasons). Used only by robustness.py for
the champion-class heterogeneity cut.

Output: data/derived/champion_archetypes.csv  (champion, carry_index, archetype, n)
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

COLS = ["position", "champion", "league", "datacompleteness",
        "damageshare", "damagemitigatedperminute"]


def classify(ci: float) -> str:
    if ci <= -1.0: return "tank"
    if ci >= 0.6:  return "carry"
    return "bruiser"


def main():
    frames = []
    for y in (2022, 2023, 2024, 2025, 2026):
        p = C.find_raw(y)
        if p is None:
            continue
        d = pd.read_csv(p, usecols=lambda c: c in COLS, low_memory=False)
        d = d[(d.position == "top") & (~d.league.map(C.is_china))]
        if "datacompleteness" in d:
            d = d[d.datacompleteness == "complete"]
        frames.append(d[["champion", "damageshare", "damagemitigatedperminute"]])
    allt = pd.concat(frames, ignore_index=True).dropna()

    prof = allt.groupby("champion").agg(
        damageshare=("damageshare", "mean"),
        dmg_mit=("damagemitigatedperminute", "mean"),
        n=("champion", "size")).reset_index()
    prof = prof[prof.n >= 20]                      # stable estimate only
    zshare = (prof.damageshare - prof.damageshare.mean()) / prof.damageshare.std()
    zmit = (prof.dmg_mit - prof.dmg_mit.mean()) / prof.dmg_mit.std()
    prof["carry_index"] = zshare - zmit
    prof["archetype"] = prof["carry_index"].apply(classify)

    out = os.path.join(C.DERIVED_DIR, "champion_archetypes.csv")
    prof.sort_values("carry_index").to_csv(out, index=False)
    print(f"Wrote {out}  ({len(prof)} top champions)")
    print("archetype counts:", prof.archetype.value_counts().to_dict())
    print("most carry :", ", ".join(prof.sort_values('carry_index', ascending=False).champion.head(6)))
    print("most tank  :", ", ".join(prof.sort_values('carry_index').champion.head(6)))


if __name__ == "__main__":
    main()
