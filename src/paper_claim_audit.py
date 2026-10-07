#!/usr/bin/env python3
"""
Lightweight audit for paper-facing repo claims.

This intentionally uses only the Python standard library so it can run even when the
full analysis stack is unavailable. It checks that headline claims in the README and
methods note still agree with the committed results and figure inventory.

    python src/paper_claim_audit.py
"""
from __future__ import annotations

import csv
import math
import re
from pathlib import Path


EXPECTED_FILES = [
    Path("README.md"),
    Path("docs/METHODS.md"),
    Path("results/blue_or_by_year.csv"),
    Path("results/draft_value_ORs.csv"),
    Path("results/equivalence_tost.csv"),
    Path("results/fixed_effects_controls.csv"),
    Path("results/ml_model_comparison.csv"),
    Path("results/paper_sample_by_year.csv"),
]

EXPECTED_FIGURES = [
    "fig1_forest_draft_value.png",
    "fig2_blue_or_by_year.png",
    "fig3_did_eventstudy.png",
    "fig4_mediation_channels.png",
    "fig5_herald_engine_trend.png",
    "fig6_equivalence_tost.png",
    "fig7_matchup_vs_timing.png",
]

EXPECTED_EN_FIGURES = [
    "fig_en1_blue_or_by_season.png",
    "fig_en2_path_decomposition.png",
    "fig_en3_forest_draft_levers.png",
    "fig_en4_equivalence_tost.png",
    "fig_en5_did_event_study.png",
    "fig_en6_ml_validation.png",
]


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _rounded_range(values: list[float], digits: int) -> tuple[str, str]:
    return (f"{min(values):.{digits}f}", f"{max(values):.{digits}f}")


def audit_repository(root: Path) -> list[str]:
    failures: list[str] = []

    for relative_path in EXPECTED_FILES:
        if not (root / relative_path).exists():
            failures.append(f"Missing required file: {relative_path}")
    if failures:
        return failures

    readme = (root / "README.md").read_text(encoding="utf-8")
    methods = (root / "docs" / "METHODS.md").read_text(encoding="utf-8")
    blue_rows = _load_csv(root / "results" / "blue_or_by_year.csv")
    draft_rows = _load_csv(root / "results" / "draft_value_ORs.csv")
    tost_rows = _load_csv(root / "results" / "equivalence_tost.csv")
    fe_rows = _load_csv(root / "results" / "fixed_effects_controls.csv")
    ml_rows = _load_csv(root / "results" / "ml_model_comparison.csv")
    sample_rows = _load_csv(root / "results" / "paper_sample_by_year.csv")

    figure_dir = root / "figures"
    missing_figures = [name for name in EXPECTED_FIGURES if not (figure_dir / name).exists()]
    if missing_figures:
        failures.append(f"Missing expected figure files: {', '.join(missing_figures)}")

    en_dir = figure_dir / "en"
    missing_en_figures = [name for name in EXPECTED_EN_FIGURES if not (en_dir / name).exists()]
    if missing_en_figures:
        failures.append(f"Missing expected English paper figures: {', '.join(missing_en_figures)}")

    required_readme_snippets = [
        "fixed_effects_controls.py",
        "ml_validation.py",
        "paper_claim_audit.py",
        "results/ml_model_comparison.csv",
        "fig_en6_ml_validation.png",
        "English set in figures/en/",
    ]
    for snippet in required_readme_snippets:
        if snippet not in readme:
            failures.append(f"README should document `{snippet}`.")

    if "0/10 survive FDR" not in methods:
        failures.append("docs/METHODS.md should state that 0/10 counter-pick tests survive FDR.")
    if "10/10 counter-pick tests are statistically equivalent to null" not in methods:
        failures.append("docs/METHODS.md should state that 10/10 counter-pick tests are statistically equivalent to null.")
    if "GroupKFold" not in methods or "XGBoost" not in methods:
        failures.append("docs/METHODS.md should document the supplementary predictive validation workflow.")

    blue_ors = [float(row["OR"]) for row in blue_rows]
    or_lo, or_hi = _rounded_range(blue_ors, 2)
    expected_or_range = f"**OR {or_lo}–{or_hi}** each season"
    if expected_or_range not in readme:
        failures.append(f"README blue-side odds headline should match results/blue_or_by_year.csv: {expected_or_range}.")

    counterpick_rows = [row for row in draft_rows if row["label"].startswith("Counterpick ")]
    counterpick_fdr_hits = sum(float(row["p_fdr"]) < 0.05 for row in counterpick_rows)
    if len(counterpick_rows) != 10:
        failures.append(f"Expected 10 counter-pick rows in results/draft_value_ORs.csv, found {len(counterpick_rows)}.")
    if counterpick_fdr_hits != 0:
        failures.append(f"Expected 0/10 counter-pick FDR hits, found {counterpick_fdr_hits}/10.")
    if counterpick_fdr_hits == 0 and "**0/10** FDR-significant" not in readme:
        failures.append("README should summarize the counter-pick family as 0/10 FDR-significant.")

    equivalent_counterpicks = [
        row for row in tost_rows if row["param"].startswith("Counterpick ") and row["equivalent_10"] == "True"
    ]
    if len(equivalent_counterpicks) != 10:
        failures.append(
            f"Expected 10/10 counter-pick TOST equivalence results, found {len(equivalent_counterpicks)}/10."
        )

    expected_fe_models = [
        "Pooled LPM",
        "Own team-season FE",
        "Own team-season FE + opponent-team FE",
    ]
    actual_fe_models = [row["model"] for row in fe_rows]
    if actual_fe_models != expected_fe_models:
        failures.append(
            "results/fixed_effects_controls.csv should contain the pooled, own-team-season FE, "
            "and own-team-season plus opponent-team FE rows in order."
        )

    # Check the ordered narrative, not just model labels or broad effect ranges.
    # Whitespace normalization allows ordinary Markdown line wrapping.
    if actual_fe_models == expected_fe_models:
        try:
            effects = [float(row["blue_effect_pp"]) for row in fe_rows]
            if not all(math.isfinite(value) for value in effects):
                raise ValueError("non-finite estimate")
        except (KeyError, ValueError):
            failures.append("results/fixed_effects_controls.csv has invalid blue_effect_pp estimates.")
        else:
            expected_fe_claim = (
                f"from **{effects[0]:+.2f} percentage points** to **{effects[1]:+.2f} points** "
                f"with own-team-season fixed effects and **{effects[2]:+.2f} points** "
                "after opponent-team effects are added."
            )
            if expected_fe_claim not in re.sub(r"\s+", " ", readme):
                failures.append(
                    "README fixed-effects headline should match results/fixed_effects_controls.csv: "
                    + expected_fe_claim
                )

    ml_models = [row["model"] for row in ml_rows]
    expected_ml_models = ["Logistic regression", "Random forest", "XGBoost"]
    if ml_models != expected_ml_models:
        failures.append(
            "results/ml_model_comparison.csv should contain Logistic regression, Random forest, and XGBoost in order."
        )
    auc_lo, auc_hi = _rounded_range([float(row["cv_auc"]) for row in ml_rows], 3)
    expected_auc_range = f"**AUC {auc_lo}–{auc_hi}** across models"
    if expected_auc_range not in readme:
        failures.append(f"README predictive-triangulation row should match results/ml_model_comparison.csv: {expected_auc_range}.")

    sample_row = next((row for row in sample_rows if row["season"] == "All"), None)
    if sample_row is None:
        failures.append("results/paper_sample_by_year.csv should contain an `All` row.")
    else:
        expected_games = f"**{int(sample_row['games']):,} professional games**"
        if expected_games not in readme:
            failures.append(f"README headline sample size should match results/paper_sample_by_year.csv: {expected_games}.")

    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures = audit_repository(root)
    if failures:
        print("Paper-claim audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-claim audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
