import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from paper_claim_audit import audit_repository  # noqa: E402


class PaperClaimAuditTests(unittest.TestCase):
    def test_repository_claim_audit_passes(self) -> None:
        self.assertEqual(audit_repository(ROOT), [])

    def test_audit_rejects_changed_or_invalid_fixed_effects(self) -> None:
        # Mutate each stage independently: these changes passed the old audit.
        for index, value in [(0, "5.90"), (1, "5.60"), (2, "4.70"),
                             (0, "nan"), (1, "inf"), (2, "")]:
            with self.subTest(index=index, value=value), tempfile.TemporaryDirectory() as tmpdir:
                repo = Path(tmpdir)
                for directory in ["results", "figures", "docs"]:
                    shutil.copytree(ROOT / directory, repo / directory)
                shutil.copy2(ROOT / "README.md", repo / "README.md")
                path = repo / "results/fixed_effects_controls.csv"
                with path.open(newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    fields = reader.fieldnames
                    rows = list(reader)
                rows[index]["blue_effect_pp"] = value
                with path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                failures = audit_repository(repo)
                self.assertTrue(any("fixed_effects_controls.csv" in f for f in failures), failures)

    def test_audit_flags_missing_ml_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            shutil.copytree(ROOT / "results", repo / "results")
            shutil.copytree(ROOT / "figures", repo / "figures")
            shutil.copytree(ROOT / "docs", repo / "docs")

            readme = (ROOT / "README.md").read_text(encoding="utf-8")
            readme = readme.replace("results/ml_model_comparison.csv", "results/ml_summary.csv")
            (repo / "README.md").write_text(readme, encoding="utf-8")

            failures = audit_repository(repo)

            self.assertTrue(
                any("results/ml_model_comparison.csv" in failure for failure in failures),
                failures,
            )


if __name__ == "__main__":
    unittest.main()
