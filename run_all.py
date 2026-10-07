#!/usr/bin/env python3
"""
Reproduce everything.

    python run_all.py              # analysis + figures from the committed derived table
    python run_all.py --from-raw   # also rebuild data/derived/* from data/raw/ CSVs

The default path needs no raw data: it reads data/derived/redblue_teamgames.csv.gz
(committed) and regenerates every table in results/ and every figure in figures/.
"""
from __future__ import annotations
import argparse, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
sys.path.insert(0, SRC)

from runtime import configure_matplotlib_env

BUILD = ["build_dataset.py", "champion_archetypes.py"]        # need data/raw
ANALYSIS = ["audit_data.py",                                   # validate before analysing
            "model_draft_value.py", "team_strength.py",
            "fixed_effects_controls.py",
            "mediation_path.py", "mediation_full.py",
            "did_first_selection.py", "robustness.py",
            "matchup_quality.py", "equivalence_tost.py", "ml_validation.py",
            "paper_tables.py", "figures.py", "figures_paper_en.py"]


def run(script: str):
    print(f"\n{'='*70}\n▶ {script}\n{'='*70}")
    t = time.time()
    r = subprocess.run([sys.executable, os.path.join(SRC, script)])
    if r.returncode != 0:
        sys.exit(f"✗ {script} failed (exit {r.returncode})")
    print(f"✓ {script}  ({time.time()-t:.1f}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-raw", action="store_true",
                    help="rebuild the derived table + archetypes from data/raw/ first")
    args = ap.parse_args()
    configure_matplotlib_env(HERE)
    steps = (BUILD if args.from_raw else []) + ANALYSIS
    print("Pipeline:", " -> ".join(steps))
    for s in steps:
        run(s)
    print("\n✅ Done. See results/ (tables + logs) and figures/ (PNGs).")


if __name__ == "__main__":
    main()
