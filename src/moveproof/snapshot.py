from __future__ import annotations

import fnmatch
import json
import os
import tempfile
from pathlib import Path
from typing import Callable, Iterator, Sequence

from .fingerprint import DEFAULT_SAMPLE_BYTES, _fingerprint_with_size
from .model import ErrorPolicy, FileRecord, ScanIssue, Snapshot


def _relative_display(root: Path, path: Path) -> str:
    try:
        value = path.relative_to(root).as_posix()
        return value or "."
    except ValueError:
        return str(path)


def _walk_files(
    root: Path,
    *,
    include_hidden: bool,
    handle_error: Callable[[Path, OSError], None],
) -> Iterator[Path]:
    def on_error(error: OSError) -> None:
        handle_error(Path(error.filename) if error.filename else root, error)

    for directory, directory_names, file_names in os.walk(
        root,
        topdown=True,
        onerror=on_error,
        followlinks=False,
    ):
        directory_path = Path(directory)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if (include_hidden or not name.startswith("."))
            and not (directory_path / name).is_symlink()
        )
        for name in sorted(file_names):
            if not include_hidden and name.startswith("."):
                continue
            path = directory_path / name
            if not path.is_symlink():
                yield path


def create_snapshot(
    root: str | Path,
    *,
    full: bool = False,
    include_hidden: bool = False,
    sample_bytes: int = DEFAULT_SAMPLE_BYTES,
    on_error: ErrorPolicy = "raise",
    include_patterns: Sequence[str] = (),
    exclude_patterns: Sequence[str] = (),
) -> Snapshot:
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise NotADirectoryError(root_path)

    if on_error not in {"raise", "record"}:
        raise ValueError(f"unsupported error policy: {on_error}")
    includes = tuple(sorted(set(include_patterns)))
    excludes = tuple(sorted(set(exclude_patterns)))
    if any(not pattern for pattern in includes + excludes):
        raise ValueError("include and exclude patterns cannot be empty")

    records: list[FileRecord] = []
    issues: list[ScanIssue] = []

    def handle_error(path: Path, error: OSError) -> None:
        if on_error == "raise":
            raise error
        issues.append(
            ScanIssue(
                path=_relative_display(root_path, path),
                error_type=type(error).__name__,
                message=error.strerror or str(error),
            )
        )

    for path in _walk_files(
        root_path,
        include_hidden=include_hidden,
        handle_error=handle_error,
    ):
        relative = path.relative_to(root_path)
        relative_name = relative.as_posix()
        if includes and not any(
            fnmatch.fnmatchcase(relative_name, pattern) for pattern in includes
        ):
            continue
        if any(fnmatch.fnmatchcase(relative_name, pattern) for pattern in excludes):
            continue
        try:
            fingerprint, size = _fingerprint_with_size(
                path,
                full=full,
                sample_bytes=sample_bytes,
            )
        except OSError as error:
            handle_error(path, error)
            continue
        records.append(
            FileRecord(
                path=relative_name,
                size=size,
                fingerprint=fingerprint,
            )
        )

    return Snapshot(
        root=str(root_path),
        mode="full" if full else "sampled",
        records=tuple(sorted(records, key=lambda record: record.path)),
        issues=tuple(sorted(issues, key=lambda issue: issue.path)),
        sample_bytes=None if full else sample_bytes,
        include_patterns=includes,
        exclude_patterns=excludes,
    )


def save_snapshot(snapshot: Snapshot, path: str | Path) -> None:
    output = Path(path)
    body = json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n"
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as target:
            target.write(body)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, output)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def load_snapshot(path: str | Path) -> Snapshot:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("snapshot must be a JSON object")
    return Snapshot.from_dict(value)
