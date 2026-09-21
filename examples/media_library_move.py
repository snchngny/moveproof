"""Try a safe media-library move using only a temporary directory."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from moveproof import create_reconciliation_plan, create_snapshot


def main() -> None:
    with TemporaryDirectory(prefix="moveproof-demo-") as temporary_directory:
        media_root = Path(temporary_directory) / "media"
        original_path = media_root / "samples" / "kick.wav"
        original_path.parent.mkdir(parents=True)
        original_path.write_bytes(b"example audio content")

        before = create_snapshot(media_root, full=True)

        moved_path = media_root / "archive" / "kick.wav"
        moved_path.parent.mkdir()
        original_path.rename(moved_path)

        after = create_snapshot(media_root, full=True)
        plan = create_reconciliation_plan(before, after)

        result = {
            "safe_to_apply": plan.safe_to_apply,
            "moves": [
                {"old_path": move.old_path, "new_path": move.new_path}
                for move in plan.moves
            ],
        }
        assert result == {
            "safe_to_apply": True,
            "moves": [
                {"old_path": "samples/kick.wav", "new_path": "archive/kick.wav"}
            ],
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
