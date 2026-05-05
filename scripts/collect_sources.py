#!/usr/bin/env python3
"""Collect RSS/Atom source metadata for The Witness.

No third-party dependencies. Designed to be idempotent and safe for cron/GitHub Actions.
It stores metadata and short summaries, not full article text.
"""
from __future__ import annotations

import argparse
import email.utils
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "sources" / "source_config.json"
USER_AGENT = "TheWitnessDiary/0.1 (+https://example.com; source metadata collector)"
XML_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
INVALID_XML_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


@dataclass(frozen=True)
class Feed:
    name: str
    url: str
    category: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        except ValueError:
            continue
    return value[:80]


def clean_text(value: str | None, limit: int) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = TAG_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rsplit(" ", 1)[0].rstrip() + "…"


def child_text(el: ET.Element, names: tuple[str, ...], limit: int = 10000) -> str:
    for name in names:
        found = el.find(name, XML_NS)
        if found is not None and found.text:
            return clean_text(found.text, limit)
    return ""


def rss_link(item: ET.Element) -> str:
    link = child_text(item, ("link",), 2000)
    if link:
        return link
    guid = child_text(item, ("guid",), 2000)
    return guid if guid.startswith("http") else ""


def atom_link(entry: ET.Element) -> str:
    for link in entry.findall("atom:link", XML_NS):
        href = link.attrib.get("href", "").strip()
        rel = link.attrib.get("rel", "alternate")
        if href and rel == "alternate":
            return href
    return ""


def stable_id(url: str, title: str) -> str:
    raw = (url or title).strip().lower().encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:16]


def fetch_url(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(2_000_000)


def parse_feed(feed: Feed, payload: bytes, per_feed: int, summary_chars: int, accessed_at: str) -> list[dict[str, Any]]:
    payload = INVALID_XML_RE.sub(b"".decode(), payload.decode("utf-8", errors="replace")).encode("utf-8")
    root = ET.fromstring(payload)
    records: list[dict[str, Any]] = []

    rss_items = root.findall(".//channel/item")
    if rss_items:
        for item in rss_items[:per_feed]:
            title = child_text(item, ("title",), 500)
            url = rss_link(item)
            summary = child_text(item, ("description", "content:encoded"), summary_chars)
            author = child_text(item, ("dc:creator", "author"), 200) or None
            published_at = parse_date(child_text(item, ("pubDate", "dc:date"), 200))
            if title or url:
                records.append(source_record(feed, title, url, summary, author, published_at, accessed_at))
        return records

    atom_entries = root.findall("atom:entry", XML_NS)
    for entry in atom_entries[:per_feed]:
        title = child_text(entry, ("atom:title",), 500)
        url = atom_link(entry)
        summary = child_text(entry, ("atom:summary", "atom:content"), summary_chars)
        author_el = entry.find("atom:author", XML_NS)
        author = child_text(author_el, ("atom:name",), 200) if author_el is not None else None
        published_at = parse_date(child_text(entry, ("atom:published", "atom:updated"), 200))
        if title or url:
            records.append(source_record(feed, title, url, summary, author, published_at, accessed_at))
    return records


def source_record(feed: Feed, title: str, url: str, summary: str, author: str | None, published_at: str | None, accessed_at: str) -> dict[str, Any]:
    return {
        "id": stable_id(url, title),
        "title": title,
        "url": url,
        "publisher": feed.name,
        "author": author,
        "published_at": published_at,
        "accessed_at": accessed_at,
        "category": feed.category,
        "summary": summary,
        "archive_url": None,
        "reliability_note": "RSS/Atom metadata; verify important claims against primary or corroborating sources.",
    }


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def output_path(date: str) -> Path:
    y, m, _ = date.split("-")
    return ROOT / "sources" / y / m / f"{date}.json"


def collect(config: dict[str, Any], date: str, timeout: float) -> dict[str, Any]:
    limits = config.get("limits", {})
    per_feed = int(limits.get("per_feed", 8))
    total_sources = int(limits.get("total_sources", 60))
    summary_chars = int(limits.get("summary_chars", 360))
    
    # Load category allocation targets to prevent Western bias
    source_allocation = config.get("source_allocation", {
        "global_news": 18,
        "regional_asia": 12,
        "regional_africa": 8,
        "regional_latam": 8,
        "regional_middle_east": 6,
        "ai_tech": 10,
        "internet_culture": 8,
        "local_vantage": 10,
        "economy_climate": 6
    })
    
    accessed_at = utc_now()
    all_sources: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for raw_feed in config.get("feeds", []):
        feed = Feed(name=raw_feed["name"], url=raw_feed["url"], category=raw_feed["category"])
        try:
            payload = fetch_url(feed.url, timeout=timeout)
            all_sources.extend(parse_feed(feed, payload, per_feed, summary_chars, accessed_at))
            time.sleep(0.2)
        except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError, ValueError) as exc:
            errors.append({"feed": feed.name, "url": feed.url, "error": str(exc)[:300]})

    deduped: dict[str, dict[str, Any]] = {}
    for source in all_sources:
        deduped.setdefault(source["id"], source)

    # Apply weighted selection to balance categories and meet allocation targets
    # This prevents tech-Western bias by ensuring Global South and regional voices are included
    all_sources_list = sorted(
        deduped.values(),
        key=lambda s: (s.get("published_at") or "", s.get("publisher") or "", s.get("title") or ""),
        reverse=True,
    )
    
    # Allocate sources by category to meet targets
    selected_by_category: dict[str, list[dict[str, Any]]] = {}
    for category in source_allocation:
        selected_by_category[category] = []
    
    # First pass: prioritize underrepresented categories
    for source in all_sources_list:
        category = source.get("category", "other")
        target = source_allocation.get(category, 5)
        
        if len(selected_by_category.get(category, [])) < target:
            selected_by_category.setdefault(category, []).append(source)
    
    # Flatten and sort by recency, respecting allocation limits
    sources = []
    for category, target in source_allocation.items():
        sources.extend(selected_by_category.get(category, [])[:target])
    
    sources = sorted(
        sources,
        key=lambda s: (s.get("published_at") or "", s.get("publisher") or "", s.get("title") or ""),
        reverse=True,
    )[:total_sources]

    return {
        "date": date,
        "generated_at": accessed_at,
        "project": config.get("project", {}),
        "sources": sources,
        "errors": errors,
        "note": "Source metadata only. Important claims must be verified before publication.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect daily source metadata for The Witness.")
    parser.add_argument("--date", default=datetime.now().date().isoformat(), help="Entry date in YYYY-MM-DD format; pass explicitly from run_daily.py for Asia/Karachi default")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()

    config = load_config(args.config)
    doc = collect(config, args.date, args.timeout)
    out = args.output or output_path(args.date)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(doc['sources'])} sources to {out}")
    if doc["errors"]:
        print(f"Encountered {len(doc['errors'])} feed errors", file=sys.stderr)
    return 0 if doc["sources"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
