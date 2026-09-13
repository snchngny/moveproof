from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


FingerprintMode = Literal["sampled", "full"]
ChangeKind = Literal["unchanged", "moved", "copied", "added", "removed", "ambiguous"]


@dataclass(frozen=True, slots=True)
class FileRecord:
    path: str
    size: int
    fingerprint: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> FileRecord:
        return cls(
            path=str(value["path"]),
            size=int(value["size"]),
            fingerprint=str(value["fingerprint"]),
        )


@dataclass(frozen=True, slots=True)
class Snapshot:
    root: str
    mode: FingerprintMode
    records: tuple[FileRecord, ...]
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "root": self.root,
            "mode": self.mode,
            "records": [asdict(record) for record in self.records],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Snapshot:
        schema_version = int(value.get("schema_version", 0))
        if schema_version != 1:
            raise ValueError(f"unsupported snapshot schema: {schema_version}")
        mode = str(value["mode"])
        if mode not in {"sampled", "full"}:
            raise ValueError(f"unsupported fingerprint mode: {mode}")
        return cls(
            root=str(value["root"]),
            mode=mode,  # type: ignore[arg-type]
            records=tuple(FileRecord.from_dict(item) for item in value["records"]),
        )


@dataclass(frozen=True, slots=True)
class Change:
    kind: ChangeKind
    fingerprint: str
    old_path: str | None = None
    new_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ChangeSet:
    changes: tuple[Change, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"changes": [change.to_dict() for change in self.changes]}

