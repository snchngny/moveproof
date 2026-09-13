from __future__ import annotations

import json
from pathlib import Path

from .fingerprint import DEFAULT_SAMPLE_BYTES, _fingerprint_with_size
from .model import FileRecord, Snapshot


def create_snapshot(
    root: str | Path,
    *,
    full: bool = False,
    include_hidden: bool = False,
    sample_bytes: int = DEFAULT_SAMPLE_BYTES,
) -> Snapshot:
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise NotADirectoryError(root_path)

    records: list[FileRecord] = []
    for path in sorted(root_path.rglob("*")):
        relative = path.relative_to(root_path)
        if not include_hidden and any(part.startswith(".") for part in relative.parts):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        fingerprint, size = _fingerprint_with_size(
            path,
            full=full,
            sample_bytes=sample_bytes,
        )
        records.append(
            FileRecord(
                path=relative.as_posix(),
                size=size,
                fingerprint=fingerprint,
            )
        )

    return Snapshot(
        root=str(root_path),
        mode="full" if full else "sampled",
        records=tuple(records),
        sample_bytes=None if full else sample_bytes,
    )


def save_snapshot(snapshot: Snapshot, path: str | Path) -> None:
    output = Path(path)
    output.write_text(
        json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_snapshot(path: str | Path) -> Snapshot:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("snapshot must be a JSON object")
    return Snapshot.from_dict(value)
