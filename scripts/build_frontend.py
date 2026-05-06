#!/usr/bin/env python3
"""Build static frontend data from Markdown diary entries."""
from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DIARY_DIR = ROOT / "diary"
PUBLIC_DIR = ROOT / "public"
ENTRY_JSON = PUBLIC_DIR / "entries.json"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass(frozen=True)
class Entry:
    date: str
    title: str
    path: Path
    html: str
    excerpt: str


def extract_date(path: Path) -> str:
    return path.stem


def inline_markdown(text: str, hide_citations: bool = False) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    
    # Hide citation numbers [1, 5, 36] style if requested (for prose readability)
    if hide_citations:
        escaped = re.sub(r'\s*\[\d+(?:,\s*\d+)*\]', '', escaped)

    def repl(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        url = html.escape(match.group(2), quote=True)
        return f'<a href="{url}" rel="noopener noreferrer" target="_blank">{label}</a>'

    return LINK_RE.sub(repl, escaped)


def markdown_to_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            # Hide citation numbers in prose for better readability
            blocks.append(f"<p>{inline_markdown(' '.join(paragraph), hide_citations=True)}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            # Hide citations in list items too
            blocks.append("<ul>" + "".join(f"<li>{inline_markdown(item, hide_citations=True)}</li>" for item in list_items) + "</ul>")
            list_items = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue
        heading = HEADING_RE.match(line)
        if heading:
            flush_paragraph()
            flush_list()
            level = min(len(heading.group(1)), 4)
            text = inline_markdown(heading.group(2))
            if level == 1:
                blocks.append(f'<header class="entry-header"><p class="entry-kicker">Latest entry</p><h2 id="entry-title">{text}</h2></header>')
            elif level == 2:
                if "sources" in heading.group(2).lower():
                    section_class = ' class="sources-section"'
                elif "machine" in heading.group(2).lower():
                    section_class = ' class="machine-condition"'
                else:
                    section_class = ""
                blocks.append(f"<section{section_class}><h3>{text}</h3>")
            else:
                blocks.append(f"<h{level + 1}>{text}</h{level + 1}>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            list_items.append(line[2:].strip())
            continue
        paragraph.append(line)

    flush_paragraph()
    flush_list()

    # Close sections opened by h2 headings. Keep the initial header outside entry-body.
    rendered: list[str] = []
    open_section = False
    for block in blocks:
        if block.startswith("<section"):
            if open_section:
                rendered.append("</section>")
            open_section = True
        rendered.append(block)
    if open_section:
        rendered.append("</section>")
    
    # Post-process: Convert source lists to styled source grid
    result = "\n".join(rendered)
    
    # Wrap sources section list in grid div
    sources_pattern = r'(<section class="sources-section"><h3>Sources</h3>)\n(<ul>.*?</ul>)\n(</section>)'
    sources_replacement = r'\1\n<div class="sources-grid">\n\2\n</div>\n\3'
    result = re.sub(sources_pattern, sources_replacement, result, flags=re.DOTALL)
    
    return result


def title_from_markdown(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 1:
            return match.group(2).strip()
    return fallback


def excerpt_from_markdown(markdown: str, max_chars: int = 170) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("["):
            plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", stripped)
            return plain[: max_chars - 1].rstrip() + "…" if len(plain) > max_chars else plain
    return "A diary entry from The Witness."


def read_entries(include_future: bool = False, today: str | None = None) -> list[Entry]:
    entries: list[Entry] = []
    today = today or datetime.now(ZoneInfo("Asia/Karachi")).date().isoformat()
    for path in DIARY_DIR.glob("[0-9][0-9][0-9][0-9]/*/*.md"):
        markdown = path.read_text(encoding="utf-8")
        date = extract_date(path)
        if not include_future and date > today:
            continue
        entries.append(
            Entry(
                date=date,
                title=title_from_markdown(markdown, f"The Witness — {date}"),
                path=path.relative_to(ROOT),
                html=markdown_to_html(markdown),
                excerpt=excerpt_from_markdown(markdown),
            )
        )
    return sorted(entries, key=lambda e: e.date, reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build frontend JSON data from diary Markdown.")
    parser.add_argument("--include-future", action="store_true", help="Include entries dated after today")
    parser.add_argument("--today", default=None, help="Override today's date in YYYY-MM-DD format for builds/tests")
    args = parser.parse_args()
    entries = read_entries(include_future=args.include_future, today=args.today)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": "static-build",
        "entries": [
            {
                "date": e.date,
                "title": e.title,
                "path": str(e.path),
                "excerpt": e.excerpt,
                "html": e.html,
            }
            for e in entries
        ],
    }
    ENTRY_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} entries to {ENTRY_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
