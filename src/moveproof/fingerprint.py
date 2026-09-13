from __future__ import annotations

import hashlib
import os
import stat
import struct
from pathlib import Path


DEFAULT_SAMPLE_BYTES = 64 * 1024
SAMPLED_SCHEME = "moveproof-sampled-v1"
FULL_SCHEME = "moveproof-full-v1"


class FileChangedError(OSError):
    """Raised when a file changes while its fingerprint is being computed."""


def _stat_signature(value: os.stat_result) -> tuple[int, int, int]:
    return (
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _file_identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def fingerprint_file(
    path: str | Path,
    *,
    full: bool = False,
    sample_bytes: int = DEFAULT_SAMPLE_BYTES,
) -> str:
    """Return a versioned content fingerprint for one regular file."""
    value, _ = _fingerprint_with_size(path, full=full, sample_bytes=sample_bytes)
    return value


def _fingerprint_with_size(
    path: str | Path,
    *,
    full: bool = False,
    sample_bytes: int = DEFAULT_SAMPLE_BYTES,
) -> tuple[str, int]:
    if sample_bytes < 1:
        raise ValueError("sample_bytes must be positive")

    file_path = Path(path)
    path_before = file_path.lstat()
    if not stat.S_ISREG(path_before.st_mode):
        raise OSError(f"not a regular file: {file_path}")

    digest = hashlib.blake2b(digest_size=32)
    scheme = FULL_SCHEME if full else f"{SAMPLED_SCHEME}-{sample_bytes}"
    digest.update(scheme.encode("ascii"))

    with file_path.open("rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise OSError(f"not a regular file: {file_path}")
        size = before.st_size
        digest.update(struct.pack(">Q", size))

        if full or size <= sample_bytes:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        else:
            offsets = (0, max(0, (size - sample_bytes) // 2), size - sample_bytes)
            for offset in offsets:
                source.seek(offset)
                digest.update(struct.pack(">Q", offset))
                digest.update(source.read(sample_bytes))

        after = os.fstat(source.fileno())

    path_after = file_path.lstat()
    if (
        _stat_signature(path_before) != _stat_signature(path_after)
        or _stat_signature(before) != _stat_signature(after)
        or _file_identity(path_before) != _file_identity(before)
        or _file_identity(after) != _file_identity(path_after)
    ):
        raise FileChangedError(f"file changed while fingerprinting: {file_path}")

    return f"{scheme}:{digest.hexdigest()}", size
