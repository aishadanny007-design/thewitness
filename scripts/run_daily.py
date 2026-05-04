#!/usr/bin/env python3
"""Run the full daily pipeline: collect sources, generate entry, and validate."""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run The Witness daily pipeline.")
    parser.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Karachi")).date().isoformat())
    parser.add_argument("--dry-run", action="store_true", help="Skip OpenAI call and generate a local validation draft")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing diary entry")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation step")
    parser.add_argument("--strict-validation", action="store_true", help="Treat validation warnings as failures")
    args = parser.parse_args()

    commands = [
        [sys.executable, str(ROOT / "scripts" / "collect_sources.py"), "--date", args.date],
        [sys.executable, str(ROOT / "scripts" / "generate_entry.py"), "--date", args.date],
    ]
    if args.dry_run:
        commands[1].append("--dry-run")
    if args.force:
        commands[1].append("--force")

    for cmd in commands:
        print("$ " + " ".join(cmd))
        completed = subprocess.run(cmd, cwd=ROOT)
        if completed.returncode != 0:
            return completed.returncode
    
    # Run validation after generation
    if not args.skip_validation:
        print("\n🔍 Running validation...")
        # Construct path: diary/YYYY/MM/YYYY-MM-DD.md
        date_parts = args.date.split("-")
        entry_path = ROOT / "diary" / date_parts[0] / date_parts[1] / f"{args.date}.md"
        
        if not entry_path.exists():
            print(f"⚠️  Entry not found: {entry_path}", file=sys.stderr)
            return 1
        
        validate_cmd = [
            sys.executable, str(ROOT / "scripts" / "entry_review.py"),
            str(entry_path)
        ]
        
        if args.strict_validation:
            validate_cmd.append("--strict")
        
        print("$ " + " ".join(validate_cmd))
        completed = subprocess.run(validate_cmd, cwd=ROOT)
        
        if completed.returncode != 0:
            print("❌ Validation failed!", file=sys.stderr)
            if args.strict_validation:
                return completed.returncode
            else:
                print("⚠️  Continuing despite validation warnings (use --strict-validation to fail on warnings)")
        else:
            print("✅ Validation passed!")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
