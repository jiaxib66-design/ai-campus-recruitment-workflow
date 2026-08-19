#!/usr/bin/env python3
"""Read recruiting mail via IMAP or mock JSON and extract reviewable deadline candidates."""

from __future__ import annotations

import argparse
import email
import imaplib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from pathlib import Path

EVENT_WORDS = {
    "测评": "assessment", "笔试": "written_test", "面试": "interview",
    "材料": "materials", "assessment": "assessment", "interview": "interview",
    "written test": "written_test", "deadline": "deadline",
}
DATE_PATTERNS = [
    re.compile(r"(?P<date>20\d{2}-\d{1,2}-\d{1,2})[ T](?P<time>\d{1,2}:\d{2})(?:\s*(?P<tz>北京时间|UTC\+?8|CST))?", re.I),
    re.compile(r"(?P<date>20\d{2}年\d{1,2}月\d{1,2}日)(?:\s*(?P<time>\d{1,2}[:：]\d{2}))?(?:\s*(?P<tz>北京时间))?"),
]


def decode_value(value: str | None) -> str:
    parts = []
    for chunk, charset in decode_header(value or ""):
        parts.append(chunk.decode(charset or "utf-8", errors="replace") if isinstance(chunk, bytes) else chunk)
    return "".join(parts)


def body_text(message: email.message.Message) -> str:
    if message.is_multipart():
        texts = []
        for part in message.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                payload = part.get_payload(decode=True) or b""
                texts.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
        return "\n".join(texts)
    payload = message.get_payload(decode=True) or b""
    return payload.decode(message.get_content_charset() or "utf-8", errors="replace")


def normalize_date(date_text: str, time_text: str | None, tz_text: str | None) -> tuple[str, str]:
    normalized = date_text.replace("年", "-").replace("月", "-").replace("日", "")
    year, month, day = (int(x) for x in normalized.split("-"))
    hour, minute = (0, 0)
    if time_text:
        hour, minute = (int(x) for x in time_text.replace("：", ":").split(":"))
    tz = timezone(timedelta(hours=8)) if tz_text else None
    value = datetime(year, month, day, hour, minute, tzinfo=tz)
    return value.isoformat(), ("Asia/Shanghai" if tz_text else "unknown")


def extract_candidates(messages: list[dict]) -> list[dict]:
    output = []
    for message in messages:
        subject = str(message.get("subject", ""))
        body = str(message.get("body", ""))
        text = f"{subject}\n{body}"
        event = next((kind for word, kind in EVENT_WORDS.items() if word.casefold() in text.casefold()), "recruiting_event")
        for pattern in DATE_PATTERNS:
            for match in pattern.finditer(text):
                deadline, timezone_name = normalize_date(match.group("date"), match.groupdict().get("time"), match.groupdict().get("tz"))
                output.append({
                    "event_type": event,
                    "deadline": deadline,
                    "timezone": timezone_name,
                    "confidence": "medium" if timezone_name == "unknown" else "high",
                    "subject": subject,
                    "message_id": str(message.get("message_id", "")),
                    "source_excerpt": match.group(0),
                    "requires_user_confirmation": True,
                })
    return output


def fetch_messages(since_days: int, limit: int) -> list[dict]:
    host = os.environ.get("RECRUITMENT_IMAP_HOST", "imap.163.com")
    user = os.environ.get("RECRUITMENT_IMAP_USER")
    auth_code = os.environ.get("RECRUITMENT_IMAP_AUTH_CODE")
    if not user or not auth_code:
        raise RuntimeError("Set RECRUITMENT_IMAP_USER and RECRUITMENT_IMAP_AUTH_CODE in the environment")
    since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%d-%b-%Y")
    messages = []
    with imaplib.IMAP4_SSL(host) as client:
        client.login(user, auth_code)
        status, _ = client.select("INBOX", readonly=True)
        if status != "OK":
            raise RuntimeError("Unable to open INBOX read-only")
        status, data = client.search(None, "SINCE", since)
        if status != "OK":
            raise RuntimeError("IMAP search failed")
        for msg_id in data[0].split()[-limit:]:
            status, payload = client.fetch(msg_id, "(BODY.PEEK[])")
            if status != "OK" or not payload or not isinstance(payload[0], tuple):
                continue
            parsed = email.message_from_bytes(payload[0][1])
            messages.append({"message_id": decode_value(parsed.get("Message-ID")), "subject": decode_value(parsed.get("Subject")), "body": body_text(parsed)})
        client.logout()
    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    mock = sub.add_parser("mock", help="Use offline fictional messages")
    mock.add_argument("--input", required=True)
    mock.add_argument("--output", required=True)
    fetch = sub.add_parser("fetch", help="Read IMAP after explicit user confirmation")
    fetch.add_argument("--output", required=True)
    fetch.add_argument("--since-days", type=int, default=30)
    fetch.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    if args.command == "mock":
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        messages = data.get("messages", data) if isinstance(data, dict) else data
    else:
        messages = fetch_messages(args.since_days, args.limit)
    result = {
        "calendar_write_performed": False,
        "notice": "请逐条核验候选事项；确认前不得写入日历。",
        "todos": extract_candidates(messages),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(result['todos'])} review candidate(s) to {output}; no calendar write was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
