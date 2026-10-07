"""
Out-of-sample model comparison for the paper's early-state feature set.

Purpose
-------
This analysis does not identify causal effects.  It asks a narrower predictive
question: under the same information set, does a flexible tree ensemble provide
materially better out-of-sample discrimination than the paper's interpretable
logistic benchmark?

Models
------
* Logistic regression, with standardisation fitted inside each training fold.
* Random forest (300 trees, maximum depth 8).
* XGBoost (300 boosting rounds, maximum depth 4, learning rate 0.10).

Validation
----------
* Five-fold GroupKFold, grouped by gameid so the two mirrored team-game rows
  from one match never appear in different folds.
* Two chronological checks: train through 2024/test 2025 and train through
  2025/test 2026.
* AUC, log loss, and Brier score are reported.  The incremental AUC of `blue`
  is computed against the same model fitted without `blue`.

Outputs
-------
* results/ml_model_comparison.csv
* results/ml_fold_metrics.csv
* results/ml_feature_importance.csv
* figures/en/fig_en6_ml_validation.png
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime import configure_matplotlib_env

configure_matplotlib_env(Path(__file__).resolve().parents[1])

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

import config as C
from utils import load_teamgames


FEATURES = [
    "blue",
    "golddiffat10",
    "golddiffat15",
    "xpdiffat10",
    "xpdiffat15",
    "firstherald",
    "firstdragon",
    "firsttower",
    "firstblood",
    "void_grubs",
]

PRETTY = {
    "blue": "Blue side",
    "golddiffat10": "Gold difference at 10",
    "golddiffat15": "Gold difference at 15",
    "xpdiffat10": "XP difference at 10",
    "xpdiffat15": "XP difference at 15",
    "firstherald": "First herald",
    "firstdragon": "First dragon",
    "firsttower": "First tower",
    "firstblood": "First blood",
    "void_grubs": "Void-grub count",
}

RANDOM_STATE = 20260826


def make_model(name: str):
    if name == "Logistic regression":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", LogisticRegression(max_iter=2_000, C=1.0, random_state=RANDOM_STATE)),
            ]
        )
    if name == "Random forest":
        return RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=5,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )
    if name == "XGBoost":
        return XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.10,
            subsample=0.90,
            colsample_bytree=0.90,
            objective="binary:logistic",
            eval_metric="logloss",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )
    raise KeyError(name)


def metric_row(y: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    return {
        "auc": float(roc_auc_score(y, probability)),
        "log_loss": float(log_loss(y, probability)),
        "brier": float(brier_score_loss(y, probability)),
    }


def fit_predict(name: str, x_train: pd.DataFrame, y_train: np.ndarray,
                x_test: pd.DataFrame) -> tuple[object, np.ndarray]:
    model = make_model(name)
    model.fit(x_train, y_train)
    probability = model.predict_proba(x_test)[:, 1]
    return model, probability


def grouped_cross_validation(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    y = d["result"].to_numpy(int)
    groups = d["gameid"].to_numpy()
    splitter = GroupKFold(n_splits=5)
    model_names = ["Logistic regression", "Random forest", "XGBoost"]
    rows: list[dict[str, float | int | str]] = []
    importance_rows: list[dict[str, float | int | str]] = []

    for fold, (train, test) in enumerate(splitter.split(d[FEATURES], y, groups), start=1):
        x_train = d.iloc[train][FEATURES]
        x_test = d.iloc[test][FEATURES]
        y_train, y_test = y[train], y[test]
        structural = [f for f in FEATURES if f != "blue"]

        for name in model_names:
            fitted, probability = fit_predict(name, x_train, y_train, x_test)
            _, probability_no_blue = fit_predict(
                name, x_train[structural], y_train, x_test[structural]
            )
            metrics = metric_row(y_test, probability)
            auc_no_blue = roc_auc_score(y_test, probability_no_blue)
            rows.append(
                {
                    "validation": "GroupKFold",
                    "fold": fold,
                    "model": name,
                    **metrics,
                    "auc_without_blue": float(auc_no_blue),
                    "delta_auc_blue": float(metrics["auc"] - auc_no_blue),
                    "n_test_team_games": int(len(test)),
                    "n_test_games": int(d.iloc[test]["gameid"].nunique()),
                }
            )

            if name == "Random forest":
                perm = permutation_importance(
                    fitted,
                    x_test,
                    y_test,
                    n_repeats=5,
                    random_state=RANDOM_STATE + fold,
                    scoring="roc_auc",
                    # Single-process scoring avoids platform semaphore limits and
                    # leaves the statistical calculation unchanged.
                    n_jobs=1,
                )
                for feature, mean, sd in zip(
                    FEATURES, perm.importances_mean, perm.importances_std
                ):
                    importance_rows.append(
                        {
                            "fold": fold,
                            "feature": feature,
                            "permutation_auc_drop": float(mean),
                            "repeat_sd": float(sd),
                        }
                    )

    return pd.DataFrame(rows), pd.DataFrame(importance_rows)


def chronological_validation(d: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    tests = [(2024, 2025), (2025, 2026)]
    for train_through, test_year in tests:
        train = d[d["year"] <= train_through]
        test = d[d["year"] == test_year]
        for name in ("Logistic regression", "Random forest", "XGBoost"):
            _, probability = fit_predict(
                name,
                train[FEATURES],
                train["result"].to_numpy(int),
                test[FEATURES],
            )
            rows.append(
                {
                    "validation": f"Train <= {train_through}; test {test_year}",
                    "fold": test_year,
                    "model": name,
                    **metric_row(test["result"].to_numpy(int), probability),
                    "auc_without_blue": np.nan,
                    "delta_auc_blue": np.nan,
                    "n_test_team_games": int(len(test)),
                    "n_test_games": int(test["gameid"].nunique()),
                }
            )
    return pd.DataFrame(rows)


def summarize(folds: pd.DataFrame, chronological: pd.DataFrame) -> pd.DataFrame:
    summary = (
        folds.groupby("model", sort=False)
        .agg(
            cv_auc=("auc", "mean"),
            cv_auc_sd=("auc", "std"),
            cv_log_loss=("log_loss", "mean"),
            cv_brier=("brier", "mean"),
            cv_delta_auc_blue=("delta_auc_blue", "mean"),
        )
        .reset_index()
    )
    oot = chronological.pivot(index="model", columns="fold", values="auc").reset_index()
    oot = oot.rename(columns={2025: "oot_auc_2025", 2026: "oot_auc_2026"})
    return summary.merge(oot, on="model", how="left")


def summarize_importance(importance: pd.DataFrame) -> pd.DataFrame:
    return (
        importance.groupby("feature", sort=False)
        .agg(
            permutation_auc_drop=("permutation_auc_drop", "mean"),
            fold_sd=("permutation_auc_drop", "std"),
        )
        .reset_index()
        .sort_values("permutation_auc_drop", ascending=False)
    )


def make_figure(summary: pd.DataFrame, importance: pd.DataFrame) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlesize": 11,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.25), gridspec_kw={"width_ratios": [0.9, 1.3]})

    colors = ["#1F4D78", "#6B7A8F", "#A06A2B"]
    x = np.arange(len(summary))
    axes[0].bar(
        x,
        summary["cv_auc"],
        yerr=summary["cv_auc_sd"],
        capsize=3,
        color=colors,
        width=0.64,
    )
    axes[0].set_xticks(x, ["Logistic", "Random\nforest", "XGBoost"])
    axes[0].set_ylim(0.81, 0.85)
    axes[0].set_ylabel("Five-fold grouped CV AUC")
    axes[0].set_title("A. Predictive discrimination")
    axes[0].grid(axis="y", color="#D8DDE3", linewidth=0.6)
    for i, value in enumerate(summary["cv_auc"]):
        axes[0].text(i, value + 0.0023, f"{value:.3f}", ha="center", va="bottom", fontsize=8.5)

    shown = importance.head(8).sort_values("permutation_auc_drop")
    axes[1].barh(
        [PRETTY[x] for x in shown["feature"]],
        shown["permutation_auc_drop"],
        xerr=shown["fold_sd"].fillna(0),
        color="#1F4D78",
        capsize=2,
    )
    axes[1].set_xlabel("Random-forest permutation importance (AUC decrease)")
    axes[1].set_title("B. Early-state feature importance")
    axes[1].grid(axis="x", color="#D8DDE3", linewidth=0.6)

    fig.tight_layout(w_pad=2.0)
    out = os.path.join(C.FIGURES_DIR, "en", "fig_en6_ml_validation.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    d = load_teamgames().copy()
    # Before 2024 the mechanic did not exist, so zero is the structural value.
    d["void_grubs"] = d["void_grubs"].fillna(0)
    d = d.dropna(subset=FEATURES + ["result", "gameid", "year"]).copy()

    folds, raw_importance = grouped_cross_validation(d)
    chronological = chronological_validation(d)
    all_metrics = pd.concat([folds, chronological], ignore_index=True)
    summary = summarize(folds, chronological)
    importance = summarize_importance(raw_importance)

    # Limit serialized precision so harmless platform-level floating-point noise
    # does not leave a dirty tree after a successful reproduction run.
    csv_options = {"index": False, "float_format": "%.15g"}
    all_metrics.to_csv(os.path.join(C.RESULTS_DIR, "ml_fold_metrics.csv"), **csv_options)
    summary.to_csv(os.path.join(C.RESULTS_DIR, "ml_model_comparison.csv"), **csv_options)
    importance.to_csv(os.path.join(C.RESULTS_DIR, "ml_feature_importance.csv"), **csv_options)
    make_figure(summary, importance)

    print(f"ML sample: {len(d):,} team-games / {d.gameid.nunique():,} games")
    print("\nMODEL COMPARISON")
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print("\nRANDOM-FOREST PERMUTATION IMPORTANCE")
    print(importance.to_string(index=False, float_format=lambda value: f"{value:.5f}"))
    print("\nWrote results/ml_*.csv and figures/en/fig_en6_ml_validation.png")


if __name__ == "__main__":
    main()
