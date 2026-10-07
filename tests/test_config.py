import pathlib
import sys
import unittest


SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import config  # type: ignore  # noqa: E402


class ConfigTests(unittest.TestCase):
    def test_is_china_only_matches_exact_lpl_ldl_codes(self) -> None:
        self.assertTrue(config.is_china("LPL"))
        self.assertTrue(config.is_china("LDL"))
        self.assertTrue(config.is_china(" LDL "))
        self.assertFalse(config.is_china("LPLOL"))
        self.assertFalse(config.is_china("LCK"))
        self.assertFalse(config.is_china(""))


if __name__ == "__main__":
    unittest.main()
