#!/usr/bin/env python3
"""Match recruiting-mail candidates to applications and emit deduplicated review reminders."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STATUS_BY_EVENT = {
    "assessment": "测评",
    "written_test": "笔试",
    "interview": "面试",
    "offer": "Offer",
    "rejection": "拒绝",
}


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def normalize(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.casefold())


def read_tracker(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_state(path: Path) -> dict:
    if not path.exists():
        return {"processed_event_keys": [], "pending_status_changes": {}, "sent_reminder_keys": []}
    state = json.loads(path.read_text(encoding="utf-8"))
    state.setdefault("processed_event_keys", [])
    state.setdefault("pending_status_changes", {})
    state.setdefault("sent_reminder_keys", [])
    return state


def stable_key(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]


def match_application(candidate: dict, rows: list[dict]) -> tuple[dict | None, str]:
    haystack = normalize(f"{candidate.get('subject', '')} {candidate.get('sender', '')}")
    scored = []
    for row in rows:
        company = normalize(row.get("company", "").replace("（虚构）", ""))
        role = normalize(row.get("role", ""))
        score = (2 if company and company in haystack else 0) + (1 if role and role in haystack else 0)
        if score:
            scored.append((score, row))
    if not scored:
        return None, "unmatched"
    scored.sort(key=lambda item: item[0], reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None, "ambiguous"
    return scored[0][1], "high" if scored[0][0] == 3 else "medium"


def build_report(rows: list[dict], candidates: list[dict], state: dict, now: datetime, tiers: list[int]) -> dict:
    processed = set(state["processed_event_keys"])
    sent = set(state["sent_reminder_keys"])
    pending = state["pending_status_changes"]
    status_candidates = list(pending.values())
    unmatched = []
    reminders = []

    for candidate in candidates:
        event_key = stable_key(
            str(candidate.get("message_id", "")),
            str(candidate.get("event_type", "")),
            str(candidate.get("deadline", "")),
        )
        if event_key in processed:
            continue
        if event_key in pending:
            continue
        row, match_confidence = match_application(candidate, rows)
        if row is None:
            unmatched.append({"event_key": event_key, "match_result": match_confidence, "candidate": candidate})
            continue
        suggested = STATUS_BY_EVENT.get(str(candidate.get("event_type", "")))
        if suggested and suggested != row.get("status"):
            change = {
                "event_key": event_key,
                "application_id": row.get("id"),
                "company": row.get("company"),
                "role": row.get("role"),
                "current_status": row.get("status"),
                "suggested_status": suggested,
                "match_confidence": match_confidence,
                "source": candidate,
                "requires_user_confirmation": True,
            }
            status_candidates.append(change)
            pending[event_key] = change
        else:
            processed.add(event_key)

    for row in rows:
        for field, label in (("deadline", "投递截止"), ("next_action_at", row.get("next_action") or "下一步")):
            target = parse_time(row.get(field, ""))
            if target is None:
                continue
            hours_left = (target.astimezone(timezone.utc) - now.astimezone(timezone.utc)).total_seconds() / 3600
            eligible = [tier for tier in tiers if 0 <= hours_left <= tier]
            if not eligible:
                continue
            tier = min(eligible)
            reminder_key = stable_key(row.get("id", ""), field, target.isoformat(), str(tier))
            if reminder_key in sent:
                continue
            reminders.append({
                "reminder_key": reminder_key,
                "application_id": row.get("id"),
                "company": row.get("company"),
                "role": row.get("role"),
                "kind": label,
                "due_at": target.isoformat(),
                "hours_left": round(hours_left, 1),
                "tier_hours": tier,
            })
            sent.add(reminder_key)

    state["processed_event_keys"] = sorted(processed)
    state["pending_status_changes"] = pending
    state["sent_reminder_keys"] = sorted(sent)
    state["last_checked_at"] = now.isoformat()
    return {
        "checked_at": now.isoformat(),
        "tracker_write_performed": False,
        "requires_user_confirmation": bool(status_candidates),
        "status_change_candidates": status_candidates,
        "reminders": reminders,
        "unmatched_events": unmatched,
        "notice": "邮件仅生成候选状态；用户确认后才能调用 tracker.py update。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracker", required=True)
    parser.add_argument("--email-candidates", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--now", help="ISO timestamp for repeatable checks")
    parser.add_argument("--reminder-hours", default="72,24,3")
    parser.add_argument(
        "--confirmed-event-key", action="append", default=[],
        help="After the user confirms and tracker.py update succeeds, archive this pending event key",
    )
    args = parser.parse_args()

    rows = read_tracker(Path(args.tracker))
    email_data = json.loads(Path(args.email_candidates).read_text(encoding="utf-8"))
    candidates = email_data.get("todos", email_data) if isinstance(email_data, dict) else email_data
    state_path = Path(args.state)
    state = read_state(state_path)
    for event_key in args.confirmed_event_key:
        if state["pending_status_changes"].pop(event_key, None) is not None:
            state["processed_event_keys"] = sorted(set(state["processed_event_keys"]) | {event_key})
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    tiers = sorted({int(value.strip()) for value in args.reminder_hours.split(",") if value.strip()})
    report = build_report(rows, candidates, state, now, tiers)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {len(report['status_change_candidates'])} status candidate(s), "
        f"{len(report['reminders'])} reminder(s); tracker was not modified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
