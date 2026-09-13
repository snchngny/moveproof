from __future__ import annotations

from collections import defaultdict

from .model import Change, ChangeSet, FileRecord, Snapshot


def _by_fingerprint(records: tuple[FileRecord, ...]) -> dict[str, list[FileRecord]]:
    grouped: dict[str, list[FileRecord]] = defaultdict(list)
    for record in records:
        grouped[record.fingerprint].append(record)
    return grouped


def compare_snapshots(before: Snapshot, after: Snapshot) -> ChangeSet:
    if before.mode != after.mode:
        raise ValueError("snapshots use different fingerprint modes")

    old_groups = _by_fingerprint(before.records)
    new_groups = _by_fingerprint(after.records)
    changes: list[Change] = []

    for fingerprint in sorted(old_groups.keys() | new_groups.keys()):
        old_records = old_groups.get(fingerprint, [])
        new_records = new_groups.get(fingerprint, [])
        old_by_path = {record.path: record for record in old_records}
        new_by_path = {record.path: record for record in new_records}

        common_paths = sorted(old_by_path.keys() & new_by_path.keys())
        for path in common_paths:
            changes.append(Change("unchanged", fingerprint, path, path))

        unmatched_old = sorted(old_by_path.keys() - new_by_path.keys())
        unmatched_new = sorted(new_by_path.keys() - old_by_path.keys())

        if len(unmatched_old) == 1 and len(unmatched_new) == 1:
            changes.append(Change("moved", fingerprint, unmatched_old[0], unmatched_new[0]))
        elif not unmatched_old:
            for path in unmatched_new:
                kind = "copied" if old_records else "added"
                source = old_records[0].path if old_records else None
                changes.append(Change(kind, fingerprint, source, path))
        elif not unmatched_new:
            for path in unmatched_old:
                changes.append(Change("removed", fingerprint, path, None))
        else:
            for path in unmatched_old:
                changes.append(Change("ambiguous", fingerprint, path, None))
            for path in unmatched_new:
                changes.append(Change("ambiguous", fingerprint, None, path))

    return ChangeSet(tuple(changes))

