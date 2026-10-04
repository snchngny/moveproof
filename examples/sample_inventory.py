"""一時フォルダだけで混在ライブラリの集計を試す例。実音源は使わない。"""

import json
import tempfile
from pathlib import Path

from moveproof import create_inventory


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name, size in {"kick.wav": 8, "instrument.nki": 4, "notes.txt": 2}.items():
            (root / name).write_bytes(b"x" * size)
        report = create_inventory(root)
        assert report.total_files == 3
        assert report.total_bytes == 14
        assert not report.issues
        print(json.dumps({
            "total_files": report.total_files,
            "total_bytes": report.total_bytes,
            "categories": report.categories,
        }, indent=2))


if __name__ == "__main__":
    main()
