from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from moveproof import classify_extension, create_inventory
from moveproof.cli import main


class InventoryTests(unittest.TestCase):
    def test_inventory_counts_without_reading_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "audio").mkdir()
            (root / "audio" / "kick.WAV").write_bytes(b"1234")
            (root / "audio" / "library.nki").write_bytes(b"12")
            (root / "container.ncw").write_bytes(b"123")
            (root / "README").write_bytes(b"1")

            report = create_inventory(root)

            self.assertEqual(report.total_files, 4)
            self.assertEqual(report.total_bytes, 10)
            self.assertEqual(
                [(item.extension, item.files) for item in report.extensions],
                [(".ncw", 1), (".nki", 1), (".wav", 1), ("[no extension]", 1)],
            )
            self.assertEqual(report.categories["audio"]["files"], 1)
            self.assertEqual(report.categories["instrument_preset"]["files"], 1)
            self.assertEqual(report.categories["sample_container"]["files"], 1)
            self.assertEqual(report.categories["other"]["files"], 1)

    def test_hidden_files_are_optional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".hidden.wav").write_bytes(b"hidden")
            self.assertEqual(create_inventory(root).total_files, 0)
            self.assertEqual(create_inventory(root, include_hidden=True).total_files, 1)

    def test_classification_is_case_insensitive(self) -> None:
        self.assertEqual(classify_extension(".WAV"), "audio")
        self.assertEqual(classify_extension(".NKI"), "instrument_preset")
        self.assertEqual(classify_extension(".unknown"), "other")

    def test_cli_writes_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.wav").write_bytes(b"sample")
            output = root / "inventory.json"

            self.assertEqual(main(["inventory", str(root), "-o", str(output)]), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["total_files"], 1)
            self.assertEqual(report["extensions"][0]["extension"], ".wav")


if __name__ == "__main__":
    unittest.main()
