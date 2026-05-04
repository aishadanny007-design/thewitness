#!/bin/bash
# Quick validation examples for The Witness

# Example 1: Validate a single entry
echo "=== Validating a single entry ==="
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md

# Example 2: Validate with strict mode (warnings = failures)
echo ""
echo "=== Validating with strict mode ==="
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md --strict

# Example 3: Batch review all entries in a directory
echo ""
echo "=== Batch review with summary ==="
python3 scripts/entry_review.py diary/2026/05/ --batch --summary

# Example 4: JSON output for integration
echo ""
echo "=== JSON output (for CI/CD) ==="
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md --json

echo ""
echo "See docs/validation-guide.md for more information."
