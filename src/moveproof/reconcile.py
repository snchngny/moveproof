from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from .compare import compare_snapshots
from .model import ChangeSet, FingerprintMode, Snapshot


@dataclass(frozen=True, slots=True)
class ReconciliationMove:
    old_path: str
    new_path: str
    fingerprint: str
    size: int


@dataclass(frozen=True, slots=True)
class ReconciliationConflict:
    fingerprint: str
    old_paths: tuple[str, ...]
    new_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "old_paths": list(self.old_paths),
            "new_paths": list(self.new_paths),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationRootMove:
    old_root: str
    new_root: str
    file_count: int


@dataclass(frozen=True, slots=True)
class ReconciliationPlan:
    moves: tuple[ReconciliationMove, ...]
    conflicts: tuple[ReconciliationConflict, ...]
    fingerprint_mode: FingerprintMode
    complete: bool
    root_move: ReconciliationRootMove | None = None
    schema_version: int = 1

    @property
    def safe_to_apply(self) -> bool:
        return self.fingerprint_mode == "full" and self.complete and not self.conflicts

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "fingerprint_mode": self.fingerprint_mode,
            "complete": self.complete,
            "safe_to_apply": self.safe_to_apply,
            "root_move": asdict(self.root_move) if self.root_move else None,
            "moves": [asdict(move) for move in self.moves],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
        }


def _plan_from_changes(
    changes: ChangeSet,
    *,
    fingerprint_mode: FingerprintMode,
    complete: bool,
    root_move: ReconciliationRootMove | None = None,
) -> ReconciliationPlan:
    moves = tuple(
        ReconciliationMove(
            old_path=change.old.path,
            new_path=change.new.path,
            fingerprint=change.old.fingerprint,
            size=change.old.size,
        )
        for change in changes.changes
        if change.kind == "moved" and change.old is not None and change.new is not None
    )

    ambiguous: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"old": [], "new": []}
    )
    for change in changes.changes:
        if change.kind != "ambiguous":
            continue
        if change.old is not None:
            ambiguous[change.old.fingerprint]["old"].append(change.old.path)
        if change.new is not None:
            ambiguous[change.new.fingerprint]["new"].append(change.new.path)

    conflicts = tuple(
        ReconciliationConflict(
            fingerprint=fingerprint,
            old_paths=tuple(sorted(paths["old"])),
            new_paths=tuple(sorted(paths["new"])),
        )
        for fingerprint, paths in sorted(ambiguous.items())
    )
    return ReconciliationPlan(
        moves=moves,
        conflicts=conflicts,
        fingerprint_mode=fingerprint_mode,
        complete=complete,
        root_move=root_move,
    )


def _detect_root_move(
    before: Snapshot,
    after: Snapshot,
) -> ReconciliationRootMove | None:
    if before.root == after.root or not before.records or before.issues or after.issues:
        return None
    before_records = {
        record.path: (record.size, record.fingerprint) for record in before.records
    }
    after_records = {
        record.path: (record.size, record.fingerprint) for record in after.records
    }
    if before_records != after_records:
        return None
    return ReconciliationRootMove(
        old_root=before.root,
        new_root=after.root,
        file_count=len(before.records),
    )


def create_reconciliation_plan(
    before: Snapshot,
    after: Snapshot,
    *,
    allow_incomplete: bool = False,
    allow_sampled: bool = False,
) -> ReconciliationPlan:
    if before.mode != "full" and not allow_sampled:
        raise ValueError(
            "reconciliation plans require full fingerprints; pass allow_sampled=True "
            "for an advisory plan that is not safe to apply automatically"
        )
    changes = compare_snapshots(
        before,
        after,
        allow_incomplete=allow_incomplete,
    )
    return _plan_from_changes(
        changes,
        fingerprint_mode=before.mode,
        complete=not before.issues and not after.issues,
        root_move=_detect_root_move(before, after),
    )
