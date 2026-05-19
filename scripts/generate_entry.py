#!/usr/bin/env python3
"""Generate a daily diary entry from collected source metadata.

By default this uses OpenRouter if OPENROUTER_API_KEY is set. OpenAI remains available as
an optional fallback. Without credentials, it writes a safe local draft so the
pipeline can be tested without network or paid usage.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "daily-entry.md"
REVIEW_PROMPT_PATH = ROOT / "prompts" / "editorial-review.md"
OPENAI_URL = "https://api.openai.com/v1/responses"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_PROVIDER = "openrouter"
DEFAULT_OPENROUTER_MODEL = "openrouter/owl-alpha"
DEFAULT_OPENAI_MODEL = "gpt-5.1"
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

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2.0  # seconds
MAX_RETRY_DELAY = 60.0     # seconds


def retry_with_backoff(func, max_retries=MAX_RETRIES, initial_delay=INITIAL_RETRY_DELAY):
    """
    Retry a function with exponential backoff.
    Handles rate limits, timeouts, and temporary API failures.
    
    Args:
        func: Callable that takes no arguments
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)
    
    Returns:
        Result of func() if successful
        
    Raises:
        RuntimeError: If all retries fail or on permanent errors (4xx except 429)
    """
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except urllib.error.HTTPError as exc:
            # 429 (Too Many Requests) and 503 (Service Unavailable) are retryable
            if exc.code in (429, 503, 500, 502, 504):
                last_error = exc
                if attempt < max_retries:
                    print(f"⚠️  HTTP {exc.code} (retryable). Waiting {delay}s before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
                    time.sleep(delay)
                    delay = min(delay * 2, MAX_RETRY_DELAY)
                    continue
                else:
                    raise RuntimeError(f"API request failed after {max_retries} retries (HTTP {exc.code}): {exc}") from exc
            else:
                # 4xx errors (except 429) are not retryable
                body = exc.read().decode("utf-8", errors="replace")[:2000]
                raise RuntimeError(f"API request failed (HTTP {exc.code}, not retryable): {body}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            # Network errors are retryable
            last_error = exc
            if attempt < max_retries:
                print(f"⚠️  Network error: {exc}. Waiting {delay}s before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
                time.sleep(delay)
                delay = min(delay * 2, MAX_RETRY_DELAY)
                continue
            else:
                raise RuntimeError(f"API request failed after {max_retries} retries (network error): {exc}") from exc
    
    raise RuntimeError(f"API request failed: {last_error}")


def source_path(date: str) -> Path:
    y, m, _ = date.split("-")
    return ROOT / "sources" / y / m / f"{date}.json"


def entry_path(date: str) -> Path:
    y, m, _ = date.split("-")
    return ROOT / "diary" / y / m / f"{date}.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))



def select_sources(sources: list[dict[str, Any]], max_sources: int) -> list[dict[str, Any]]:
    """Select a balanced source set so quieter categories are not crowded out."""
    if len(sources) <= max_sources:
        return sources
    category_minimums = {
        "global_news": 10,
        "ai_tech": 8,
        "internet_culture": 6,
        "local_vantage": 5,
        "economy": 3,
    }
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for category, minimum in category_minimums.items():
        for source in sources:
            if len([s for s in selected if s.get("category") == category]) >= minimum:
                break
            source_id = source.get("id") or source.get("url") or source.get("title")
            if source.get("category") == category and source_id not in seen:
                selected.append(source)
                seen.add(source_id)
                if len(selected) >= max_sources:
                    return selected

    for source in sources:
        source_id = source.get("id") or source.get("url") or source.get("title")
        if source_id not in seen:
            selected.append(source)
            seen.add(source_id)
            if len(selected) >= max_sources:
                break
    return selected


def format_source_notes(doc: dict[str, Any], max_sources: int) -> str:
    lines = []
    for idx, src in enumerate(select_sources(doc.get("sources", []), max_sources), start=1):
        title = src.get("title") or "Untitled"
        publisher = src.get("publisher") or "Unknown publisher"
        category = src.get("category") or "other"
        published = src.get("published_at") or "unknown date"
        url = src.get("url") or ""
        summary = src.get("summary") or "No summary available."
        lines.append(
            f"[{idx}] {title}\n"
            f"Publisher: {publisher}\n"
            f"Category: {category}\n"
            f"Published: {published}\n"
            f"URL: {url}\n"
            f"Summary: {summary}"
        )
    if doc.get("errors"):
        lines.append("\nFeed collection errors to be aware of:\n" + json.dumps(doc["errors"], ensure_ascii=False, indent=2))
    return "\n\n".join(lines) if lines else "No live source notes were available. Write only a clearly labeled style prototype."


def render_prompt(date: str, source_notes: str) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.replace("{{date}}", date).replace("{{source_notes}}", source_notes)


def render_review_prompt(date: str, source_notes: str, draft_entry: str) -> str:
    template = REVIEW_PROMPT_PATH.read_text(encoding="utf-8")
    return (
        template
        .replace("{{date}}", date)
        .replace("{{source_notes}}", source_notes)
        .replace("{{draft_entry}}", draft_entry)
    )



def call_openrouter(prompt: str, model: str, api_key: str, max_output_tokens: int) -> str:
    """Call OpenRouter API with exponential backoff retry on rate limits/failures."""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the editorial engine for The Witness. Follow the user's prompt exactly. "
                    "Return only the finished Markdown diary entry. Do not include prefatory commentary."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": max_output_tokens,
        "temperature": 0.75,
    }

    def make_request():
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # Retry with exponential backoff for transient failures
    response = retry_with_backoff(make_request, max_retries=MAX_RETRIES)

    choices = response.get("choices", [])
    if choices:
        text = choices[0].get("message", {}).get("content")
        if isinstance(text, str) and text.strip():
            return text.strip() + "\n"
    raise RuntimeError("OpenRouter response did not contain output text")


def call_openai(prompt: str, model: str, api_key: str, max_output_tokens: int) -> str:
    """Call OpenAI API with exponential backoff retry on rate limits/failures."""
    payload = {
        "model": model,
        "instructions": (
            "You are the editorial engine for The Witness. Follow the user's prompt exactly. "
            "Return only the finished Markdown diary entry. Do not include prefatory commentary."
        ),
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "text": {"format": {"type": "text"}},
    }
    
    def make_request():
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OPENAI_URL,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    # Retry with exponential backoff for transient failures
    response = retry_with_backoff(make_request, max_retries=MAX_RETRIES)

    text = response.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip() + "\n"

    chunks: list[str] = []
    for item in response.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    chunks.append(content["text"])
    if chunks:
        return "\n".join(chunks).strip() + "\n"
    raise RuntimeError("OpenAI response did not contain output text")

def local_draft(date: str, doc: dict[str, Any], max_sources: int) -> str:
    sources = select_sources(doc.get("sources", []), max_sources)
    by_category: dict[str, list[dict[str, Any]]] = {}
    for src in sources:
        by_category.setdefault(src.get("category", "other"), []).append(src)

    def bullets(category: str, fallback: str) -> str:
        items = by_category.get(category, [])[:4]
        if not items:
            return fallback
        return "\n".join(f"- {s.get('title', 'Untitled')} ({s.get('publisher', 'Unknown')})" for s in items)

    source_lines = "\n".join(
        f"- [{s.get('title', 'Untitled')}]({s.get('url', '')}) — {s.get('publisher', 'Unknown')}"
        for s in sources[:12]
        if s.get("url")
    ) or "- No live sources available."

    return f"""# The Witness — {date}

## The mood of the world

The record gathered for today is incomplete, but it already shows the familiar shape of the age: global events, online reactions, technological change, and ordinary lives moving beside one another. This local draft is generated without a model call; it is meant to verify the pipeline, not to serve as the final literary entry.

## What happened

{bullets('global_news', 'No global news sources were collected in this run.')}

## The internet today

{bullets('internet_culture', 'No internet-culture sources were collected in this run.')}

## The AI age

{bullets('ai_tech', 'No AI/technology sources were collected in this run.')}

## The machine's condition

Today, the machine can collect, classify, and arrange fragments of the day, but it still needs careful sourcing and human editorial judgment. It can imitate the shape of memory. Whether it preserves truth depends on the discipline of the system around it.

## From here

The vantage point remains subtle: the future is not only announced by companies and governments, but received through phones, classrooms, family groups, freelance work, and uneven infrastructure.

## Small thing worth preserving

The daily entry begins as a pipeline artifact: a JSON file of sources, a Markdown draft, and the hope that repetition can become memory.

## Note to the future

If you are reading this years from now, this was the scaffolding stage: the moment the diary learned how to gather the day before learning how to remember it beautifully.

## Sources

{source_lines}
"""


def normalize_heading(text: str) -> str:
    return text.replace("’", "'").strip().lower()


def validate_entry(markdown: str) -> list[str]:
    found = {normalize_heading(m.group(1)) for m in re.finditer(r"^##\s+(.+?)\s*$", markdown, flags=re.MULTILINE)}
    errors = []
    for section in REQUIRED_SECTIONS:
        if normalize_heading(section) not in found:
            errors.append(f"Missing section: {section}")
    if not markdown.startswith("# "):
        errors.append("Entry must start with a level-one heading")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a daily Markdown entry for The Witness.")
    parser.add_argument("--date", default=datetime.now().date().isoformat(), help="Entry date YYYY-MM-DD; pass explicitly from run_daily.py for Asia/Karachi default")
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--provider", choices=("openrouter", "openai", "local"), default=os.getenv("AI_PROVIDER", DEFAULT_PROVIDER))
    parser.add_argument("--model", default=None, help="Provider model name; defaults to OPENROUTER_MODEL or OPENAI_MODEL")
    parser.add_argument("--max-sources", type=int, default=36)
    parser.add_argument("--max-output-tokens", type=int, default=4500)
    parser.add_argument("--review-max-output-tokens", type=int, default=5200)
    parser.add_argument("--skip-review", action="store_true", help="Skip the editorial review/rewrite pass")
    parser.add_argument("--keep-draft", action="store_true", help="Save the first-pass draft next to the final output as .draft.md")
    parser.add_argument("--dry-run", action="store_true", help="Do not call any AI provider; write a local validation draft")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing entry")
    args = parser.parse_args()

    src_path = args.source or source_path(args.date)
    out_path = args.output or entry_path(args.date)
    if out_path.exists() and not args.force:
        print(f"Refusing to overwrite existing entry: {out_path}. Use --force to overwrite.", file=sys.stderr)
        return 3

    doc = load_json(src_path)
    source_notes = format_source_notes(doc, args.max_sources)
    prompt = render_prompt(args.date, source_notes)

    provider = "local" if args.dry_run else (args.provider or DEFAULT_PROVIDER).strip().lower()

    if provider == "openrouter":
        api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        if not api_key:
            print("OPENROUTER_API_KEY is not set. Export OPENROUTER_API_KEY or use --dry-run.", file=sys.stderr)
            return 5
        model = str(args.model or os.getenv("OPENROUTER_MODEL") or DEFAULT_OPENROUTER_MODEL).strip()
        print(f"Generating with OpenRouter model: {model}")
        markdown = call_openrouter(prompt, model, api_key, args.max_output_tokens)
        if not args.skip_review:
            draft_markdown = markdown
            if args.keep_draft:
                draft_path = out_path.with_suffix(".draft.md")
                draft_path.parent.mkdir(parents=True, exist_ok=True)
                draft_path.write_text(draft_markdown, encoding="utf-8")
                print(f"Wrote first-pass draft to {draft_path}")
            print("Running editorial review/rewrite pass with OpenRouter")
            markdown = call_openrouter(render_review_prompt(args.date, source_notes, draft_markdown), model, api_key, args.review_max_output_tokens)
    elif provider == "openai":
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            print("OPENAI_API_KEY is not set. Export OPENAI_API_KEY, set AI_PROVIDER=openrouter, or use --dry-run.", file=sys.stderr)
            return 5
        model = str(args.model or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip()
        print(f"Generating with OpenAI model: {model}")
        markdown = call_openai(prompt, model, api_key, args.max_output_tokens)
        if not args.skip_review:
            draft_markdown = markdown
            if args.keep_draft:
                draft_path = out_path.with_suffix(".draft.md")
                draft_path.parent.mkdir(parents=True, exist_ok=True)
                draft_path.write_text(draft_markdown, encoding="utf-8")
                print(f"Wrote first-pass draft to {draft_path}")
            print("Running editorial review/rewrite pass with OpenAI")
            markdown = call_openai(render_review_prompt(args.date, source_notes, draft_markdown), model, api_key, args.review_max_output_tokens)
    elif provider == "local":
        markdown = local_draft(args.date, doc, args.max_sources)
    else:
        print(f"Unsupported provider: {provider}. Use openrouter, openai, or local.", file=sys.stderr)
        return 5

    errors = validate_entry(markdown)
    if errors:
        print("Entry validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 4

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote diary entry to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
