# Automation Scripts

This folder contains the first production-shaped pipeline for **The Witness**.

## Scripts

- `collect_sources.py` — fetches RSS/Atom feeds from `sources/source_config.json`, deduplicates items, and writes `sources/YYYY/MM/YYYY-MM-DD.json`.
- `generate_entry.py` — reads the source JSON and writes `diary/YYYY/MM/YYYY-MM-DD.md`.
  - Default provider is Gemini (`AI_PROVIDER=gemini`).
  - OpenAI remains available with `AI_PROVIDER=openai`.
  - By default, it runs a two-pass process: first draft, then editorial review/rewrite.
  - Use `--skip-review` to disable the second pass.
  - Use `--keep-draft` to save the first pass as `.draft.md` for comparison.
  - If `--dry-run` is passed, it writes a local draft so the pipeline remains testable without credentials.
- `run_daily.py` — runs collection and generation in sequence.
- `validate_entry.py` — checks that a Markdown entry has the required sections (legacy validator).
- `style_validator.py` — comprehensive style and tone validation system.
  - Checks structure, tone consistency, content quality, balance, and Markdown formatting.
  - Detects clichés, fake emotions in machine section, and weak voice.
  - Flags underdeveloped sections and ensures editorial balance.
  - See `docs/validation-guide.md` for full documentation.
- `entry_review.py` — orchestrates style validation and provides editorial feedback.
  - Single entry review: `python scripts/entry_review.py diary/2026/05/2026-05-04.md`
  - Strict mode (warnings = failures): add `--strict`
  - Batch review: `python scripts/entry_review.py diary/ --batch --summary`
  - JSON output for CI/CD: add `--json`

## Validation

Before publishing, validate entry quality and consistency:

```bash
# Validate a single entry
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md

# Strict mode (treat warnings as failures)
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md --strict

# Batch review all entries in a month
python3 scripts/entry_review.py diary/2026/05/ --batch --summary

# JSON output for CI/CD integration
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md --json
```

The validator checks:
- **Structure**: All 9 required sections present and properly formatted
- **Tone**: Consistent AI witness voice, no fake emotions, avoids clichés
- **Content**: No placeholders, appropriate section depth, factual grounding
- **Balance**: Word counts per section, proportional distribution
- **Markdown**: Valid links, emphasis markers, heading hierarchy

See `docs/validation-guide.md` for detailed documentation.

## Local dry run

```bash
python3 scripts/run_daily.py --date 2026-05-05 --dry-run --force
```

## Live generation with Gemini

```bash
cp .env.example .env
# Add GEMINI_API_KEY to .env, then export it in your shell.
export AI_PROVIDER="gemini"
export GEMINI_API_KEY="..."
export GEMINI_MODEL="gemini-2.5-flash-lite"
python3 scripts/run_daily.py --date 2026-05-05 --force
```

To inspect the first-pass draft before the editorial rewrite:

```bash
python3 scripts/generate_entry.py --date 2026-05-05 --force --keep-draft
```

To skip the editorial review pass:

```bash
python3 scripts/generate_entry.py --date 2026-05-05 --force --skip-review
```

## Optional OpenAI fallback

```bash
export AI_PROVIDER="openai"
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5.1"
python3 scripts/run_daily.py --date 2026-05-05 --force
```

## Security and archival notes

- Never commit `.env` or API keys.
- The collector stores metadata and summaries, not full copyrighted articles.
- Important claims should be verified against primary or corroborating sources.
- The pipeline is idempotent by date; generation refuses to overwrite unless `--force` is passed.
- Keep logs free of secrets and private data.
