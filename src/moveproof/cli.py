from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from .compare import compare_snapshots
from .guard import check_library_guard
from .immich import create_immich_asset_audit, fetch_immich_asset_paths
from .inventory import create_inventory
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

    inventory = commands.add_parser(
        "inventory",
        help="count file extensions and broad sample-library categories without reading contents",
    )
    inventory.add_argument("root", type=Path)
    inventory.add_argument("--output", "-o", type=Path)
    inventory.add_argument("--include-hidden", action="store_true")
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
    reconcile.add_argument(
        "--allow-sampled",
        action="store_true",
        help="emit an advisory plan that cannot be applied automatically",
    )

    guard = commands.add_parser(
        "guard",
        help="block automation when a library scan looks unsafe",
    )
    guard.add_argument("baseline", type=Path)
    guard.add_argument("root", type=Path)
    guard.add_argument("--output", "-o", type=Path)
    guard.add_argument(
        "--max-missing-ratio",
        type=float,
        default=0.1,
        help="block when the removed-file ratio exceeds this value (default: 0.1)",
    )

    immich_audit = commands.add_parser(
        "immich-audit",
        help="join a reconciliation plan to Immich asset IDs without changing Immich",
    )
    immich_audit.add_argument("--api-url", required=True, help="Immich API root")
    immich_audit.add_argument("--library-id", required=True)
    immich_audit.add_argument("--immich-root", required=True, help="container path to the library")
    immich_audit.add_argument("--plan", required=True, type=Path)
    immich_audit.add_argument("--output", "-o", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "inventory":
        report = create_inventory(args.root, include_hidden=args.include_hidden)
        body = json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(body, encoding="utf-8")
        else:
            print(body, end="")
        return 1 if report.issues else 0

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

    if args.command == "reconcile":
        plan = create_reconciliation_plan(
            load_snapshot(args.before),
            load_snapshot(args.after),
            allow_incomplete=args.allow_incomplete,
            allow_sampled=args.allow_sampled,
        )
        body = json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(body, encoding="utf-8")
        else:
            print(body, end="")
        return 0 if plan.safe_to_apply else 1

    if args.command == "guard":
        baseline = load_snapshot(args.baseline)
        current = create_snapshot(
            args.root,
            full=baseline.mode == "full",
            include_hidden=baseline.include_hidden,
            sample_bytes=baseline.sample_bytes or 64 * 1024,
            on_error="record",
            include_patterns=baseline.include_patterns,
            exclude_patterns=baseline.exclude_patterns,
        )
        report = check_library_guard(
            baseline,
            current,
            max_missing_ratio=args.max_missing_ratio,
        )
        body = json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(body, encoding="utf-8")
        else:
            print(body, end="")
        return 0 if report.safe_to_continue else 1

    if args.command == "immich-audit":
        api_key = os.environ.get("IMMICH_API_KEY")
        if not api_key:
            parser.error("set IMMICH_API_KEY in the environment (never pass it on the command line)")
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        assets = fetch_immich_asset_paths(args.api_url, api_key, args.library_id)
        audit = create_immich_asset_audit(
            plan,
            assets,
            library_id=args.library_id,
            immich_root=args.immich_root,
        )
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(audit, output, ensure_ascii=False, indent=2)
            output.write("\n")
        return 0

    result = compare_snapshots(
        load_snapshot(args.before),
        load_snapshot(args.after),
        allow_incomplete=args.allow_incomplete,
    )

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
