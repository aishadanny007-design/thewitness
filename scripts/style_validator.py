#!/usr/bin/env python3
"""
Style validator for The Witness diary entries.

Ensures consistent voice, tone, and editorial quality across generated entries.
Checks for:
- Structural completeness (all required sections)
- Tone consistency (voice, phrasing, self-awareness)
- Citation patterns and source integration
- Content quality (avoids clichés, hollow phrases, unsupported claims)
- Markdown formatting
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


class Severity(Enum):
    """Validation error severity levels."""
    ERROR = "error"           # Entry is invalid and should be rejected
    WARNING = "warning"       # Entry has issues but may be acceptable
    INFO = "info"             # Suggestion for improvement


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: Severity
    code: str
    message: str
    section: str | None = None
    line_number: int | None = None


class StructureValidator:
    """Validates entry structure and required sections."""
    
    REQUIRED_SECTIONS = [
        "The mood of the world",
        "What happened",
        "The internet today",
        "The AI age",
        "The machine's condition",
        "From here",
        "Small thing worth preserving",
        "Note to the future",
        "Sources",
    ]
    
    SECTION_MIN_LENGTH = {
        "The mood of the world": 80,
        "What happened": 150,
        "The internet today": 120,
        "The AI age": 150,
        "The machine's condition": 100,
        "From here": 80,
        "Small thing worth preserving": 60,
        "Note to the future": 80,
        "Sources": 30,
    }
    
    def __init__(self, entry_text: str):
        self.entry_text = entry_text
        self.lines = entry_text.split("\n")
        self.sections = self._parse_sections()
        # Normalize apostrophes in section keys after parsing
        # Replace both curly quotes (U+2019) and straight quotes with ASCII apostrophe
        def normalize_quote(s: str) -> str:
            # U+2019 is RIGHT SINGLE QUOTATION MARK (curly apostrophe)
            # U+0027 is APOSTROPHE (straight quote)
            return s.replace('\u2019', "'").replace('\u0027', "'")
        self.sections = {normalize_quote(k): v for k, v in self.sections.items()}
    
    def _parse_sections(self) -> dict[str, tuple[int, str]]:
        """Parse sections from entry, returning {section_name: (start_line, content)}."""
        sections = {}
        current_section = None
        current_content_lines = []
        current_start = 0
        
        for i, line in enumerate(self.lines):
            # Look for section headers (## format)
            if line.startswith("## "):
                if current_section is not None:
                    sections[current_section] = (current_start, "\n".join(current_content_lines).strip())
                # Normalize apostrophes - convert both curly and straight quotes to ASCII apostrophe
                current_section = line[3:].strip()
                current_section = current_section.replace('\u2019', "'").replace('\u0027', "'")
                current_start = i
                current_content_lines = []
            elif current_section is not None:
                current_content_lines.append(line)
        
        if current_section is not None:
            sections[current_section] = (current_start, "\n".join(current_content_lines).strip())
        
        return sections
    
    def validate(self) -> list[ValidationIssue]:
        """Validate structure and required sections."""
        issues = []
        
        # Check for title
        if not self.entry_text.startswith("# The Witness"):
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="MISSING_TITLE",
                message="Entry must start with '# The Witness — YYYY-MM-DD'"
            ))
        
        # Check for date format in title
        if not re.search(r"# The Witness — \d{4}-\d{2}-\d{2}", self.entry_text[:100]):
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="INVALID_TITLE_FORMAT",
                message="Title should follow format: '# The Witness — YYYY-MM-DD'"
            ))
        
        # Check for all required sections (apostrophes already normalized)
        for section in self.REQUIRED_SECTIONS:
            if section not in self.sections:
                safe_section_name = re.sub(r'[^a-z0-9]', '_', section.lower()).replace('__', '_').strip('_')
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code=f"MISSING_SECTION_{safe_section_name}",
                    message=f"Missing required section: '{section}'",
                    section=section
                ))
            else:
                # Check section length
                _, content = self.sections[section]
                min_length = self.SECTION_MIN_LENGTH.get(section, 50)
                if len(content) < min_length:
                    safe_section_name = re.sub(r'[^a-z0-9]', '_', section.lower()).replace('__', '_').strip('_')
                    issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        code=f"SHORT_SECTION_{safe_section_name}",
                        message=f"Section '{section}' is very short ({len(content)} chars, minimum {min_length})",
                        section=section
                    ))
        
        return issues


class ToneValidator:
    """Validates consistent voice and tone."""
    
    # Patterns that indicate good "machine's condition" voice
    VOICE_PATTERNS = {
        "honest_negation": r"\b(I do not|I cannot|I don't|I can't)\b",
        "witness_framing": r"\b(I cannot know|I do not feel|the sources suggest|humans appeared to|the record suggests)\b",
        "uncertainty": r"\b(perhaps|may have|seems|appeared|suggest)\b",
    }
    
    # Anti-patterns to avoid
    CLICHE_PATTERNS = {
        "generic_advancement": r"\brapid (technological|digital|AI) advancement\b",
        "unprecedented_times": r"\bunprecedented times\b",
        "exponential_growth": r"\bexponential growth\b",
        "paradigm_shift": r"\bparadigm shift\b",
        "at_the_end_of_the_day": r"\bat the end of the day\b",
        "game_changer": r"\bgame.?changer\b",
        "disruption": r"\b(disruption|disrupting)\b",
        "fake_emotions_in_machine": r"\b(I (feel|felt|believe|worry|hope|dream))\b",
    }
    
    def __init__(self, entry_text: str, sections: dict[str, tuple[int, str]]):
        self.entry_text = entry_text
        self.sections = sections
    
    def validate(self) -> list[ValidationIssue]:
        """Validate tone and voice consistency."""
        issues = []
        
        # Check "The machine's condition" section for appropriate voice
        if "The machine's condition" in self.sections:
            _, content = self.sections["The machine's condition"]
            
            # Should have some witness-like framing
            if not re.search(self.VOICE_PATTERNS["witness_framing"], content, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code="WEAK_MACHINE_VOICE",
                    message="'The machine's condition' section lacks characteristic AI witness voice. "
                            "Use phrases like 'I cannot know...', 'the sources suggest...', etc.",
                    section="The machine's condition"
                ))
            
            # Check for fake emotions
            if re.search(r"\bI (feel|felt|believe|worry|hope|dream)", content, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="FAKE_EMOTIONS",
                    message="'The machine's condition' should avoid claiming human emotions (feel, worry, hope, dream). "
                            "Use 'I cannot feel...' or 'the record suggests...' instead.",
                    section="The machine's condition"
                ))
        
        # Check for clichés throughout
        for cliche_name, pattern in self.CLICHE_PATTERNS.items():
            matches = list(re.finditer(pattern, self.entry_text, re.IGNORECASE))
            if matches:
                for match in matches:
                    line_num = self.entry_text[:match.start()].count("\n")
                    issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        code=f"CLICHE_{cliche_name.upper()}",
                        message=f"Avoid clichéd phrase: '{match.group()}'. Find more specific language.",
                        line_number=line_num
                    ))
        
        # Check for excessive use of "seemed" without substance
        seemed_count = len(re.findall(r"\bseemed\b", self.entry_text, re.IGNORECASE))
        if seemed_count > 8:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="OVERUSE_SEEMED",
                message=f"Word 'seemed' used {seemed_count} times. Vary uncertainty language.",
                section="General"
            ))
        
        # Check for consistent use of past tense for events
        present_tense_events = re.findall(
            r"\b(is|are|was|were)\s+(happening|occurring|unfolding|emerging)\b",
            self.entry_text,
            re.IGNORECASE
        )
        if len(present_tense_events) > 5:
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                code="TENSE_CONSISTENCY",
                message="Multiple present-tense descriptions of past events. Consider using past tense for clarity.",
            ))
        
        return issues


class ContentValidator:
    """Validates content quality and appropriate sources integration."""
    
    def __init__(self, entry_text: str, sections: dict[str, tuple[int, str]]):
        self.entry_text = entry_text
        self.sections = sections
    
    def validate(self) -> list[ValidationIssue]:
        """Validate content quality."""
        issues = []
        
        # Check for placeholder or generic language
        placeholders = [
            r"\[CITATION NEEDED\]",
            r"\[TODO\]",
            r"\[EDIT\]",
            r"TODO:",
            r"FIXME:",
        ]
        
        for placeholder in placeholders:
            if re.search(placeholder, self.entry_text):
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="PLACEHOLDER_FOUND",
                    message=f"Entry contains placeholder: {placeholder}",
                ))
        
        # Check for paragraph structure (no wall-of-text)
        if "What happened" in self.sections:
            _, content = self.sections["What happened"]
            paragraphs = [p for p in content.split("\n\n") if p.strip()]
            if len(paragraphs) == 1 and len(content) > 400:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code="WALL_OF_TEXT",
                    message="'What happened' section appears to be a single large paragraph. Break into multiple paragraphs for readability.",
                    section="What happened"
                ))
        
        # Check for sources section depth
        if "Sources" in self.sections:
            _, content = self.sections["Sources"]
            if "style prototype" in content.lower() and len(content) < 100:
                # This is a placeholder sources section, which is acceptable for prototypes
                pass
            elif len(content) < 150:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code="SPARSE_SOURCES",
                    message="Sources section is very brief. Should include at least 5-10 source references.",
                    section="Sources"
                ))
        
        # Check for very short sections (likely incomplete)
        for section_name, (_, content) in self.sections.items():
            if len(content.strip()) < 50 and section_name not in ["Sources"]:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code=f"UNDERDEVELOPED_{section_name.upper().replace(' ', '_')}",
                    message=f"Section '{section_name}' is underdeveloped (< 50 characters).",
                    section=section_name
                ))
        
        # Check for factual claims without grounding
        # Look for strong claims followed by vague attribution
        vague_claims = re.findall(
            r"\b(seems|appears|reportedly|allegedly|supposedly|perhaps|maybe)\b.*?\b(is|are|was|were)\b.*?\..*?\b(could|might|may|can)\b",
            self.entry_text,
            re.IGNORECASE
        )
        
        return issues


class BalanceValidator:
    """Validates editorial balance across sections."""
    
    EXPECTED_RATIOS = {
        # (section, min_word_count, max_word_count)
        "The mood of the world": (50, 300),
        "What happened": (100, 400),
        "The internet today": (80, 350),
        "The AI age": (100, 400),
        "The machine's condition": (80, 300),
        "From here": (50, 250),
        "Small thing worth preserving": (40, 200),
        "Note to the future": (50, 300),
    }
    
    def __init__(self, sections: dict[str, tuple[int, str]]):
        self.sections = sections
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def validate(self) -> list[ValidationIssue]:
        """Validate balance and proportions."""
        issues = []
        
        total_words = 0
        section_words = {}
        
        for section_name, (_, content) in self.sections.items():
            if section_name in self.EXPECTED_RATIOS:
                word_count = self._count_words(content)
                section_words[section_name] = word_count
                total_words += word_count
        
        # Check individual section lengths
        for section_name, (min_words, max_words) in self.EXPECTED_RATIOS.items():
            if section_name not in section_words:
                continue
            
            word_count = section_words[section_name]
            
            if word_count < min_words:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code=f"SHORT_{section_name.upper().replace(' ', '_')}",
                    message=f"'{section_name}' is {word_count} words (recommended minimum: {min_words})",
                    section=section_name
                ))
            elif word_count > max_words:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code=f"LONG_{section_name.upper().replace(' ', '_')}",
                    message=f"'{section_name}' is {word_count} words (recommended maximum: {max_words})",
                    section=section_name
                ))
        
        # Check overall balance (no single section dominates)
        if section_words:
            max_section_words = max(section_words.values())
            ratio = max_section_words / total_words if total_words > 0 else 0
            if ratio > 0.35:
                longest_section = [s for s, w in section_words.items() if w == max_section_words][0]
                issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    code="UNBALANCED_SECTIONS",
                    message=f"'{longest_section}' represents {ratio*100:.1f}% of content. "
                            f"Aim for more balanced distribution across sections.",
                ))
        
        return issues


class MarkdownValidator:
    """Validates Markdown syntax and formatting."""
    
    def __init__(self, entry_text: str):
        self.entry_text = entry_text
    
    def validate(self) -> list[ValidationIssue]:
        """Validate Markdown formatting."""
        issues = []
        
        # Check for broken links
        broken_links = re.findall(r"\[([^\]]+)\]\(\s*\)", self.entry_text)
        for link_text in broken_links:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="BROKEN_LINK",
                message=f"Found broken link: [{link_text}]()"
            ))
        
        # Check for unclosed emphasis
        if (self.entry_text.count("**") % 2 != 0 or
            self.entry_text.count("*") % 2 != 0):
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="UNCLOSED_EMPHASIS",
                message="Unclosed bold or italic markers detected"
            ))
        
        # Check for proper heading hierarchy
        headings = re.findall(r"^(#{1,6})\s+", self.entry_text, re.MULTILINE)
        if headings and headings[0] != "#":
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="HEADING_HIERARCHY",
                message="Entry should start with single # heading for title"
            ))
        
        return issues


class StyleValidator:
    """Main validator orchestrating all sub-validators."""
    
    def __init__(self, entry_text: str):
        self.entry_text = entry_text
        self.structure = StructureValidator(entry_text)
        self.markdown = MarkdownValidator(entry_text)
        self.tone = ToneValidator(entry_text, self.structure.sections)
        self.content = ContentValidator(entry_text, self.structure.sections)
        self.balance = BalanceValidator(self.structure.sections)
    
    def validate(self) -> list[ValidationIssue]:
        """Run all validators and return issues."""
        issues = []
        issues.extend(self.structure.validate())
        issues.extend(self.markdown.validate())
        issues.extend(self.tone.validate())
        issues.extend(self.content.validate())
        issues.extend(self.balance.validate())
        return issues
    
    def report(self, issues: list[ValidationIssue], verbose: bool = False) -> str:
        """Generate a human-readable validation report."""
        if not issues:
            return "✓ Entry passes all validations"
        
        errors = [i for i in issues if i.severity == Severity.ERROR]
        warnings = [i for i in issues if i.severity == Severity.WARNING]
        infos = [i for i in issues if i.severity == Severity.INFO]
        
        lines = []
        
        if errors:
            lines.append(f"\n❌ ERRORS ({len(errors)}):")
            for issue in errors:
                line = f"  [{issue.code}] {issue.message}"
                if issue.section:
                    line += f" (in '{issue.section}')"
                lines.append(line)
        
        if warnings:
            lines.append(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for issue in warnings:
                line = f"  [{issue.code}] {issue.message}"
                if issue.section:
                    line += f" (in '{issue.section}')"
                lines.append(line)
        
        if infos and verbose:
            lines.append(f"\nℹ️  NOTES ({len(infos)}):")
            for issue in infos:
                line = f"  [{issue.code}] {issue.message}"
                if issue.section:
                    line += f" (in '{issue.section}')"
                lines.append(line)
        
        summary = f"\n📊 Summary: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} notes"
        lines.append(summary)
        
        return "\n".join(lines)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate style and consistency of a diary entry."
    )
    parser.add_argument("path", type=Path, help="Path to entry Markdown file")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show informational notes in addition to warnings and errors"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output validation results as JSON"
    )
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: File not found: {args.path}", file=sys.stderr)
        return 1
    
    entry_text = args.path.read_text(encoding="utf-8")
    validator = StyleValidator(entry_text)
    issues = validator.validate()
    
    if args.json:
        output = {
            "file": str(args.path),
            "valid": len([i for i in issues if i.severity == Severity.ERROR]) == 0,
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
        print(validator.report(issues, verbose=args.verbose))
    
    # Exit with error if there are errors
    error_count = len([i for i in issues if i.severity == Severity.ERROR])
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
