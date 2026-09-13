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
