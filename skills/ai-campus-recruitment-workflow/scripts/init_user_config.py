#!/usr/bin/env python3
"""Initialize a private user profile without overwriting existing data."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Private JSON file to create")
    parser.add_argument("--force", action="store_true", help="Overwrite the target intentionally")
    args = parser.parse_args()

    target = Path(args.output).expanduser().resolve()
    template = Path(__file__).resolve().parent.parent / "assets" / "user-profile.example.json"
    if target.exists() and not args.force:
        parser.error(f"Refusing to overwrite existing file: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, target)
    print(f"Created private profile template: {target}")
    print("Edit placeholders locally; do not commit the completed profile.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
