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
