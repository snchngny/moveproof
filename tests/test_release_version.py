from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_release_version import project_version


class ReleaseVersionTests(unittest.TestCase):
    def test_reads_project_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pyproject = Path(directory) / "pyproject.toml"
            pyproject.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
            self.assertEqual(project_version(pyproject), "1.2.3")


if __name__ == "__main__":
    unittest.main()
