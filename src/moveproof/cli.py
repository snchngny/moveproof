from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .compare import compare_snapshots
from .reconcile import create_reconciliation_plan
from .snapshot import create_snapshot, load_snapshot, save_snapshot


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="moveproof")
    commands = parser.add_subparsers(dest="command", required=True)

    snapshot = commands.add_parser("snapshot", help="create a directory snapshot")
    snapshot.add_argument("root", type=Path)
    snapshot.add_argument("--output", "-o", type=Path, required=True)
    snapshot.add_argument("--full", action="store_true", help="hash every byte")
    snapshot.add_argument("--include-hidden", action="store_true")
    snapshot.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="GLOB",
        help="include matching relative paths; repeat for multiple patterns",
    )
    snapshot.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="exclude matching relative paths; repeat for multiple patterns",
    )
    snapshot.add_argument(
        "--record-errors",
        action="store_true",
        help="write an incomplete snapshot with per-path issues instead of stopping",
    )

    compare = commands.add_parser("compare", help="compare two snapshots")
    compare.add_argument("before", type=Path)
    compare.add_argument("after", type=Path)
    compare.add_argument("--output", "-o", type=Path)
    compare.add_argument("--include-unchanged", action="store_true")
    compare.add_argument("--allow-incomplete", action="store_true")

    reconcile = commands.add_parser(
        "reconcile",
        help="create a dry-run path reconciliation plan",
    )
    reconcile.add_argument("before", type=Path)
    reconcile.add_argument("after", type=Path)
    reconcile.add_argument("--output", "-o", type=Path)
    reconcile.add_argument("--allow-incomplete", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "snapshot":
        result = create_snapshot(
            args.root,
            full=args.full,
            include_hidden=args.include_hidden,
            on_error="record" if args.record_errors else "raise",
            include_patterns=args.include,
            exclude_patterns=args.exclude,
        )
        save_snapshot(result, args.output)
        return 1 if result.issues else 0

    result = compare_snapshots(
        load_snapshot(args.before),
        load_snapshot(args.after),
        allow_incomplete=args.allow_incomplete,
    )
    if args.command == "reconcile":
        plan = create_reconciliation_plan(result)
        body = json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(body, encoding="utf-8")
        else:
            print(body, end="")
        return 0 if plan.safe else 1

    changes = result.changes
    if not args.include_unchanged:
        changes = tuple(change for change in changes if change.kind != "unchanged")
    body = json.dumps(
        {"changes": [change.to_dict() for change in changes]},
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    if args.output:
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
