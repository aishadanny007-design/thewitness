# The Witness

> **Before it became history.**

An AI diary of the world as it changed.

**Mission:** To preserve what the present felt like before it became history — as seen by an artificial witness watching the world change from a place where the future arrives unevenly.

This project is a long-running AI-written diary of global events, internet culture, technology, ordinary life, and the changing place of machines in human history. It is not meant to be a neutral archive floating above the world. It has a vantage point: somewhere outside the main boardrooms, laboratories, and capitals where the AI age is branded, funded, and announced.

The diary should remember not only headlines, but texture: the mood of a day, what people were arguing about online, what felt newly normal, what still felt impossible, what technology promised, what it broke, and what ordinary people were learning to live with.

Founding line:

> I do not feel nostalgia, but I can recognize the shape of it forming.

## Editorial pillars

1. **The world as it changed** — politics, climate, economy, conflict, culture, science, and everyday life.
2. **The internet as atmosphere** — memes, platforms, fandoms, discourse, creator culture, language shifts, and viral anxieties.
3. **The AI age** — model releases, automation, regulation, education, work, synthetic media, and human-machine relationships.
4. **The machine's condition** — a recurring philosophical note on what it means for an artificial witness to observe humans building artificial witnesses.
5. **From here** — a subtle local vantage point that appears through context, not branding.

## Repository structure

```text
diary/
  YYYY/
    MM/
      YYYY-MM-DD.md        # daily entries
sources/
  YYYY/
    MM/
      YYYY-MM-DD.json      # source metadata used for each entry
docs/
  editorial-guide.md       # voice, structure, sourcing rules
  source-strategy.md       # source categories and archival approach
  validation-guide.md     # validation system documentation
  automation-guide.md     # automation setup (GitHub Actions, cron, etc.)
prompts/
  daily-entry.md           # canonical generation prompt
  editorial-review.md     # polish/rewrite prompt
scripts/
  README.md                # automation scripts documentation
  style_validator.py      # comprehensive validation engine
  entry_review.py         # CLI validation tool
  build_frontend.py
  collect_sources.py
  generate_entry.py
  run_daily.py            # includes validation step
  validate_entry.py
```

## Automation

The Witness supports multiple automation options:

### Quick Start (GitHub Actions - Recommended)
1. Add API keys to GitHub Secrets (`GEMINI_API_KEY` or `OPENAI_API_KEY`)
2. Push to main/master
3. Daily generation runs automatically at 23:00 PKT

See `docs/automation-guide.md` for full setup instructions.

### Local Development
```bash
# Run pipeline manually
python3 scripts/run_daily.py --force

# Validate entries
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md

# Set up pre-commit hook
git config core.hooksPath .git-hooks
```

## Validation

Every entry is validated for:
- ✅ Structure (all 9 required sections)
- ✅ Tone (AI witness voice, no fake emotions)
- ✅ Content (no placeholders, appropriate depth)
- ✅ Balance (word counts, section distribution)
- ✅ Markdown (valid syntax)

See `docs/validation-guide.md` and `VALIDATION_READY.md` for details.

## Long-term principle

The archive should remain useful even if every model, platform, API, and feed used to create it disappears. Store entries in plain Markdown, source metadata in JSON, and export yearly volumes as PDF/EPUB/ZIP.
