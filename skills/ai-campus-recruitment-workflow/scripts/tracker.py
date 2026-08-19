#!/usr/bin/env python3
"""Maintain a local CSV campus-application tracker."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIELDS = ["id", "company", "role", "cycle", "location", "applied_at", "deadline", "status", "next_action", "next_action_at", "official_url", "notes", "updated_at"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError("Unexpected tracker columns; initialize a new tracker or migrate explicitly")
        return list(reader)


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def next_id(rows: list[dict]) -> str:
    numbers = []
    for row in rows:
        value = row.get("id", "")
        if value.startswith("APP-") and value[4:].isdigit():
            numbers.append(int(value[4:]))
    return f"APP-{max(numbers, default=0) + 1:04d}"


def add_command(args) -> dict:
    path = Path(args.file)
    rows = read_rows(path)
    row = {field: "" for field in FIELDS}
    row.update({
        "id": next_id(rows), "company": args.company, "role": args.role,
        "cycle": args.cycle, "location": args.location, "applied_at": args.applied_at,
        "deadline": args.deadline, "status": args.status, "next_action": args.next_action,
        "next_action_at": args.next_action_at, "official_url": args.official_url,
        "notes": args.notes, "updated_at": now_iso(),
    })
    rows.append(row)
    write_rows(path, rows)
    return row


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--file", required=True)

    add = sub.add_parser("add")
    add.add_argument("--file", required=True)
    add.add_argument("--company", required=True)
    add.add_argument("--role", required=True)
    for name in ["cycle", "location", "applied-at", "deadline", "next-action", "next-action-at", "official-url", "notes"]:
        add.add_argument(f"--{name}", default="")
    add.add_argument("--status", default="待投递")

    update = sub.add_parser("update")
    update.add_argument("--file", required=True)
    update.add_argument("--id", required=True)
    for name in ["status", "applied-at", "deadline", "next-action", "next-action-at", "notes"]:
        update.add_argument(f"--{name}")

    listing = sub.add_parser("list")
    listing.add_argument("--file", required=True)
    listing.add_argument("--status")

    due = sub.add_parser("due")
    due.add_argument("--file", required=True)
    due.add_argument("--days", type=int, default=7)
    due.add_argument("--now", help="ISO timestamp for repeatable checks")

    args = parser.parse_args()
    path = Path(args.file)
    if args.command == "init":
        if path.exists():
            parser.error(f"Refusing to overwrite existing tracker: {path}")
        write_rows(path, [])
        print(f"Initialized tracker: {path}")
        return 0
    if args.command == "add":
        print(json.dumps(add_command(args), ensure_ascii=False, indent=2))
        return 0

    rows = read_rows(path)
    if args.command == "update":
        changed = False
        for row in rows:
            if row["id"] == args.id:
                for field in ["status", "applied_at", "deadline", "next_action", "next_action_at", "notes"]:
                    value = getattr(args, field)
                    if value is not None:
                        row[field] = value
                row["updated_at"] = now_iso()
                changed = True
                print(json.dumps(row, ensure_ascii=False, indent=2))
                break
        if not changed:
            parser.error(f"Application id not found: {args.id}")
        write_rows(path, rows)
        return 0
    if args.command == "list":
        selected = [row for row in rows if not args.status or row["status"] == args.status]
    else:
        start = parse_time(args.now) if args.now else datetime.now(timezone.utc)
        end = start + timedelta(days=args.days)
        selected = []
        for row in rows:
            candidates = [parse_time(row["deadline"]), parse_time(row["next_action_at"])]
            if any(value is not None and start <= value <= end for value in candidates):
                selected.append(row)
    print(json.dumps(selected, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
