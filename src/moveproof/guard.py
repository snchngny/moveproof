from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .compare import compare_snapshots
from .model import Snapshot


@dataclass(frozen=True, slots=True)
class LibraryGuardReport:
    baseline_root: str
    current_root: str
    baseline_files: int
    current_files: int
    missing_files: int
    missing_ratio: float
    max_missing_ratio: float
    change_counts: dict[str, int]
    reasons: tuple[str, ...]
    schema_version: int = 1

    @property
    def safe_to_continue(self) -> bool:
        return not self.reasons

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "safe_to_continue": self.safe_to_continue,
            "baseline_root": self.baseline_root,
            "current_root": self.current_root,
            "baseline_files": self.baseline_files,
            "current_files": self.current_files,
            "missing_files": self.missing_files,
            "missing_ratio": self.missing_ratio,
            "max_missing_ratio": self.max_missing_ratio,
            "change_counts": self.change_counts,
            "reasons": list(self.reasons),
        }


def check_library_guard(
    baseline: Snapshot,
    current: Snapshot,
    *,
    max_missing_ratio: float = 0.1,
) -> LibraryGuardReport:
    if not 0 <= max_missing_ratio <= 1:
        raise ValueError("max_missing_ratio must be between 0 and 1")
    if not baseline.records:
        raise ValueError("library guard requires a non-empty baseline snapshot")

    changes = compare_snapshots(baseline, current, allow_incomplete=True)
    change_counts: dict[str, int] = {}
    for change in changes.changes:
        change_counts[change.kind] = change_counts.get(change.kind, 0) + 1

    missing_files = change_counts.get("removed", 0)
    missing_ratio = missing_files / len(baseline.records)
    reasons: list[str] = []
    if current.issues:
        reasons.append("scan_incomplete")
    if not current.records:
        reasons.append("library_empty")
    if change_counts.get("ambiguous", 0):
        reasons.append("ambiguous_changes")
    if missing_ratio > max_missing_ratio:
        reasons.append("missing_ratio_exceeded")

    return LibraryGuardReport(
        baseline_root=baseline.root,
        current_root=current.root,
        baseline_files=len(baseline.records),
        current_files=len(current.records),
        missing_files=missing_files,
        missing_ratio=missing_ratio,
        max_missing_ratio=max_missing_ratio,
        change_counts=dict(sorted(change_counts.items())),
        reasons=tuple(reasons),
    )
