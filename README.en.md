# Moveproof

Moveproof is a zero-dependency Python library for identifying large local files without reading them in full on every scan. It compares snapshots and reports modifications, renames, moves, copies, additions, and removals.

## Install

```bash
pip install moveproof
```

## Python API

```python
from pathlib import Path
from moveproof import compare_snapshots, create_snapshot

before = create_snapshot(Path("media"))
# Move or add files.
after = create_snapshot(Path("media"))

for change in compare_snapshots(before, after).changes:
    print(change.kind, change.old_path, change.new_path)
```

## CLI

```bash
moveproof snapshot media --output before.json
moveproof snapshot media --output after.json
moveproof compare before.json after.json
```

Limit a scan with relative-path globs. Excludes take precedence over includes, and the filter profile is stored in the snapshot. Snapshots with different filters cannot be compared accidentally.

```bash
moveproof snapshot media --include "*.wav" --include "*.aiff" --exclude "archive/*" -o audio.json
```

By default, one unreadable file stops snapshot creation. Use `--record-errors` to preserve diagnostics from a long scan: the CLI writes an incomplete snapshot with per-path issues and exits with code 1. Comparing incomplete snapshots is rejected by default to avoid false removal reports; use `--allow-incomplete` only when you understand the missing coverage.

Snapshot JSON is written to a temporary file in the same directory and then replaced, so a failed write does not leave an existing snapshot half-written.

By default, files up to 64 KiB are read in full. Larger files are sampled at the beginning, middle, and end, with the file size included in the digest. A file that changes while being read is rejected.

The snapshot records its sampling width. Comparing snapshots created with different modes or widths fails explicitly instead of producing misleading changes.

A sampled fingerprint is not proof of complete byte identity. Use `--full` when adversarial collisions or exact content identity matter.

## Benchmark

```bash
python benchmarks/benchmark_fingerprint.py --size-mib 256
```

The benchmark repeatedly reads the same file and is affected by the OS cache, storage, and sparse-file support. Include the environment and run parameters when publishing results.

See the [contribution guide](CONTRIBUTING.md) before proposing changes and the [security policy](SECURITY.md) before reporting a vulnerability.

## License

MIT
