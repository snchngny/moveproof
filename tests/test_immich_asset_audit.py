import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from examples.immich_asset_audit import create_asset_audit, fetch_asset_paths, main


class ImmichAssetAuditTests(unittest.TestCase):
    def test_fetches_all_pages_using_search_only(self):
        requests = []
        pages = [
            {"assets": {"items": [{"id": "one"}], "nextPage": "2", "nextCursor": None}},
            {"assets": {"items": [{"id": "two"}], "nextPage": None, "nextCursor": None}},
        ]

        def open_request(request):
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(request.full_url, "https://example.test/api/search/metadata")
            self.assertEqual(request.get_header("X-api-key"), "secret")
            requests.append(json.loads(request.data))
            return io.BytesIO(json.dumps(pages[len(requests) - 1]).encode())

        with patch("examples.immich_asset_audit._open_request", side_effect=open_request):
            assets = fetch_asset_paths("https://example.test/api", "secret", "library")
        self.assertEqual([asset["id"] for asset in assets], ["one", "two"])
        self.assertEqual([request["page"] for request in requests], [1, 2])
        self.assertTrue(all(request["libraryId"] == "library" for request in requests))

    def test_refuses_cursor_pagination_instead_of_reporting_partial_results(self):
        response = {"assets": {"items": [], "nextPage": None, "nextCursor": "more"}}
        with patch(
            "examples.immich_asset_audit._open_request",
            return_value=io.BytesIO(json.dumps(response).encode()),
        ):
            with self.assertRaisesRegex(ValueError, "cursor pagination"):
                fetch_asset_paths("https://example.test/api", "secret", "library")

    def test_rejects_nonlocal_http_before_sending_api_key(self):
        with patch("examples.immich_asset_audit._open_request") as opener:
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                fetch_asset_paths("http://example.test/api", "secret", "library")
        opener.assert_not_called()

    def test_only_matches_unique_assets_in_the_selected_library_and_root(self):
        plan = {
            "safe_to_apply": False,
            "moves": [
                {"old_path": "old/a.jpg", "new_path": "new/a.jpg"},
                {"old_path": "old/b.jpg", "new_path": "new/b.jpg"},
                {"old_path": "old/c.jpg", "new_path": "new/c.jpg"},
            ],
        }
        assets = [
            {"id": "a", "originalPath": "/mnt/photos/old/a.jpg", "libraryId": "one"},
            {"id": "b1", "originalPath": "/mnt/photos/old/b.jpg", "libraryId": "one"},
            {"id": "b2", "originalPath": "/mnt/photos/old/b.jpg", "libraryId": "one"},
            {"id": "wrong", "originalPath": "/mnt/photos/old/c.jpg", "libraryId": "two"},
            {"id": "outside", "originalPath": "/mnt/photos2/old/c.jpg", "libraryId": "one"},
        ]
        audit = create_asset_audit(plan, assets, library_id="one", immich_root="/mnt/photos")
        self.assertFalse(audit["plan_safe_to_apply"])
        self.assertEqual(
            [move["status"] for move in audit["moves"]],
            ["matched", "ambiguous", "missing"],
        )
        self.assertEqual(audit["moves"][1]["asset_ids"], ["b1", "b2"])

    def test_cli_writes_local_audit_without_overwriting_existing_result(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.json"
            output_path = Path(directory) / "audit.json"
            plan = {"safe_to_apply": True, "moves": [{"old_path": "a.jpg", "new_path": "b.jpg"}]}
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            argv = [
                "immich_asset_audit.py", "--api-url", "https://example.test/api",
                "--library-id", "one", "--immich-root", "/mnt/photos",
                "--plan", str(plan_path), "--output", str(output_path),
            ]
            asset = {
                "id": "asset-1",
                "originalPath": "/mnt/photos/a.jpg",
                "libraryId": "one",
            }
            with (
                patch("sys.argv", argv),
                patch.dict("os.environ", {"IMMICH_API_KEY": "secret"}),
                patch("examples.immich_asset_audit.fetch_asset_paths", return_value=[asset]) as fetch,
            ):
                self.assertEqual(main(), 0)
                result = json.loads(output_path.read_text(encoding="utf-8"))
                self.assertEqual(result["moves"][0]["asset_ids"], ["asset-1"])
                with self.assertRaises(FileExistsError):
                    main()
            fetch.assert_called_with("https://example.test/api", "secret", "one")


if __name__ == "__main__":
    unittest.main()
