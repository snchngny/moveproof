from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path

from moveproof import fingerprint_file


def _measure(path: Path, *, full: bool, repeats: int) -> float:
    started = time.perf_counter()
    for _ in range(repeats):
        fingerprint_file(path, full=full)
    return (time.perf_counter() - started) / repeats


def _write_benchmark_file(path: Path, *, size_mib: int) -> None:
    with path.open("wb") as output:
        for _ in range(size_mib):
            output.write(os.urandom(1024 * 1024))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size-mib", type=int, default=256)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.size_mib < 1 or args.repeats < 1:
        parser.error("size-mib and repeats must be positive")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "benchmark.bin"
        _write_benchmark_file(path, size_mib=args.size_mib)

        sampled_seconds = _measure(path, full=False, repeats=args.repeats)
        full_seconds = _measure(path, full=True, repeats=args.repeats)

    print(
        json.dumps(
            {
                "size_mib": args.size_mib,
                "repeats": args.repeats,
                "data": "random bytes, written before timing",
                "platform": platform.system(),
                "python": f"{sys.version_info.major}.{sys.version_info.minor}",
                "sampled_seconds": round(sampled_seconds, 6),
                "full_seconds": round(full_seconds, 6),
                "speedup": round(full_seconds / sampled_seconds, 2),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
