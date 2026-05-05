# GitHub Pages Deployment Guide

## Overview
Your diary is now configured to automatically deploy to GitHub Pages whenever changes are pushed to the `main` branch.

## Deployment Setup Complete ✅

The following files have been created/updated:

### 1. **GitHub Pages Workflow** (`.github/workflows/deploy-pages.yml`)
- Automatically triggers on push to `main`
- Builds frontend assets
- Generates sitemap and RSS feeds
- Deploys to GitHub Pages

### 2. **Jekyll Configuration** (`_config.yml`)
- Sets up proper URL structure for GitHub Pages
- Configures diary entries as a collection

### 3. **No Jekyll Flag** (`.nojekyll`)
- Ensures GitHub Pages serves static files without Jekyll processing
- Allows for custom directory structure

### 4. **Robots.txt** (Updated)
- Configured for GitHub Pages URL
- Points search engines to sitemap

## Step-by-Step: Enable GitHub Pages

### Step 1: Push Changes
Push all the new files to your repository:
```bash
cd /Users/dan/Desktop/diaryjournal
git add .github/workflows/deploy-pages.yml _config.yml .nojekyll robots.txt
git commit -m "Setup GitHub Pages deployment"
git push origin main
```

### Step 2: Enable GitHub Pages in Repository Settings
1. Go to your GitHub repository: https://github.com/aishadanny007-design/thewitness
2. Click **Settings** (top right)
3. Scroll to **Pages** section in the left sidebar
4. Under "Source", select:
   - **Deploy from a branch**
   - Branch: **main**
   - Folder: **/ (root)**
5. Click **Save**

### Step 3: Wait for Deployment
- GitHub Pages will automatically build and deploy from the deploy-pages.yml workflow
- Check the **Actions** tab to see the deployment progress
- Your site will be available at: `https://aishadanny007-design.github.io/thewitness`

## How It Works

### Automatic Deployment Pipeline:
1. **Daily Pipeline** (`daily.yml`): Generates new diary entries via AI
2. **Commit**: Automatically commits generated entries to main branch
3. **GitHub Pages Workflow** (triggered): 
   - Checks out code
   - Runs build scripts
   - Generates sitemap & RSS
   - Deploys to GitHub Pages

### What Gets Deployed:
- `index.html` - Main landing page
- `app.js` - Frontend JavaScript
- `styles.css` - Styling
- `public/entries.json` - Entry manifest
- `diary/` - All diary entries (markdown)
- `assets/` - Brand assets

## Verification Checklist

After enabling GitHub Pages, verify:

- [ ] Navigate to `https://aishadanny007-design.github.io/thewitness`
- [ ] Landing page loads correctly
- [ ] Diary entries are visible
- [ ] Check browser console for errors (F12)
- [ ] View page source to confirm SEO metadata is present

## URLs & Resources

**GitHub Pages Site**: https://aishadanny007-design.github.io/thewitness

**Diary Entries**: Dynamically loaded from `public/entries.json`

**Sitemap**: Generated at `/sitemap.xml`

**RSS Feed**: Available at `/feed.xml` (when generated)

## DNS Setup (Optional)

If you want to use a custom domain like `thewitness.ai`:

1. Go to **Settings > Pages**
2. Under "Custom domain", enter your domain
3. Update your domain's DNS records to point to GitHub Pages
4. GitHub will provide specific instructions

## Troubleshooting

### Deployment Shows Yellow/Red ❌
- Check the **Actions** tab for error details
- Common issues:
  - Build scripts missing or failing
  - Incorrect file permissions
  - Missing dependencies

### Site Not Loading
- Verify GitHub Pages is enabled in Settings
- Check that `.nojekyll` file exists
- Clear browser cache (Ctrl+Shift+Delete)

### Changes Not Appearing
- Ensure commits are pushed to `main` branch
- Wait ~30 seconds for GitHub Pages to rebuild
- Check Actions tab for successful deployment

## Next Steps

1. **Monitor deployments** in the Actions tab
2. **Set up domain** if desired
3. **Configure analytics** (Google Analytics, Plausible, etc.)
4. **Enable HTTPS** (automatic with GitHub Pages)
5. **Monitor SEO** with Google Search Console

## Files Reference

```
.github/workflows/
├── daily.yml              # Daily entry generation
├── daily-pipeline.yml     # Alternative pipeline
└── deploy-pages.yml       # GitHub Pages deployment ← NEW

Root Files:
├── _config.yml            # Jekyll/GitHub Pages config ← NEW
├── .nojekyll              # Disable Jekyll processing ← NEW
├── robots.txt             # SEO & sitemap reference ← UPDATED
├── index.html             # Landing page
├── app.js                 # Frontend logic
├── styles.css             # Styling
└── public/entries.json    # Entry manifest
```

---

**Status**: ✅ Ready to Deploy

Your diary is now configured for automatic deployment to GitHub Pages!
