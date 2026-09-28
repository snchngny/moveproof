"""Read-only helpers for joining Moveproof plans to Immich asset IDs."""

from __future__ import annotations

import json
from pathlib import PurePosixPath
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        raise ValueError("Immich redirected the request; refusing to forward the API key")


def _open_request(request: Request):
    return build_opener(_NoRedirect).open(request, timeout=30)


def fetch_immich_asset_paths(api_url: str, api_key: str, library_id: str) -> list[dict]:
    parsed_url = urlsplit(api_url)
    is_secure = parsed_url.scheme == "https" or (
        parsed_url.scheme == "http"
        and parsed_url.hostname in {"localhost", "127.0.0.1", "::1"}
    )
    if (
        not is_secure
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
        or not parsed_url.path.rstrip("/").endswith("/api")
    ):
        raise ValueError("api-url must be an HTTPS Immich /api URL (HTTP only for localhost)")

    assets: list[dict] = []
    page = 1
    seen_pages: set[int] = set()
    endpoint = api_url.rstrip("/") + "/search/metadata"
    while page not in seen_pages:
        seen_pages.add(page)
        request = Request(
            endpoint,
            data=json.dumps({"libraryId": library_id, "page": page, "size": 100}).encode(),
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            method="POST",
        )
        with _open_request(request) as response:
            result = json.load(response)["assets"]
        if result.get("nextCursor"):
            raise ValueError("unsupported Immich cursor pagination; no report was written")
        if not isinstance(result.get("items"), list):
            raise ValueError("Immich response has no assets.items list")
        assets.extend(result["items"])
        next_page = result.get("nextPage")
        if next_page is None:
            return assets
        if not str(next_page).isdigit() or int(next_page) <= page:
            raise ValueError("unexpected Immich nextPage; no report was written")
        page = int(next_page)
    raise ValueError("repeated Immich page; no report was written")


def create_immich_asset_audit(
    plan: dict,
    assets: list[dict],
    *,
    library_id: str,
    immich_root: str,
) -> dict:
    root = PurePosixPath(immich_root)
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("immich-root must be an absolute container path")
    asset_ids_by_path: dict[str, set[str]] = {}
    for asset in assets:
        if asset.get("libraryId") != library_id:
            continue
        path = PurePosixPath(asset["originalPath"])
        if ".." in path.parts:
            continue
        try:
            relative_path = path.relative_to(root).as_posix()
        except ValueError:
            continue
        asset_ids_by_path.setdefault(relative_path, set()).add(asset["id"])

    moves = []
    for move in plan["moves"]:
        asset_ids = sorted(asset_ids_by_path.get(move["old_path"], set()))
        status = "matched" if len(asset_ids) == 1 else "missing" if not asset_ids else "ambiguous"
        moves.append(
            {
                "old_path": move["old_path"],
                "new_path": move["new_path"],
                "asset_ids": asset_ids,
                "status": status,
            }
        )
    return {
        "schema_version": 1,
        "read_only": True,
        "plan_safe_to_apply": plan["safe_to_apply"],
        "moves": moves,
    }
