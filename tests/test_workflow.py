from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills" / "ai-campus-recruitment-workflow" / "scripts"
GUIDED_WORKFLOW = ROOT / "skills" / "ai-campus-recruitment-workflow" / "references" / "guided-workflow.md"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


score_roles = load_module("score_roles", SKILL_SCRIPTS / "score_roles.py")
email_imap = load_module("email_imap", SKILL_SCRIPTS / "email_imap.py")


class ScoringTests(unittest.TestCase):
    def test_example_ranking_and_shared_quota(self):
        profile = json.loads((ROOT / "config" / "user-profile.example.json").read_text(encoding="utf-8"))
        roles = json.loads((ROOT / "examples" / "roles.example.json").read_text(encoding="utf-8"))["roles"]
        result = score_roles.rank(profile, roles)
        indexed = {item["role"]: item for item in result["roles"]}

        self.assertEqual(indexed["数据产品培训生"]["category"], "努力争取")
        self.assertEqual(indexed["商业分析培训生"]["category"], "重点投递")
        self.assertTrue(indexed["数据产品培训生"]["quota_selected"])
        self.assertTrue(indexed["商业分析培训生"]["quota_selected"])
        self.assertFalse(indexed["嵌入式开发工程师"]["quota_selected"])
        self.assertEqual(indexed["嵌入式开发工程师"]["hard_gate"], "fail")
        self.assertIn("不承诺录用", result["disclaimer"])

    def test_unknown_verification_is_penalized(self):
        profile = json.loads((ROOT / "config" / "user-profile.example.json").read_text(encoding="utf-8"))
        role = json.loads((ROOT / "examples" / "roles.example.json").read_text(encoding="utf-8"))["roles"][0]
        role["verification_status"] = "unverified"
        item = score_roles.score_role(profile, role, score_roles.DEFAULT_WEIGHTS)
        self.assertEqual(item["hard_gate"], "unknown")
        self.assertEqual(item["uncertainty_penalty"], 3)


class EmailTests(unittest.TestCase):
    def test_mock_deadline_extraction_requires_confirmation(self):
        data = json.loads((ROOT / "examples" / "mock-emails.example.json").read_text(encoding="utf-8"))
        candidates = email_imap.extract_candidates(data["messages"])
        self.assertEqual(len(candidates), 2)
        self.assertTrue(all(item["requires_user_confirmation"] for item in candidates))
        self.assertTrue(all(item["timezone"] == "Asia/Shanghai" for item in candidates))


class CliTests(unittest.TestCase):
    def run_cli(self, script: str, *args: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(SKILL_SCRIPTS / script), *args],
            check=True, capture_output=True, text=True, encoding="utf-8", env=env
        )

    def test_init_clues_tracker_and_email_mock(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            profile = temp_path / "private" / "profile.json"
            self.run_cli("init_user_config.py", "--output", str(profile))
            self.assertTrue(profile.exists())

            clues = temp_path / "clues.json"
            self.run_cli(
                "import_clues.py", "--input", str(ROOT / "examples" / "clues.example.csv"),
                "--output", str(clues), "--observed-at", "2026-08-19T00:00:00+08:00"
            )
            self.assertEqual(len(json.loads(clues.read_text(encoding="utf-8"))["clues"]), 2)

            tracker = temp_path / "applications.csv"
            self.run_cli("tracker.py", "init", "--file", str(tracker))
            self.run_cli(
                "tracker.py", "add", "--file", str(tracker), "--company", "星河科技（虚构）",
                "--role", "数据产品培训生", "--deadline", "2026-09-01T12:00:00+00:00"
            )
            self.run_cli(
                "tracker.py", "update", "--file", str(tracker), "--id", "APP-0001",
                "--status", "已投递", "--next-action", "等待通知"
            )
            with tracker.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["status"], "已投递")

            todos = temp_path / "todos.json"
            result = self.run_cli(
                "email_imap.py", "mock", "--input", str(ROOT / "examples" / "mock-emails.example.json"),
                "--output", str(todos)
            )
            self.assertIn("no calendar write", result.stdout)
            self.assertFalse(json.loads(todos.read_text(encoding="utf-8"))["calendar_write_performed"])


class GuidedWorkflowContractTests(unittest.TestCase):
    def test_onboarding_and_target_discovery_routes_exist(self):
        guide = GUIDED_WORKFLOW.read_text(encoding="utf-8")
        required_contracts = (
            "First-time user",
            "Returning user",
            "Named companies",
            "Direction or region",
            "Unclear target",
            "Run mode",
            "Improvement mode",
            "voice input",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, guide)


if __name__ == "__main__":
    unittest.main()
