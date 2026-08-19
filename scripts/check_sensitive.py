#!/usr/bin/env python3
"""Fail when repository text resembles common personal data or committed secrets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "private", "output", "dist", "build"}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py", ".toml", ".ini", ".cfg", ".env", ""}
PATTERNS = {
    "Chinese mobile number": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "Chinese resident ID": re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:auth(?:orization)?[_-]?code|api[_-]?key|secret|password|token)\s*[=:]\s*[\"']?([^\s\"']{8,})"
)


def scan(root: Path) -> list[str]:
    findings = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{path.relative_to(root)}:{line_no}: {label}")
            assignment = SECRET_ASSIGNMENT.search(line)
            if assignment:
                value = assignment.group(1)
                placeholder_markers = ("<", ">", "example", "placeholder", "your-", "os.environ", "getenv")
                if not any(marker.casefold() in value.casefold() or marker.casefold() in line.casefold() for marker in placeholder_markers):
                    findings.append(f"{path.relative_to(root)}:{line_no}: possible literal secret")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=".")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    findings = scan(root)
    if findings:
        print("Potential sensitive data found:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Sensitive-data scan passed (heuristic; manual review is still required).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
