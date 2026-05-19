# 🚀 Automation Setup Complete!

## What Was Set Up

I've created a **complete automation system** for The Witness with multiple options to fit your workflow.

---

## 📦 Deliverables

### **GitHub Actions Workflow**
- **File**: `.github/workflows/daily-pipeline.yml`
- **What it does**:
  - Runs daily at 23:00 PKT (18:00 UTC)
  - Collects sources → Generates entry → Validates
  - Commits and pushes automatically
  - Uploads validation reports as artifacts
  - Notifies on failure

### **Pre-commit Hook**
- **File**: `.git-hooks/pre-commit`
- **What it does**:
  - Validates staged diary entries before commit
  - Blocks commits with validation errors
  - Provides fast feedback during development

### **Updated run_daily.py**
- **New flags**:
  - `--skip-validation`: Skip validation step
  - `--strict-validation`: Treat warnings as failures
- **Integrated validation**: Runs automatically after generation

### **Documentation**
- **`docs/automation-guide.md`** (300+ lines)
  - Complete automation guide
  - GitHub Actions setup
  - Pre-commit hook setup
  - Cron job alternative
  - Monitoring and alerts
  - Testing instructions

### **Dependencies**
- **`requirements.txt`**: Python package list for automation

---

## 🚀 Quick Start

### Option 1: GitHub Actions (Recommended)

1. **Add Secrets to GitHub**:
   - Go to `Settings` → `Secrets and variables` → `Actions`
   - Add: `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`)
   - Optional: `OPENROUTER_MODEL`, `OPENAI_MODEL`, `AI_PROVIDER`

2. **Push to Main**:
   ```bash
   git add .
   git commit -m "Add automation"
   git push origin main
   ```

3. **Watch it run**:
   - Go to `Actions` tab
   - See `The Witness - Daily Pipeline` running
   - First run will generate today's entry!

### Option 2: Pre-commit Hook (Local)

```bash
cd /Users/dan/Desktop/diaryjournal
git config core.hooksPath .git-hooks

# Test it
git add diary/2026/05/2026-05-04.md
git commit -m "Test validation"
# Should pass (only warnings) or block (if errors)
```

### Option 3: Manual with Validation

```bash
# Run full pipeline with validation
python3 scripts/run_daily.py --force --strict-validation

# Skip validation if needed
python3 scripts/run_daily.py --force --skip-validation
```

---

## 📊 What Happens Daily (GitHub Actions)

```
23:00 PKT (18:00 UTC):
  ↓
1. Checkout repository
  ↓
2. Set up Python 3.11
  ↓
3. Install dependencies (requirements.txt)
  ↓
4. Determine today's date (Asia/Karachi timezone)
  ↓
5. Run collect_sources.py
  ↓
6. Run generate_entry.py
  ↓
7. Validate entry (non-strict, continues on warnings)
  ↓
8. Validate with strict mode (blocks on errors)
  ↓
9. Generate JSON validation report
  ↓
10. Commit and push changes
  ↓
11. Upload validation report (30-day retention)
  ↓
12. Notify on failure (GitHub notification)
```

---

## 🔍 Monitoring

### GitHub Actions
- **View runs**: `Actions` tab → `The Witness - Daily Pipeline`
- **View logs**: Click on workflow run → Click job → Expand steps
- **Download reports**: Click on run → Artifacts → `validation-report-YYYY-MM-DD`

### Pre-commit Hook
- **See output**: Shown in terminal when you `git commit`
- **Bypass**: `git commit --no-verify` (emergency only)

### Cron (if used)
- **View logs**: `tail -f logs/daily.log`
- **Check exit codes**: `echo $?` after manual run

---

## 🎯 Validation in Automation

### Severity Levels

| Level | GitHub Actions | Pre-commit | Cron |
|-------|---------------|------------|------|
| **ERROR** | ❌ Fails workflow | ❌ Blocks commit | ❌ Non-zero exit |
| **WARNING** | ⚠️ Continues (unless strict) | ✅ Allows commit | ⚠️ Continues (unless strict) |
| **INFO** | ℹ️ Logged only | ℹ️ Logged only | ℹ️ Logged only |

### JSON Reports

Every run generates a JSON report:
```json
{
  "file": "diary/2026/05/2026-05-04.md",
  "valid": true,
  "issues": [...]
}
```

---

## 🛠️ Customization

### Change Schedule (GitHub Actions)

Edit `.github/workflows/daily-pipeline.yml`:
```yaml
schedule:
  - cron: '0 18 * * *'  # 18:00 UTC = 23:00 PKT
```

### Change Validation Strictness

**In GitHub Actions**:
```yaml
- name: Validate with strict mode
  run: |
    python scripts/entry_review.py ... --strict  # Add --strict here
```

**In run_daily.py**:
```bash
python3 scripts/run_daily.py --force --strict-validation
```

**In Pre-commit Hook**:
Edit `.git-hooks/pre-commit` and add `--strict` to the validation command.

---

## 🧪 Testing

### Test GitHub Actions Locally

```bash
# Install act (https://github.com/nektos/act)
brew install act

# Test the workflow
act -W .github/workflows/daily-pipeline.yml
```

### Test Pre-commit Hook

```bash
# Create a bad entry
echo "# Bad Entry" > diary/2026/05/test.md

# Try to commit (should be blocked)
git add diary/2026/05/test.md
git commit -m "Test"

# Clean up
rm diary/2026/05/test.md
```

### Test Manual Run

```bash
# Dry run (no API calls)
python3 scripts/run_daily.py --date 2026-05-05 --dry-run --force

# Real run with validation
python3 scripts/run_daily.py --date 2026-05-05 --force --strict-validation
```

---

## 📋 Checklist

### For GitHub Actions
- [ ] Add API keys to GitHub Secrets
- [ ] Verify `.github/workflows/daily-pipeline.yml` is present
- [ ] Push to main/master to trigger first run
- [ ] Check `Actions` tab for successful run
- [ ] Verify entry was committed to repo

### For Pre-commit Hook
- [ ] Run: `git config core.hooksPath .git-hooks`
- [ ] Test with a sample commit
- [ ] Verify it blocks bad entries

### For Local Development
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Test manual run: `python3 scripts/run_daily.py --force`
- [ ] Test validation: `python3 scripts/entry_review.py diary/2026/05/2026-05-04.md`

---

## 🔗 Related Files

| File | Purpose |
|------|---------|
| `.github/workflows/daily-pipeline.yml` | GitHub Actions workflow |
| `.git-hooks/pre-commit` | Pre-commit hook |
| `scripts/run_daily.py` | Updated with validation flags |
| `docs/automation-guide.md` | Complete automation guide |
| `requirements.txt` | Python dependencies |
| `README.md` | Updated with automation info |

---

## 💡 Tips

### For Teams
- Share GitHub Secrets with team members who need to trigger workflows
- Document which automation is active (GitHub Actions vs. cron)
- Use `--strict-validation` for production, `--skip-validation` for prototyping

### For Debugging
- **GitHub Actions**: Check `Actions` tab → Click run → Expand failed step
- **Pre-commit**: Run `git commit` without `--no-verify` to see output
- **Manual**: Add `--verbose` or check terminal output

### For Monitoring
- Set up Slack/email notifications for failed workflows
- Periodically check validation reports (artifacts)
- Monitor cron logs if using that option

---

## ❓ FAQ

**Q: Which automation should I use?**
A: Start with GitHub Actions if you're on GitHub. Add pre-commit hooks for local development.

**Q: Can I use multiple automations?**
A: Yes! They complement each other. Pre-commit catches issues early, GitHub Actions handles daily runs.

**Q: What if the API key expires?**
A: GitHub Actions will fail. Update the secret in `Settings` → `Secrets and variables` → `Actions`.

**Q: How do I disable automation temporarily?**
A: 
- GitHub Actions: Go to `Actions` → Workflow → `Disable workflow`
- Pre-commit: `git commit --no-verify`
- Cron: Comment out the line in `crontab -e`

**Q: Can I customize the schedule?**
A: Yes! Edit the `cron:` line in the workflow file or the cron expression in `crontab`.

---

## ✅ You're Automated!

Your Witness diary pipeline now has:
- ✅ Daily automated generation (GitHub Actions)
- ✅ Validation at every step
- ✅ Pre-commit hooks for local development
- ✅ Multiple fallback options
- ✅ Monitoring and alerts
- ✅ Comprehensive documentation

**Next step**: Push to GitHub and watch the first automated entry generate!

```bash
git add .
git commit -m "Add complete automation system"
git push origin main
```

Then check the `Actions` tab to see it in action! 🎉
