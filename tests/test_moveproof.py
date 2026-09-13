from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moveproof import (
    ScanIssue,
    compare_snapshots,
    create_snapshot,
    fingerprint_file,
    load_snapshot,
    save_snapshot,
)
from moveproof.cli import main


class FingerprintTests(unittest.TestCase):
    def test_small_files_with_different_content_have_different_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.bin"
            second = root / "second.bin"
            first.write_bytes(b"alpha")
            second.write_bytes(b"bravo")
            self.assertNotEqual(fingerprint_file(first), fingerprint_file(second))

    def test_sampled_fingerprint_reads_the_middle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.bin"
            path.write_bytes(b"a" * 40 + b"b" * 40 + b"c" * 40)
            before = fingerprint_file(path, sample_bytes=16)
            path.write_bytes(b"a" * 40 + b"x" * 40 + b"c" * 40)
            after = fingerprint_file(path, sample_bytes=16)
            self.assertNotEqual(before, after)

    def test_full_and_sampled_schemes_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value.bin"
            path.write_bytes(b"value")
            self.assertNotEqual(fingerprint_file(path), fingerprint_file(path, full=True))

    def test_sample_size_is_part_of_the_fingerprint_scheme(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value.bin"
            path.write_bytes(b"value")
            self.assertTrue(fingerprint_file(path, sample_bytes=7).startswith("moveproof-sampled-v1-7:"))

    def test_symlinks_are_not_fingerprinted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text("value", encoding="utf-8")
            link = root / "link"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            with self.assertRaisesRegex(OSError, "not a regular file"):
                fingerprint_file(link)


class SnapshotTests(unittest.TestCase):
    def test_snapshot_round_trip_and_change_classification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "keep.txt").write_text("keep", encoding="utf-8")
            (root / "move.txt").write_text("move", encoding="utf-8")
            (root / "remove.txt").write_text("remove", encoding="utf-8")
            (root / "modify.txt").write_text("before", encoding="utf-8")
            before = create_snapshot(root)

            (root / "move.txt").rename(root / "moved.txt")
            (root / "remove.txt").unlink()
            (root / "added.txt").write_text("added", encoding="utf-8")
            (root / "copy.txt").write_text("keep", encoding="utf-8")
            (root / "modify.txt").write_text("after", encoding="utf-8")
            after = create_snapshot(root)

            kinds = [change.kind for change in compare_snapshots(before, after).changes]
            self.assertEqual(kinds.count("unchanged"), 1)
            self.assertEqual(kinds.count("moved"), 1)
            self.assertEqual(kinds.count("modified"), 1)
            self.assertEqual(kinds.count("removed"), 1)
            self.assertEqual(kinds.count("added"), 1)
            self.assertEqual(kinds.count("copied"), 1)

            snapshot_path = root / "snapshot.json"
            save_snapshot(after, snapshot_path)
            self.assertEqual(load_snapshot(snapshot_path), after)

    def test_failed_snapshot_replace_preserves_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "file").write_text("value", encoding="utf-8")
            snapshot = create_snapshot(root)
            output = root / "snapshot.json"
            output.write_text("existing", encoding="utf-8")

            with patch("moveproof.snapshot.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    save_snapshot(snapshot, output)

            self.assertEqual(output.read_text(encoding="utf-8"), "existing")
            self.assertEqual(list(root.glob(".snapshot.json.*.tmp")), [])

    def test_hidden_files_are_excluded_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".hidden").write_text("hidden", encoding="utf-8")
            (root / "visible").write_text("visible", encoding="utf-8")
            self.assertEqual([item.path for item in create_snapshot(root).records], ["visible"])

    def test_scan_can_record_a_file_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            good = root / "good"
            bad = root / "bad"
            good.write_text("good", encoding="utf-8")
            bad.write_text("bad", encoding="utf-8")
            original = fingerprint_file

            def fingerprint_or_fail(path: Path, **options: object) -> tuple[str, int]:
                if path.name == "bad":
                    raise PermissionError("denied for test")
                value = original(path, **options)
                return value, path.stat().st_size

            with patch("moveproof.snapshot._fingerprint_with_size", side_effect=fingerprint_or_fail):
                snapshot = create_snapshot(root, on_error="record")

            self.assertEqual([record.path for record in snapshot.records], ["good"])
            self.assertEqual(snapshot.issues[0].path, "bad")
            self.assertEqual(snapshot.issues[0].error_type, "PermissionError")

    def test_incomplete_snapshots_are_rejected_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "file").write_text("value", encoding="utf-8")
            complete = create_snapshot(root)
            incomplete = type(complete)(
                root=complete.root,
                mode=complete.mode,
                records=complete.records,
                issues=(ScanIssue("missing", "PermissionError", "denied"),),
                sample_bytes=complete.sample_bytes,
            )
            with self.assertRaisesRegex(ValueError, "incomplete snapshots"):
                compare_snapshots(complete, incomplete)
            self.assertEqual(
                compare_snapshots(complete, incomplete, allow_incomplete=True).changes[0].kind,
                "unchanged",
            )

    def test_different_modes_cannot_be_compared(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "file").write_text("value", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "different fingerprint modes"):
                compare_snapshots(create_snapshot(root), create_snapshot(root, full=True))

    def test_different_sample_sizes_cannot_be_compared(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "file").write_text("value", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "different sample sizes"):
                compare_snapshots(
                    create_snapshot(root, sample_bytes=8),
                    create_snapshot(root, sample_bytes=16),
                )

    def test_cli_writes_machine_readable_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "media"
            media.mkdir()
            (media / "file").write_text("value", encoding="utf-8")
            before = root / "before.json"
            after = root / "after.json"
            output = root / "changes.json"
            self.assertEqual(main(["snapshot", str(media), "-o", str(before)]), 0)
            (media / "file").rename(media / "renamed")
            self.assertEqual(main(["snapshot", str(media), "-o", str(after)]), 0)
            self.assertEqual(main(["compare", str(before), str(after), "-o", str(output)]), 0)
            value = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(value["changes"][0]["kind"], "moved")
            self.assertEqual(value["changes"][0]["old"]["path"], "file")
            self.assertEqual(value["changes"][0]["new"]["path"], "renamed")


if __name__ == "__main__":
    unittest.main()
