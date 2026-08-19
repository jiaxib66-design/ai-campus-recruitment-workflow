#!/usr/bin/env python3
"""Normalize recruiting clues from CSV, JSON, or plain text into JSON."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def normalize(item: dict, default_time: str) -> dict:
    return {
        "company": str(item.get("company", "")).strip(),
        "clue": str(item.get("clue", item.get("text", ""))).strip(),
        "url": str(item.get("url", "")).strip(),
        "source_type": str(item.get("source_type", "unknown")).strip() or "unknown",
        "observed_at": str(item.get("observed_at", default_time)).strip(),
        "verification_status": "unverified",
        "official_url": "",
        "verification_notes": "",
    }


def load_items(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("clues", [data])
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            raise ValueError("JSON must be an object or a list of objects")
        return data
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [{"clue": line, "source_type": "text"} for line in lines]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--observed-at", help="Stable ISO timestamp used when the source omits one")
    args = parser.parse_args()

    source = Path(args.input)
    default_time = args.observed_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    normalized = [normalize(item, default_time) for item in load_items(source)]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"clues": normalized}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(normalized)} unverified clue(s) to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
