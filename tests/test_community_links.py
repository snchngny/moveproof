"""公開問い合わせのリンクが正本ownerから逸れないことを確認する。"""

from pathlib import Path
import unittest


class CommunityLinksTest(unittest.TestCase):
    def test_use_case_form_collects_feedback_without_private_files(self):
        root = Path(__file__).resolve().parents[1]
        form = (root / ".github/ISSUE_TEMPLATE/feature.yml").read_text(encoding="utf-8")
        for text in ("この報告は公開されます", "秘密値は添付しない", "移行先", "期待する結果", "id: trial_result"):
            self.assertIn(text, form)
        self.assertEqual(form.count("required: true"), 1)

    def test_security_report_uses_canonical_owner(self):
        root = Path(__file__).resolve().parents[1]
        config = (root / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8")
        self.assertIn("https://github.com/snchngny/moveproof/security/advisories/new", config)
        self.assertNotIn("senooy-dot", config)


if __name__ == "__main__":
    unittest.main()
