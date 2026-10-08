"""公開問い合わせのリンクが正本ownerから逸れないことを確認する。"""

from pathlib import Path
import unittest


class CommunityLinksTest(unittest.TestCase):
    def test_security_report_uses_canonical_owner(self):
        root = Path(__file__).resolve().parents[1]
        config = (root / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8")
        self.assertIn("https://github.com/snchngny/moveproof/security/advisories/new", config)
        self.assertNotIn("senooy-dot", config)


if __name__ == "__main__":
    unittest.main()
