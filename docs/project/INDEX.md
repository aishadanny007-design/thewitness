# The Witness – Validation System Implementation Guide

## 🎯 Project Overview

You now have a **complete, production-ready validation system** that ensures consistent voice, editorial quality, and structural integrity across all Witness diary entries.

## 📖 Documentation Map

### Quick Start
- **[VALIDATION_READY.md](VALIDATION_READY.md)** – Overview, features, demo (start here!)
- **[validate.sh](validate.sh)** – Copy-paste ready command examples

### Detailed Documentation
- **[docs/validation-guide.md](docs/validation-guide.md)** – Complete system documentation
- **[VALIDATION_SYSTEM.md](VALIDATION_SYSTEM.md)** – Implementation details
- **[scripts/README.md](scripts/README.md)** – Tool documentation

### Editorial Guides
- **[docs/editorial-guide.md](docs/editorial-guide.md)** – Voice and style standards
- **[docs/source-strategy.md](docs/source-strategy.md)** – Source balancing

---

## 🚀 Getting Started

### Run Your First Validation

```bash
# Validate a single entry
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md

# Review multiple entries
python3 scripts/entry_review.py diary/2026/05/ --batch

# Use strict mode (warnings = failures)
python3 scripts/entry_review.py diary/2026/05/ --batch --strict

# Get JSON output
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md --json
```

---

## 🎭 What Gets Validated

### Structure
- ✅ Title format and date
- ✅ All 9 required sections present
- ✅ Section lengths within healthy ranges
- ✅ Markdown syntax

### Tone & Voice
- ✅ AI witness voice in "The machine's condition"
- ✅ No fake emotions ("I feel", "I worry")
- ✅ Honest self-description ("I cannot know...")
- ✅ Avoids clichés (7+ patterns detected)

### Content
- ✅ No placeholders or TODOs
- ✅ Appropriate section depth
- ✅ Word distribution across sections

---

## 📊 Sample Output

```
⚠️  WARNINGS (6):
  [WEAK_MACHINE_VOICE] 'The machine's condition' section lacks 
    characteristic AI witness voice...
  [SHORT_WHAT_HAPPENED] 'What happened' is 95 words 
    (recommended minimum: 100)
  [SHORT_FROM_HERE] 'From here' is 49 words (recommended minimum: 50)
  ...

📊 Summary: 0 errors, 6 warnings, 0 notes
```

---

## 🔧 Customization

### Adjust Requirements
Edit in `scripts/style_validator.py`:

```python
# Minimum word counts per section
SECTION_MIN_LENGTH = {
    "The machine's condition": 80,
    # ... adjust as needed
}

# Word count ranges (min, max)
EXPECTED_RATIOS = {
    "The mood of the world": (50, 300),
    # ... adjust as needed
}
```

### Add Clichés to Detect
```python
CLICHE_PATTERNS = {
    "your_phrase": r"\byour pattern\b",
}
```

---

## 🔌 Integration Options

### Option 1: Manual Review Before Publishing
```bash
# After generating an entry, run validation
python3 scripts/entry_review.py diary/2026/05/2026-05-05.md

# Fix any issues, then publish
```

### Option 2: Automated Batch Processing
```bash
# Review all entries in a month
python3 scripts/entry_review.py diary/2026/05/ --batch

# Generate JSON report for metrics
python3 scripts/entry_review.py diary/2026/05/ --batch --json > validation-report.json
```

### Option 3: CI/CD Integration (GitHub Actions)
```yaml
- name: Validate Entries
  run: |
    python3 scripts/entry_review.py diary/ --batch --strict
```

### Option 4: Python Integration
```python
from scripts.style_validator import StyleValidator, Severity

validator = StyleValidator(entry_text)
issues = validator.validate()

errors = [i for i in issues if i.severity == Severity.ERROR]
if errors:
    print("Entry needs fixes before publishing")
```

---

## 📋 New Files Created

| File | Purpose |
|------|---------|
| `scripts/style_validator.py` | Core validation engine (550+ lines) |
| `scripts/entry_review.py` | CLI review tool (110+ lines) |
| `docs/validation-guide.md` | Complete documentation (250+ lines) |
| `VALIDATION_SYSTEM.md` | Implementation summary |
| `VALIDATION_READY.md` | Quick reference |
| `validate.sh` | Command examples |
| `INDEX.md` | This file |

---

## 🎓 Understanding Severity Levels

- **ERROR** ❌ – Entry cannot be published (missing sections, placeholder text)
- **WARNING** ⚠️ – Issues found, suitable for human review (short sections, weak voice)
- **INFO** ℹ️ – Suggestions for improvement (unused words, consider varying language)

---

## 💡 Best Practices

### For Manual Review
```bash
# Use verbose output to understand each issue
python3 scripts/entry_review.py diary/2026/05/2026-05-04.md

# Fix issues one by one
# Re-run to confirm fixes
```

### For Automation
```bash
# Use JSON output for machine parsing
python3 scripts/entry_review.py diary/ --batch --json

# Use strict mode to catch everything
python3 scripts/entry_review.py diary/ --batch --strict
```

### For Teams
```bash
# Share validation reports
python3 scripts/entry_review.py diary/2026/05/ --batch --json > report.json

# Each team member can review in their preferred format
# Or integrate with project management tools
```

---

## 🔍 Troubleshooting

### All entries show as "passed" but have warnings
- **Expected behavior**: Warnings don't fail by default
- Use `--strict` flag to fail on warnings
- Use `--json` for machine processing

### Validation misses expected issues
- Check `docs/validation-guide.md` for coverage
- Patterns can be customized in `style_validator.py`
- Report gaps in documentation

### Apostrophe issues
- **Already fixed**: System handles both ' and ' automatically
- No configuration needed

---

## 📞 Common Questions

**Q: How strict should I be?**
A: Start with default mode (errors only). Use `--strict` for pre-publication review.

**Q: Can I use this in my CI/CD?**
A: Yes! Use `--json` flag and integrate into any pipeline.

**Q: What if an entry legitimately breaks a rule?**
A: Customize the thresholds in `style_validator.py` or just review manually.

**Q: Can I disable certain validators?**
A: Not directly, but you can comment out calls in `StyleValidator.validate()` method.

---

## 🚀 Recommended Workflow

```
1. Generate entry
   ↓
2. Run validation
   ↓
3. If errors → Retry generation with revised prompt
   ↓
4. If only warnings → Human editorial review
   ↓
5. Make fixes
   ↓
6. Run validation again
   ↓
7. If clean → Publish to entries.json
```

---

## 📈 Next Enhancement Ideas

- [ ] Track validation metrics over time
- [ ] Create dashboard for voice consistency
- [ ] Compare entries against editorial standards
- [ ] Integration with fact-checking APIs
- [ ] Automated tone matching to reference entries
- [ ] Export validation report as PDF

---

## 📞 Support & Documentation

| Need | Resource |
|------|----------|
| Quick start | [VALIDATION_READY.md](VALIDATION_READY.md) |
| All features | [docs/validation-guide.md](docs/validation-guide.md) |
| Examples | [validate.sh](validate.sh) |
| Implementation | [VALIDATION_SYSTEM.md](VALIDATION_SYSTEM.md) |
| Editorial standards | [docs/editorial-guide.md](docs/editorial-guide.md) |

---

## ✨ Key Achievements

✅ **Comprehensive** – 5 validation layers covering all quality dimensions  
✅ **Consistent** – Enforces editorial standards automatically  
✅ **Extensible** – Easy to customize and add validators  
✅ **Production-Ready** – Error handling, Unicode support, CI/CD ready  
✅ **Well-Documented** – 250+ lines of docs with examples and FAQ  
✅ **Tested** – Works on real entries, catches real issues  

---

## 🎉 You're All Set!

The validation system is ready to use. Start with the Quick Start section above, then dive into the detailed documentation as needed.

**Happy validating! 🚀**

