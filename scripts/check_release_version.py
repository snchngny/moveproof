from __future__ import annotations

import argparse
import re
from pathlib import Path


def project_version(pyproject_path: Path) -> str:
    in_project = False
    for line in pyproject_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if in_project and stripped.startswith("["):
            break
        if in_project and (match := re.fullmatch(r'version\s*=\s*"([^"]+)"', stripped)):
            return match.group(1)
    raise ValueError(f"project.version not found in {pyproject_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    args = parser.parse_args()

    tag_version = args.tag.removeprefix("v")
    package_version = project_version(args.pyproject)
    if tag_version != package_version:
        parser.error(
            f"release tag {args.tag!r} does not match package version {package_version!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
