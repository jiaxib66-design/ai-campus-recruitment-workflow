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
PRIVACY_GUIDE = ROOT / "skills" / "ai-campus-recruitment-workflow" / "references" / "privacy-and-safety.md"
APPLICATION_FORM_GUIDE = (
    ROOT / "skills" / "ai-campus-recruitment-workflow" / "references" / "application-form-filling.md"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


score_roles = load_module("score_roles", SKILL_SCRIPTS / "score_roles.py")
email_imap = load_module("email_imap", SKILL_SCRIPTS / "email_imap.py")
recruitment_monitor = load_module("recruitment_monitor", SKILL_SCRIPTS / "recruitment_monitor.py")


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
        self.assertEqual(len(candidates), 3)
        self.assertTrue(all(item["requires_user_confirmation"] for item in candidates))
        self.assertTrue(all(item["timezone"] == "Asia/Shanghai" for item in candidates[:2]))
        self.assertEqual(candidates[2]["event_type"], "offer")
        self.assertEqual(candidates[2]["deadline"], "")
        self.assertEqual(candidates[0]["sender"], "campus@example.org")


class MonitoringTests(unittest.TestCase):
    def test_match_status_candidate_and_keep_tracker_read_only(self):
        rows = [{
            "id": "APP-0001", "company": "星河科技（虚构）", "role": "数据产品培训生",
            "status": "已投递", "deadline": "", "next_action": "", "next_action_at": "",
        }]
        candidates = [{
            "message_id": "fictional-001", "event_type": "assessment", "deadline": "",
            "subject": "星河科技 数据产品培训生在线测评", "sender": "campus@example.org",
        }]
        state = {"processed_event_keys": [], "pending_status_changes": {}, "sent_reminder_keys": []}
        report = recruitment_monitor.build_report(
            rows, candidates, state, recruitment_monitor.parse_time("2026-08-23T10:00:00+08:00"), [3, 24, 72]
        )
        self.assertFalse(report["tracker_write_performed"])
        self.assertEqual(report["status_change_candidates"][0]["suggested_status"], "测评")
        self.assertTrue(report["status_change_candidates"][0]["requires_user_confirmation"])
        self.assertEqual(rows[0]["status"], "已投递")

        repeated = recruitment_monitor.build_report(
            rows, candidates, state, recruitment_monitor.parse_time("2026-08-23T10:05:00+08:00"), [3, 24, 72]
        )
        self.assertEqual(len(repeated["status_change_candidates"]), 1)

    def test_reminder_tiers_are_deduplicated(self):
        rows = [{
            "id": "APP-0002", "company": "远山智能（虚构）", "role": "产品培训生",
            "status": "测评", "deadline": "", "next_action": "完成在线测评",
            "next_action_at": "2026-08-26T10:00:00+08:00",
        }]
        state = {"processed_event_keys": [], "pending_status_changes": {}, "sent_reminder_keys": []}
        first = recruitment_monitor.build_report(
            rows, [], state, recruitment_monitor.parse_time("2026-08-23T11:00:00+08:00"), [3, 24, 72]
        )
        self.assertEqual(first["reminders"][0]["tier_hours"], 72)
        second = recruitment_monitor.build_report(
            rows, [], state, recruitment_monitor.parse_time("2026-08-23T12:00:00+08:00"), [3, 24, 72]
        )
        self.assertEqual(second["reminders"], [])
        third = recruitment_monitor.build_report(
            rows, [], state, recruitment_monitor.parse_time("2026-08-25T11:00:00+08:00"), [3, 24, 72]
        )
        self.assertEqual(third["reminders"][0]["tier_hours"], 24)


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
                "--role", "数据产品培训生", "--deadline", "2026-09-01T12:00:00+00:00",
                "--history-file", str(temp_path / "history.jsonl")
            )
            self.run_cli(
                "tracker.py", "update", "--file", str(tracker), "--id", "APP-0001",
                "--status", "已投递", "--next-action", "等待通知",
                "--history-file", str(temp_path / "history.jsonl"), "--source", "user_confirmed",
                "--source-id", "fictional-confirmation-001"
            )
            with tracker.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["status"], "已投递")
            history = [json.loads(line) for line in (temp_path / "history.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([item["event_type"] for item in history], ["application_created", "status_changed"])
            self.assertEqual(history[1]["source_id"], "fictional-confirmation-001")

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

    def test_shortlisted_official_pages_are_opened_before_final_ranking(self):
        guide = GUIDED_WORKFLOW.read_text(encoding="utf-8")
        verification_stage = guide.split("### 3. Verify official facts", 1)[1].split(
            "### 4. Check gates and prioritize", 1
        )[0]
        self.assertIn("automatically open", verification_stage)
        self.assertIn("official employer page", verification_stage)
        self.assertIn("clickable official links", verification_stage)
        self.assertIn("which role or roles they prefer", verification_stage)
        self.assertIn("do not finalize", verification_stage)

    def test_supported_reversible_actions_precede_manual_handoff(self):
        guide = GUIDED_WORKFLOW.read_text(encoding="utf-8")
        privacy = PRIVACY_GUIDE.read_text(encoding="utf-8")
        active_execution = guide.split("### Active execution principle", 1)[1].split(
            "### Improvement mode", 1
        )[0]
        self.assertIn("perform every safe and reversible step", active_execution)
        self.assertIn("Attempt a supported action before requesting manual help", active_execution)
        self.assertIn("smallest step required", active_execution)
        self.assertIn("Never imply", active_execution)
        self.assertIn("reversible browser navigation and form entry", privacy)
        for checkpoint in ("login", "CAPTCHA", "legal attestations", "consent", "final submit"):
            with self.subTest(checkpoint=checkpoint):
                self.assertIn(checkpoint, privacy)

    def test_resume_upload_parse_reconcile_and_review_contract(self):
        guide = APPLICATION_FORM_GUIDE.read_text(encoding="utf-8")
        guided_workflow = GUIDED_WORKFLOW.read_text(encoding="utf-8")
        required_contracts = (
            "Prefer upload-and-parse",
            "ask the user to perform only that smallest action",
            "do not copy, convert, or temporarily save the resume",
            "Compare parsed fields with explicit user-confirmed resume evidence",
            "fields Codex corrected or polished",
            "Ask whether the current form is accurate",
            "must not click the final submission control",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, guide)
        self.assertIn("read `application-form-filling.md`", guided_workflow)
        self.assertIn("check for resume upload and automatic parsing", guided_workflow)

    def test_confirmed_context_and_campus_only_scope_persist(self):
        guide = GUIDED_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Carry user-confirmed context forward", guide)
        self.assertIn("campus-only requirement", guide)
        self.assertIn("exclude social recruitment and ordinary internship projects", guide)
        self.assertIn("reuse the confirmed role direction and constraints", guide)
        self.assertIn("Do not restart discovery", guide)

    def test_visible_browser_session_and_experience_classification_contract(self):
        guide = APPLICATION_FORM_GUIDE.read_text(encoding="utf-8")
        required_contracts = (
            "different sessions even when they show the same URL",
            "Selecting a background tab or opening an empty duplicate is not sufficient",
            "exact populated tab or window",
            "which sections are populated, which contain parsing errors, and which remain blank",
            "internships belong under internship experience",
            "password-bearing, access-code, private-share",
            "Do not equate a complete form with a strong role match",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, guide)

    def test_successful_submission_respects_storage_boundary(self):
        guide = GUIDED_WORKFLOW.read_text(encoding="utf-8")
        close_stage = guide.split("### 9. Close and improve", 1)[1].split(
            "## Change-control checkpoint", 1
        )[0]
        self.assertIn("reports successful submission", close_stage)
        self.assertIn("only if the user previously allowed persistence", close_stage)
        self.assertIn("conversation-only", close_stage)


if __name__ == "__main__":
    unittest.main()
