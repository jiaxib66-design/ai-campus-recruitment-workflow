from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_sensitive", ROOT / "scripts" / "check_sensitive.py")
check_sensitive = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_sensitive)


class SensitiveScanTests(unittest.TestCase):
    def test_repository_passes(self):
        self.assertEqual(check_sensitive.scan(ROOT), [])

    def test_detects_secret_and_phone(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            secret_line = "password=" + "definitely-" + "real-secret"
            phone_line = "phone=" + "138" + "1234" + "5678"
            (path / "bad.txt").write_text(secret_line + "\n" + phone_line + "\n", encoding="utf-8")
            findings = check_sensitive.scan(path)
            self.assertEqual(len(findings), 2)

    def test_rejects_runtime_data_inside_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills" / "demo-skill"
            (skill / "private").mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo-skill\n---\n", encoding="utf-8")
            (skill / "private" / "profile.json").write_text("{}\n", encoding="utf-8")
            (skill / "resume.md").write_text("test runtime resume\n", encoding="utf-8")
            (skill / "assets").mkdir()
            (skill / "assets" / "user-profile.example.json").write_text("{}\n", encoding="utf-8")

            findings = check_sensitive.scan(root)

            self.assertEqual(len(findings), 2)
            self.assertTrue(all("inside Skill" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
