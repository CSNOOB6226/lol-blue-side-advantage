import csv
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED_PATH = REPO_ROOT / "docs" / "literature_seed.csv"


class LiteratureSeedTests(unittest.TestCase):
    def test_seed_records_have_unique_dois_and_required_fields(self) -> None:
        with SEED_PATH.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertGreaterEqual(len(rows), 3)
        required = {"status", "topic", "title", "year", "doi", "url", "relevance", "next_step"}
        self.assertEqual(set(rows[0]), required)
        self.assertTrue(all(all(row[field].strip() for field in required) for row in rows))

        dois = [row["doi"].lower() for row in rows]
        self.assertEqual(len(dois), len(set(dois)))
        self.assertTrue(all(row["url"] == f"https://doi.org/{row['doi']}" for row in rows))


if __name__ == "__main__":
    unittest.main()
