from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from .model import ChangeSet


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
class ReconciliationPlan:
    moves: tuple[ReconciliationMove, ...]
    conflicts: tuple[ReconciliationConflict, ...]
    schema_version: int = 1

    @property
    def safe(self) -> bool:
        return not self.conflicts

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "safe": self.safe,
            "moves": [asdict(move) for move in self.moves],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
        }


def create_reconciliation_plan(changes: ChangeSet) -> ReconciliationPlan:
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
    return ReconciliationPlan(moves=moves, conflicts=conflicts)
