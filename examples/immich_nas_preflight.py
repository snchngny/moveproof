"""Reproduce a read-only preflight for an Immich external-library NAS move."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from moveproof import check_library_guard, create_reconciliation_plan, create_snapshot


def main() -> None:
    with TemporaryDirectory(prefix="moveproof-immich-nas-") as temporary_directory:
        workspace = Path(temporary_directory)
        old_root = workspace / "old-nas" / "photos"
        trip_photo = old_root / "2024" / "trip" / "photo.jpg"
        archive_photo = old_root / "2023" / "archive.jpg"
        trip_photo.parent.mkdir(parents=True)
        archive_photo.parent.mkdir(parents=True)
        trip_photo.write_bytes(b"trip photo")
        archive_photo.write_bytes(b"archive photo")

        baseline = create_snapshot(old_root, full=True)

        new_nas = workspace / "new-nas"
        old_root.parent.rename(new_nas)
        new_root = new_nas / "photos"
        current = create_snapshot(new_root, full=True)

        root_guard = check_library_guard(baseline, current, max_missing_ratio=0)
        root_plan = create_reconciliation_plan(baseline, current)

        before_rename = current
        renamed_directory = new_root / "2024" / "vacation"
        (new_root / "2024" / "trip").rename(renamed_directory)
        after_rename = create_snapshot(new_root, full=True)
        rename_plan = create_reconciliation_plan(before_rename, after_rename)

        empty_mount = workspace / "empty-mount"
        empty_mount.mkdir()
        empty_guard = check_library_guard(
            baseline,
            create_snapshot(empty_mount, full=True),
            max_missing_ratio=0,
        )

        result = {
            "root_move": {
                "safe_to_continue": root_guard.safe_to_continue,
                "safe_to_apply": root_plan.safe_to_apply,
                "verified": root_plan.root_move is not None,
                "file_count": root_plan.root_move.file_count
                if root_plan.root_move
                else 0,
            },
            "folder_rename": {
                "safe_to_apply": rename_plan.safe_to_apply,
                "moves": [
                    {"old_path": move.old_path, "new_path": move.new_path}
                    for move in rename_plan.moves
                ],
            },
            "empty_mount": {
                "safe_to_continue": empty_guard.safe_to_continue,
                "reasons": list(empty_guard.reasons),
            },
        }
        assert result == {
            "root_move": {
                "safe_to_continue": True,
                "safe_to_apply": True,
                "verified": True,
                "file_count": 2,
            },
            "folder_rename": {
                "safe_to_apply": True,
                "moves": [
                    {
                        "old_path": "2024/trip/photo.jpg",
                        "new_path": "2024/vacation/photo.jpg",
                    }
                ],
            },
            "empty_mount": {
                "safe_to_continue": False,
                "reasons": ["library_empty", "missing_ratio_exceeded"],
            },
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
