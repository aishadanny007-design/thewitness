# Automation Guide - The Witness

## Overview

This guide covers all automation options for The Witness diary pipeline, from local development hooks to cloud-based CI/CD.

---

## 🚀 Automation Options

### 1. **GitHub Actions** (Recommended for Production)
- ✅ Fully automated daily generation
- ✅ Validation included
- ✅ Automatic commits
- ✅ Artifact storage for reports

### 2. **Pre-commit Hooks** (Recommended for Local Development)
- ✅ Catches issues before commit
- ✅ Fast feedback loop
- ✅ Prevents bad entries from entering repo

### 3. **Cron Jobs** (Alternative for Self-Hosted)
- ✅ Simple Unix-based scheduling
- ✅ Works without GitHub
- ⚠️ Requires server maintenance

### 4. **Integrated Pipeline** (run_daily.py)
- ✅ Manual or script-triggered
- ✅ Includes validation step
- ✅ Flexible options

---

## 🤖 Option 1: GitHub Actions (Recommended)

### Setup

1. **Ensure `.github/workflows/daily-pipeline.yml` exists** (already created)

2. **Add Secrets to GitHub**:
   - Go to: `Settings` → `Secrets and variables` → `Actions`
   - Add these secrets:
     - `GEMINI_API_KEY` (if using Gemini)
     - `OPENAI_API_KEY` (if using OpenAI)
     - `GEMINI_MODEL` (optional, defaults to `gemini-2.5-flash-lite`)
     - `OPENAI_MODEL` (optional, defaults to `gpt-5.1`)
     - `AI_PROVIDER` (optional, defaults to `gemini`)

3. **Trigger Options**:
   - **Automatic**: Runs daily at 23:00 PKT (18:00 UTC)
   - **Manual**: Go to `Actions` → `The Witness - Daily Pipeline` → `Run workflow`
   - **Push**: Runs validation on pushes to main/master

### What It Does

```
Daily at 23:00 PKT:
  1. Checkout repository
  2. Set up Python 3.11
  3. Install dependencies from requirements.txt
  4. Determine date (Asia/Karachi timezone)
  5. Run: collect_sources.py → generate_entry.py
  6. Validate generated entry (non-strict mode, continues on warning)
  7. Validate with strict mode (blocks on errors)
  8. Generate JSON validation report
  9. Commit and push changes
  10. Upload validation report as artifact
  11. Notify on failure (GitHub Actions notification)
```

### Customization

Edit `.github/workflows/daily-pipeline.yml`:

```yaml
# Change schedule (cron format: minute hour day month day-of-week)
schedule:
  - cron: '0 18 * * *'  # 18:00 UTC = 23:00 PKT

# Skip validation
on:
  workflow_dispatch:
    inputs:
      skip_validation:
        description: 'Skip validation step'
        required: false
        type: boolean
        default: false
```

---

## 🪝 Option 2: Pre-commit Hooks (Local Development)

### Setup

1. **Install the hook**:
```bash
cd /Users/dan/Desktop/diaryjournal
git config core.hooksPath .git-hooks
# OR manually:
cp .git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

2. **Test it**:
```bash
# Stage a diary entry
git add diary/2026/05/2026-05-04.md
git commit -m "Test entry"

# If validation fails, you'll see:
# ❌ Commit blocked: Some entries have validation errors.
```

### What It Does

```
On git commit:
  1. Check staged files for diary entries
  2. Run entry_review.py on each staged entry
  3. If errors found → BLOCK commit
  4. If only warnings → ALLOW commit (with message)
  5. If clean → ALLOW commit
```

### Bypass (Emergency Only)

```bash
git commit --no-verify -m "Emergency commit, skipping validation"
```

---

## ⏰ Option 3: Cron Jobs (Self-Hosted)

### Setup

Create a cron job on your server:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 23:00 PKT = 18:00 UTC)
0 18 * * * cd /path/to/diaryjournal && /usr/bin/python3 scripts/run_daily.py --date $(TZ='Asia/Karachi' date +\%Y-\%m-\%d) --force >> logs/daily.log 2>&1
```

### With Validation

```bash
# Run with validation and strict mode
0 18 * * * cd /path/to/diaryjournal && \
  /usr/bin/python3 scripts/run_daily.py --date $(TZ='Asia/Karachi' date +\%Y-\%m-\%d) --force --strict-validation >> logs/daily.log 2>&1
```

### Logging

```bash
# Create log directory
mkdir -p logs

# View logs
tail -f logs/daily.log
```

---

## 🔧 Option 4: Integrated Pipeline (run_daily.py)

### Basic Usage

```bash
# Run full pipeline for today
python3 scripts/run_daily.py --force

# Run for specific date
python3 scripts/run_daily.py --date 2026-05-05 --force

# Dry run (no API calls)
python3 scripts/run_daily.py --date 2026-05-05 --dry-run --force

# Skip validation
python3 scripts/run_daily.py --force --skip-validation

# Strict validation (fail on warnings)
python3 scripts/run_daily.py --force --strict-validation
```

### Integration with Cron

```bash
#!/bin/bash
# daily.sh
cd /Users/dan/Desktop/diaryjournal
DATE=$(TZ='Asia/Karachi' date +%Y-%m-%d)
echo "[$(date)] Running pipeline for $DATE"
python3 scripts/run_daily.py --date "$DATE" --force --strict-validation
echo "[$(date)] Pipeline completed with exit code $?"
```

---

## 📊 Validation in Automation

### Severity Levels in Automation

| Level | GitHub Actions | Pre-commit | Cron |
|-------|---------------|------------|------|
| **ERROR** | ❌ Blocks commit, fails workflow | ❌ Blocks commit | ❌ Non-zero exit code |
| **WARNING** | ⚠️ Continues (unless strict) | ✅ Allows commit | ⚠️ Continues (unless strict) |
| **INFO** | ℹ️ Logged only | ℹ️ Logged only | ℹ️ Logged only |

### JSON Output for Metrics

```bash
# Generate JSON report for tracking
python3 scripts/entry_review.py diary/2026/05/ --batch --json > reports/$(date +%Y-%m-%d).json

# Track validation trends over time
# (You could build a dashboard from these JSON files)
```

---

## 🔍 Monitoring & Alerts

### GitHub Actions Notifications

- ✅ Failed workflows send email/Slack notifications automatically
- ✅ Success notifications can be configured
- ✅ Artifacts (validation reports) retained for 30-90 days

### Custom Alerts (Example)

Add to `.github/workflows/daily-pipeline.yml`:

```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: "Daily pipeline failed for ${{ steps.date.outputs.date }}"
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Log Monitoring (Cron)

```bash
# Check for errors in logs
grep -i "error\|failed\|❌" logs/daily.log | mail -s "Diary Pipeline Errors" you@example.com
```

---

## 🧪 Testing Automation

### Test GitHub Actions Locally

Use `act` to test workflows locally:

```bash
# Install act
brew install act

# Test the workflow
act -W .github/workflows/daily-pipeline.yml
```

### Test Pre-commit Hook

```bash
# Create a test entry with errors
echo "# Bad Entry" > diary/2026/05/test.md

# Try to commit
git add diary/2026/05/test.md
git commit -m "Test"

# Should be blocked
```

### Test Cron Job

```bash
# Run once manually
cd /Users/dan/Desktop/diaryjournal
/usr/bin/python3 scripts/run_daily.py --date 2026-05-05 --force
echo "Exit code: $?"
```

---

## 📋 Checklist: Choose Your Setup

### For Local Development Only
- [ ] Install pre-commit hook: `git config core.hooksPath .git-hooks`
- [ ] Test with a sample commit

### For Production (GitHub)
- [ ] Add API keys to GitHub Secrets
- [ ] Verify `.github/workflows/daily-pipeline.yml` is present
- [ ] Push to main/master to trigger workflow
- [ ] Check `Actions` tab for first run

### For Self-Hosted Server
- [ ] Set up cron job: `crontab -e`
- [ ] Create `logs/` directory
- [ ] Test manual run
- [ ] Set up monitoring/alerts

### For Team Collaboration
- [ ] Document which automation is active
- [ ] Share GitHub Secrets with team (if applicable)
- [ ] Agree on validation strictness (strict vs. non-strict)
- [ ] Set up shared notifications (Slack/email)

---

## 🎯 Recommended Setup (Best of All)

### Development Machine
```bash
# 1. Pre-commit hook for fast feedback
git config core.hooksPath .git-hooks

# 2. Manual testing
python3 scripts/run_daily.py --date 2026-05-05 --force --strict-validation
```

### Production (GitHub)
```yaml
# Automatic daily generation at 23:00 PKT
# With validation, auto-commit, and failure notifications
# (Already configured in .github/workflows/daily-pipeline.yml)
```

### Backup (Optional Cron)
```bash
# In case GitHub Actions is down
0 19 * * * cd /path/to/diaryjournal && python3 scripts/run_daily.py --force
```

---

## 💡 Tips & Tricks

### Skip Validation Temporarily
```bash
# For quick prototypes
python3 scripts/run_daily.py --force --skip-validation

# For commits (not recommended)
git commit --no-verify
```

### Run Validation Only
```bash
# After manual edits
python3 scripts/entry_review.py diary/2026/05/2026-05-05.md --strict
```

### Debug API Issues
```bash
# Test API connection
python3 -c "import openai; print('OpenAI OK')"
python3 -c "import google.generativeai; print('Gemini OK')"
```

### View GitHub Actions Logs
1. Go to `Actions` tab
2. Click on workflow run
3. Click on job (e.g., `generate-entry`)
4. Expand steps to see output

---

## 🔗 Related Documentation

- **Validation System**: `docs/validation-guide.md`
- **Scripts README**: `scripts/README.md`
- **Implementation Summary**: `VALIDATION_SYSTEM.md`
- **Quick Reference**: `VALIDATION_READY.md`

---

## ❓ FAQ

**Q: Which automation should I use?**
A: Start with GitHub Actions if you're on GitHub. Add pre-commit hooks for local development.

**Q: Can I use multiple automations?**
A: Yes! They complement each other. Pre-commit catches issues early, GitHub Actions handles daily runs.

**Q: What if validation fails in GitHub Actions?**
A: You'll get a notification. Check the `Actions` tab for details. Fix the entry and push again.

**Q: How do I disable automation temporarily?**
A: 
- GitHub Actions: Go to `Actions` → workflow → `Disable workflow`
- Pre-commit: `git commit --no-verify`
- Cron: Comment out the line in `crontab -e`

**Q: Can I customize the schedule?**
A: Yes! Edit the `cron:` line in `.github/workflows/daily-pipeline.yml` or the cron expression in `crontab`.

---

## 🎉 You're Automated!

Your Witness diary pipeline now has:
- ✅ Daily automated generation
- ✅ Validation at every step
- ✅ Multiple fallback options
- ✅ Monitoring and alerts
- ✅ Comprehensive documentation

**Next step**: Push to GitHub and watch the first automated entry generate!
