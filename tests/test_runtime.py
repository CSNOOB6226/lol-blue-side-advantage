import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR))

import runtime  # type: ignore  # noqa: E402


class RuntimeTests(unittest.TestCase):
    def test_repo_ignores_generated_matplotlib_cache(self) -> None:
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".mplconfig/", gitignore)

    def test_configure_matplotlib_env_uses_repo_local_cache_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp)
            with mock.patch.dict(os.environ, {}, clear=True):
                configured = runtime.configure_matplotlib_env(repo_root)
                expected = repo_root / ".mplconfig"
                self.assertEqual(configured, expected)
                self.assertEqual(pathlib.Path(os.environ["MPLCONFIGDIR"]), expected)
                self.assertTrue(expected.is_dir())

    def test_configure_matplotlib_env_respects_existing_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = pathlib.Path(tmp) / "repo"
            override = pathlib.Path(tmp) / "custom-cache"
            with mock.patch.dict(os.environ, {"MPLCONFIGDIR": str(override)}, clear=True):
                configured = runtime.configure_matplotlib_env(repo_root)
                self.assertEqual(configured, override)
                self.assertEqual(pathlib.Path(os.environ["MPLCONFIGDIR"]), override)
                self.assertTrue(override.is_dir())


if __name__ == "__main__":
    unittest.main()
