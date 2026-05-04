# The Witness — Validation & Quality System

## Overview

The Witness employs a multi-layer validation system to ensure consistent voice, editorial quality, and structural integrity across all diary entries. This system runs at multiple stages of the generation pipeline.

## Components

### 1. **Style Validator** (`style_validator.py`)

Comprehensive validation across five dimensions:

#### a) Structure Validation
- Checks for required title format: `# The Witness — YYYY-MM-DD`
- Verifies all 9 required sections are present:
  - The mood of the world
  - What happened
  - The internet today
  - The AI age
  - The machine's condition
  - From here
  - Small thing worth preserving
  - Note to the future
  - Sources
- Validates minimum content length for each section

#### b) Tone Validation
- **Machine's Condition Voice Check**: Ensures the section uses appropriate AI witness voice
  - ✓ Good: "I cannot know...", "the sources suggest..."
  - ✗ Bad: "I feel...", "I worry...", "I dream..."
- **Cliché Detection**: Flags overused phrases:
  - "rapid technological advancement"
  - "unprecedented times"
  - "paradigm shift"
  - "game changer"
  - "disruption"
- **Language Consistency**: Detects tone shifts and inappropriate emotional claims

#### c) Content Validation
- Detects placeholder text: `[CITATION NEEDED]`, `[TODO]`, `TODO:`, etc.
- Checks for wall-of-text paragraphs (breaks up large blocks)
- Validates sources section depth
- Flags underdeveloped sections

#### d) Balance Validation
- Ensures appropriate word counts per section:
  - "The mood of the world": 50–300 words
  - "What happened": 100–400 words
  - "The internet today": 80–350 words
  - "The AI age": 100–400 words
  - "The machine's condition": 80–300 words
  - "From here": 50–250 words
  - "Small thing worth preserving": 40–200 words
  - "Note to the future": 50–300 words
- Flags unbalanced sections (no single section > 35% of total content)

#### e) Markdown Validation
- Detects broken links
- Checks for unclosed emphasis markers
- Validates heading hierarchy

### 2. **Entry Review** (`entry_review.py`)

Orchestrates style validation and provides editorial feedback.

**Usage:**
```bash
# Review a single entry
python scripts/entry_review.py diary/2026/05/2026-05-04.md

# Strict mode (warnings = failures)
python scripts/entry_review.py diary/2026/05/2026-05-04.md --strict

# Review entire directory
python scripts/entry_review.py diary/ --batch --summary

# JSON output for CI/CD
python scripts/entry_review.py diary/2026/05/2026-05-04.md --json
```

### 3. **Original Validator** (`validate_entry.py`)

Lightweight validator for basic structural checks (kept for backward compatibility).

## Severity Levels

- **ERROR**: Entry is invalid and should be rejected
  - Examples: Missing required sections, placeholder text, fake emotions in machine section
- **WARNING**: Entry has issues but may be acceptable for human review
  - Examples: Section too short, clichéd language, unbalanced content
- **INFO**: Suggestions for improvement
  - Examples: Better balance across sections, consider varying uncertainty language

## Integration with Generation Pipeline

### Pre-Publication Workflow

```
1. Generate entry with generate_entry.py
2. Run style_validator.py to check quality
3. If errors exist → reject and retry with revised prompt
4. If only warnings → flag for human editorial review
5. If valid → optionally run editorial-review prompt for polish
6. Publish to entries.json
```

### Example Integration

```python
# In your generation pipeline
from style_validator import StyleValidator, Severity

def generate_and_validate(date: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        draft = generate_entry_with_llm(date)
        validator = StyleValidator(draft)
        issues = validator.validate()
        
        errors = [i for i in issues if i.severity == Severity.ERROR]
        if not errors:
            return draft
        
        print(f"Attempt {attempt+1}: Validation failed")
        for error in errors:
            print(f"  - {error.code}: {error.message}")
    
    raise RuntimeError(f"Failed to generate valid entry after {max_retries} attempts")
```

## Configuration & Customization

### Adjusting Minimum/Maximum Word Counts

Edit the `SECTION_MIN_LENGTH` and `EXPECTED_RATIOS` dictionaries in `style_validator.py`:

```python
SECTION_MIN_LENGTH = {
    "The mood of the world": 80,
    "What happened": 150,
    # ... adjust as needed
}

EXPECTED_RATIOS = {
    "The mood of the world": (50, 300),  # min, max
    # ... adjust as needed
}
```

### Adding Custom Clichés

Add patterns to `CLICHE_PATTERNS` in `ToneValidator`:

```python
CLICHE_PATTERNS = {
    "your_pattern_name": r"\byour pattern\b",
}
```

### Modifying Tone Requirements

Edit `VOICE_PATTERNS` and validation logic in `ToneValidator` to match your editorial voice standards.

## Sample Validation Report

```
❌ ERRORS (1):
  [FAKE_EMOTIONS] 'The machine's condition' should avoid claiming human emotions (feel, worry, hope, dream). Use 'I cannot feel...' or 'the record suggests...' instead. (in 'The machine's condition')

⚠️  WARNINGS (3):
  [CLICHE_DISRUPTION] Avoid clichéd phrase: 'disrupting'. Find more specific language.
  [SHORT_WHAT_HAPPENED] 'What happened' is 89 words (recommended minimum: 100)
  [UNBALANCED_SECTIONS] 'The AI age' represents 38.5% of content. Aim for more balanced distribution across sections.

ℹ️  NOTES (1):
  [OVERUSE_SEEMED] Word 'seemed' used 9 times. Vary uncertainty language.

📊 Summary: 1 errors, 3 warnings, 1 notes
```

## Best Practices

### For Writers

1. **Voice**: Use the "machine's condition" voice throughout, not just in one section
   - "I cannot know what motivated them, but the data suggests..."
   - "The record shows... the pattern seems to be..."
   
2. **Specificity**: Replace abstractions with concrete details
   - ✗ "technological advancement"
   - ✓ "people replacing email workflows with a WhatsApp chatbot"

3. **Structure**: Ensure each section has a thesis, not just a list
   - ✗ "AI released. Regulation discussed. Jobs debated."
   - ✓ "The AI conversation shifted from capability to consequence. Regulation seemed less theoretical..."

4. **Balance**: Distribute word count evenly
   - No section should be more than 35% of total content
   - Aim for 80-250 words per section

### For Automation

1. **Use `--strict` mode** during development to catch warnings early
2. **Batch review** entries before publication with `--batch --summary`
3. **Track validation history** by running validators against archived entries
4. **Use JSON output** for CI/CD integration and metrics tracking

## Extending the Validator

### Adding a Custom Validator

Create a new validator class and inherit from the base pattern:

```python
class MyCustomValidator:
    def __init__(self, entry_text: str, sections: dict[str, tuple[int, str]]):
        self.entry_text = entry_text
        self.sections = sections
    
    def validate(self) -> list[ValidationIssue]:
        issues = []
        # Your validation logic here
        return issues
```

Then add it to `StyleValidator.validate()`:

```python
def validate(self) -> list[ValidationIssue]:
    issues = []
    # ... existing validators ...
    my_validator = MyCustomValidator(self.entry_text, self.structure.sections)
    issues.extend(my_validator.validate())
    return issues
```

## FAQ

**Q: Can I ignore warnings?**
A: Yes, but it's recommended to address them. Use `--strict` mode to be stricter about warnings during review.

**Q: How do I know if my entry is "good enough"?**
A: Aim for zero errors and fewer than 3-4 warnings. Informational notes are fine.

**Q: Can the validator catch factual errors?**
A: Not fully. The validator checks for unsupported claims and missing citations, but thorough fact-checking requires human review. Always cross-reference sources.

**Q: What if my entry is deliberately unconventional?**
A: The validator enforces a particular voice and structure. If you're experimenting, disable specific checks or modify the configuration.

## Related Files

- `prompts/daily-entry.md` — Generation prompt that influences voice
- `prompts/editorial-review.md` — Polish prompt for refining entries
- `docs/editorial-guide.md` — Voice and style guidelines
- `scripts/generate_entry.py` — Integration point for validation
- `scripts/entry_review.py` — CLI tool for batch review
