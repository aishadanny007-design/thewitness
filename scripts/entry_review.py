#!/usr/bin/env python3
"""
Entry quality review script.

Runs comprehensive validations on a diary entry before publication.
Can be integrated into CI/CD or used manually for editorial review.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Import validators
from style_validator import (
    StyleValidator,
    Severity,
)


def review_entry(entry_path: Path, strict: bool = False) -> tuple[bool, str, list]:
    """
    Review a diary entry for quality and consistency.
    
    Args:
        entry_path: Path to the entry Markdown file
        strict: If True, treat warnings as failures
    
    Returns:
        (is_valid, report_text, issues_list)
    """
    if not entry_path.exists():
        return False, f"Error: File not found: {entry_path}", []
    
    entry_text = entry_path.read_text(encoding="utf-8")
    validator = StyleValidator(entry_text)
    issues = validator.validate()
    
    # Filter by severity
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    
    # Determine if valid
    is_valid = len(errors) == 0
    if strict and len(warnings) > 0:
        is_valid = False
    
    report = validator.report(issues, verbose=True)
    return is_valid, report, issues


def review_batch(directory: Path, pattern: str = "*.md") -> dict[str, tuple[bool, str]]:
    """Review all matching entries in a directory."""
    results = {}
    for entry_file in sorted(directory.glob(pattern)):
        if entry_file.name.startswith("_"):
            continue
        is_valid, report = review_entry(entry_file)
        results[entry_file.name] = (is_valid, report)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review a diary entry for quality and consistency."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to entry file or directory of entries"
    )
    parser.add_argument(
        "-s", "--strict",
        action="store_true",
        help="Treat warnings as failures (strict mode)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Review all .md files in directory"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show only summary, not detailed report"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output validation results as JSON"
    )
    
    args = parser.parse_args()
    
    if args.batch and args.path.is_dir():
        print(f"📋 Reviewing entries in {args.path}...\n")
        results = review_batch(args.path)
        
        passed = sum(1 for valid, _ in results.values() if valid)
        total = len(results)
        
        if not args.summary:
            for filename, (is_valid, report) in results.items():
                status = "✓" if is_valid else "✗"
                print(f"{status} {filename}")
                if not args.summary:
                    print(f"  {report}")
                print()
        
        print(f"\n📊 Summary: {passed}/{total} entries passed")
        return 0 if passed == total else 1
    
    else:
        is_valid, report, issues = review_entry(args.path, strict=args.strict)
        
        if args.json:
            # Output JSON format
            output = {
                "file": str(args.path),
                "valid": is_valid,
                "issues": [
                    {
                        "severity": i.severity.value,
                        "code": i.code,
                        "message": i.message,
                        "section": i.section,
                        "line": i.line_number,
                    }
                    for i in issues
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            print(report)
        
        return 0 if is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
