"""Join a Moveproof plan to Immich asset IDs without changing either system."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from moveproof.immich import create_immich_asset_audit, fetch_immich_asset_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", required=True, help="Immich API root, e.g. https://host/api")
    parser.add_argument("--library-id", required=True)
    parser.add_argument("--immich-root", required=True, help="container path to the scanned library")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    api_key = os.environ.get("IMMICH_API_KEY")
    if not api_key:
        parser.error("set IMMICH_API_KEY in the environment (never pass it on the command line)")
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    assets = fetch_immich_asset_paths(args.api_url, api_key, args.library_id)
    audit = create_immich_asset_audit(
        plan, assets, library_id=args.library_id, immich_root=args.immich_root
    )
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(audit, output, ensure_ascii=False, indent=2)
        output.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
