from __future__ import annotations

from collections import defaultdict

from .model import Change, ChangeSet, FileRecord, Snapshot


def _by_fingerprint(records: tuple[FileRecord, ...]) -> dict[str, list[FileRecord]]:
    grouped: dict[str, list[FileRecord]] = defaultdict(list)
    for record in records:
        grouped[record.fingerprint].append(record)
    return grouped


def compare_snapshots(
    before: Snapshot,
    after: Snapshot,
    *,
    allow_incomplete: bool = False,
) -> ChangeSet:
    if before.mode != after.mode:
        raise ValueError("snapshots use different fingerprint modes")
    if before.sample_bytes != after.sample_bytes:
        raise ValueError("snapshots use different sample sizes")
    if not allow_incomplete and (before.issues or after.issues):
        raise ValueError("cannot compare incomplete snapshots without allow_incomplete=True")

    changes: list[Change] = []
    old_by_path = {record.path: record for record in before.records}
    new_by_path = {record.path: record for record in after.records}
    common_paths = old_by_path.keys() & new_by_path.keys()

    for path in sorted(common_paths):
        old_record = old_by_path[path]
        new_record = new_by_path[path]
        kind = "unchanged" if old_record.fingerprint == new_record.fingerprint else "modified"
        changes.append(Change(kind, old_record, new_record))

    unmatched_old_records = tuple(
        record for record in before.records if record.path not in common_paths
    )
    unmatched_new_records = tuple(
        record for record in after.records if record.path not in common_paths
    )
    old_groups = _by_fingerprint(unmatched_old_records)
    new_groups = _by_fingerprint(unmatched_new_records)
    all_old_groups = _by_fingerprint(before.records)

    for fingerprint in sorted(old_groups.keys() | new_groups.keys()):
        old_records = old_groups.get(fingerprint, [])
        new_records = new_groups.get(fingerprint, [])

        if len(old_records) == 1 and len(new_records) == 1:
            changes.append(Change("moved", old_records[0], new_records[0]))
        elif not old_records:
            existing_sources = all_old_groups.get(fingerprint, [])
            for new_record in new_records:
                if existing_sources:
                    changes.append(Change("copied", existing_sources[0], new_record))
                else:
                    changes.append(Change("added", None, new_record))
        elif not new_records:
            for old_record in old_records:
                changes.append(Change("removed", old_record, None))
        else:
            for old_record in old_records:
                changes.append(Change("ambiguous", old_record, None))
            for new_record in new_records:
                changes.append(Change("ambiguous", None, new_record))

    return ChangeSet(tuple(changes))
