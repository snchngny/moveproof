from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


FingerprintMode = Literal["sampled", "full"]
ChangeKind = Literal[
    "unchanged",
    "modified",
    "moved",
    "copied",
    "added",
    "removed",
    "ambiguous",
]


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
    sample_bytes: int | None = None
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "root": self.root,
            "mode": self.mode,
            "sample_bytes": self.sample_bytes,
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
        raw_sample_bytes = value.get("sample_bytes")
        sample_bytes = None if raw_sample_bytes is None else int(raw_sample_bytes)
        if mode == "sampled" and (sample_bytes is None or sample_bytes < 1):
            raise ValueError("sampled snapshots require a positive sample_bytes value")
        return cls(
            root=str(value["root"]),
            mode=mode,  # type: ignore[arg-type]
            records=tuple(FileRecord.from_dict(item) for item in value["records"]),
            sample_bytes=sample_bytes,
        )


@dataclass(frozen=True, slots=True)
class Change:
    kind: ChangeKind
    old: FileRecord | None = None
    new: FileRecord | None = None

    @property
    def old_path(self) -> str | None:
        return self.old.path if self.old else None

    @property
    def new_path(self) -> str | None:
        return self.new.path if self.new else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "old": asdict(self.old) if self.old else None,
            "new": asdict(self.new) if self.new else None,
        }


@dataclass(frozen=True, slots=True)
class ChangeSet:
    changes: tuple[Change, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"changes": [change.to_dict() for change in self.changes]}
