import csv
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"


def _read_rows(name: str) -> list[dict[str, str]]:
    path = RESULTS_DIR / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ResultRegressionTests(unittest.TestCase):
    def test_signed_leads_use_one_blue_row_per_game(self) -> None:
        rows = _read_rows("paper_side_early_outcomes.csv")
        expected = {
            "Gold difference at 10 min (mean blue lead)": (43036, 124.10, 110.07, 138.14),
            "Gold difference at 15 min (mean blue lead)": (43035, 274.61, 246.26, 302.95),
            "XP difference at 15 min (mean blue lead)": (43035, 51.95, 32.19, 71.71),
        }
        by_outcome = {row["outcome"]: row for row in rows}
        for outcome, (n, effect, lo, hi) in expected.items():
            with self.subTest(outcome=outcome):
                row = by_outcome[outcome]
                self.assertEqual(int(row["n"]), n)
                for field, value in [("blue_effect", effect), ("ci_lo", lo), ("ci_hi", hi)]:
                    self.assertAlmostEqual(float(row[field]), value, delta=0.05)

    def test_grubs_contrast_uses_the_2024_onward_sample(self) -> None:
        rows = _read_rows("paper_side_early_outcomes.csv")
        row = next(row for row in rows if row["outcome"].startswith("Void grubs"))
        self.assertIn("blue minus red", row["outcome"])
        self.assertEqual(int(row["n"]), 46048)
        self.assertAlmostEqual(float(row["blue_effect"]), 0.984016678, delta=0.01)

    def test_full_rank_elo_model_preserves_published_fit(self) -> None:
        rows = _read_rows("team_strength_R2.csv")
        draft = next(row for row in rows if row["model"] == "strength+side+draft")
        self.assertAlmostEqual(float(draft["mcfadden_r2"]), 0.0925618476, delta=0.0001)

    def test_blue_side_or_stays_in_published_five_year_band(self) -> None:
        rows = _read_rows("blue_or_by_year.csv")
        years = [int(row["year"]) for row in rows]
        ors = [float(row["OR"]) for row in rows]

        self.assertEqual(years, [2022, 2023, 2024, 2025, 2026])
        self.assertTrue(all(1.20 <= value <= 1.35 for value in ors))

    def test_counterpick_family_remains_non_significant_after_fdr(self) -> None:
        rows = _read_rows("draft_value_ORs.csv")
        counterpick = [row for row in rows if row["label"].startswith("Counterpick")]

        self.assertEqual(len(counterpick), 10)
        self.assertTrue(all(float(row["p_fdr"]) > 0.05 for row in counterpick))

    def test_equivalence_results_keep_counterpick_nulls_and_blue_contrast(self) -> None:
        rows = _read_rows("equivalence_tost.csv")
        counterpick = [row for row in rows if row["param"].startswith("Counterpick")]
        blue = next(row for row in rows if row["param"] == "Blue side (2026)")
        first_pick = next(row for row in rows if row["param"] == "First pick (2026)")

        self.assertEqual(len(counterpick), 10)
        self.assertTrue(all(row["equivalent_10"] == "True" for row in counterpick))
        self.assertEqual(blue["equivalent_10"], "False")
        self.assertEqual(first_pick["equivalent_10"], "False")

    def test_fixed_effects_controls_keep_a_positive_blue_side_effect(self) -> None:
        rows = _read_rows("fixed_effects_controls.csv")
        self.assertEqual(
            [row["model"] for row in rows],
            [
                "Pooled LPM",
                "Own team-season FE",
                "Own team-season FE + opponent-team FE",
            ],
        )
        effects = [float(row["blue_effect_pp"]) for row in rows]
        self.assertTrue(all(value > 0.0 for value in effects))
        self.assertGreater(effects[0], effects[1])
        self.assertGreater(effects[1], effects[2])
        self.assertTrue(5.0 <= effects[0] <= 6.5)
        self.assertTrue(5.0 <= effects[1] <= 6.2)
        self.assertTrue(4.0 <= effects[2] <= 5.2)

    def test_ml_validation_keeps_models_close_and_blue_increment_small(self) -> None:
        rows = _read_rows("ml_model_comparison.csv")

        self.assertEqual(
            [row["model"] for row in rows],
            ["Logistic regression", "Random forest", "XGBoost"],
        )
        aucs = [float(row["cv_auc"]) for row in rows]
        delta_blue = [float(row["cv_delta_auc_blue"]) for row in rows]

        self.assertTrue(all(0.82 <= auc <= 0.85 for auc in aucs))
        self.assertLess(max(aucs) - min(aucs), 0.01)
        self.assertTrue(all(0.0 <= delta <= 0.002 for delta in delta_blue))


if __name__ == "__main__":
    unittest.main()
