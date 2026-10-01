from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


_CATEGORIES = {
    "audio": {
        ".aif", ".aiff", ".caf", ".flac", ".m4a", ".mp3", ".ogg", ".opus",
        ".rx2", ".wav",
    },
    "instrument_preset": {
        ".adg", ".als", ".b3xp", ".ens", ".exs", ".fxp", ".nfm8", ".nka",
        ".nki", ".nkm", ".nksf", ".nksn", ".nksr", ".nmsv", ".nrkt", ".pst",
        ".sfz", ".spf", ".sxt", ".tr5m", ".tr5p", ".zpreset",
    },
    "sample_container": {".aaz", ".ncw", ".nkr", ".nkx", ".sdir"},
    "support": {
        ".cfg", ".db", ".json", ".jpg", ".jpeg", ".meta", ".mid", ".midi",
        ".pdf", ".plist", ".png", ".rtf", ".txt", ".url", ".webp", ".xml",
    },
}


@dataclass(frozen=True, slots=True)
class InventoryIssue:
    path: str
    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class ExtensionSummary:
    extension: str
    category: str
    files: int
    bytes: int


@dataclass(frozen=True, slots=True)
class InventoryReport:
    root: str
    total_files: int
    total_bytes: int
    extensions: tuple[ExtensionSummary, ...]
    categories: dict[str, dict[str, int]]
    issues: tuple[InventoryIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "extensions": [asdict(item) for item in self.extensions],
            "categories": self.categories,
            "issues": [asdict(issue) for issue in self.issues],
        }


def classify_extension(extension: str) -> str:
    normalized = extension.lower()
    for category, extensions in _CATEGORIES.items():
        if normalized in extensions:
            return category
    return "other"


def create_inventory(root: Path, *, include_hidden: bool = False) -> InventoryReport:
    resolved_root = root.resolve()
    if not resolved_root.is_dir():
        raise NotADirectoryError(str(root))

    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    issues: list[InventoryIssue] = []

    def record_walk_error(error: OSError) -> None:
        issues.append(
            InventoryIssue(
                path=str(getattr(error, "filename", "") or ""),
                error_type=type(error).__name__,
                message=str(error),
            )
        )

    for directory, names, filenames in os.walk(resolved_root, onerror=record_walk_error):
        if not include_hidden:
            names[:] = [name for name in names if not name.startswith(".")]
            filenames = [name for name in filenames if not name.startswith(".")]
        for filename in filenames:
            path = Path(directory, filename)
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                size = path.stat().st_size
            except OSError as error:
                issues.append(
                    InventoryIssue(
                        path=path.relative_to(resolved_root).as_posix(),
                        error_type=type(error).__name__,
                        message=str(error),
                    )
                )
                continue
            extension = path.suffix.lower() or "[no extension]"
            totals[extension][0] += 1
            totals[extension][1] += size

    extensions = tuple(
        ExtensionSummary(
            extension=extension,
            category=classify_extension(extension),
            files=values[0],
            bytes=values[1],
        )
        for extension, values in sorted(
            totals.items(), key=lambda item: (-item[1][0], item[0])
        )
    )
    categories: dict[str, dict[str, int]] = {}
    for item in extensions:
        category = categories.setdefault(item.category, {"files": 0, "bytes": 0})
        category["files"] += item.files
        category["bytes"] += item.bytes

    return InventoryReport(
        root=str(resolved_root),
        total_files=sum(item.files for item in extensions),
        total_bytes=sum(item.bytes for item in extensions),
        extensions=extensions,
        categories=dict(sorted(categories.items())),
        issues=tuple(issues),
    )
