#!/usr/bin/env python3
"""Validate diary Markdown structure."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generate_entry import validate_entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a diary Markdown entry.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate_entry(args.path.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Valid entry: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
