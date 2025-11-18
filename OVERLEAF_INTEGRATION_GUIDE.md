# Overleaf Integration Options

## Available Integration Methods

### 1. 🎯 Git Bridge (Premium Feature) - BEST OPTION

**Requirements:** Overleaf Premium/Pro account (often free via university)

**How it works:**
```bash
# One-time setup
./overleaf_git_setup.sh

# Daily workflow
./overleaf_git_workflow.sh push   # Send changes to Overleaf
./overleaf_git_workflow.sh pull   # Get changes from Overleaf
./overleaf_git_workflow.sh sync   # Two-way sync
```

**Advantages:**
- ✅ True version control integration
- ✅ Bidirectional sync
- ✅ Conflict resolution via Git
- ✅ Automated workflow possible

**Check if you have it:**
1. Log into Overleaf
2. Open any project
3. Look for "Menu" → "Sync" → "Git"
4. If present, you have Git access!

### 2. 📦 Manual Upload/Download (Free) - CURRENT METHOD

**How it works:**
```bash
# Upload to Overleaf
./prepare_for_overleaf.sh
# → Upload overleaf_package.zip

# Download from Overleaf
# Menu → Download → Source
./sync_from_overleaf.sh
```

**Advantages:**
- ✅ Works with free accounts
- ✅ Simple to understand
- ✅ No special setup needed

**Disadvantages:**
- ❌ Manual process
- ❌ No automatic conflict detection
- ❌ Harder to track changes

### 3. 🔗 GitHub Integration (Premium)

Overleaf can sync with GitHub repositories directly.

**Setup:**
1. In Overleaf: Menu → Sync → GitHub
2. Link your GitHub account
3. Select repository

**How it works:**
- Overleaf pulls from GitHub
- You push changes to GitHub from local
- Overleaf auto-syncs (or manual trigger)

**Workflow:**
```bash
# Local changes
git push origin master

# In Overleaf
Menu → Sync → Pull from GitHub

# After Overleaf edits
Menu → Sync → Push to GitHub
git pull origin master
```

### 4. 🛠️ Third-Party Tools

#### Overleaf-sync (Python)
```bash
pip install overleaf-sync

# Download
ols download PROJECT_ID

# Upload
ols upload PROJECT_ID
```

**Note:** Requires storing credentials

#### Git-bridge-client
Open source alternative to official Git bridge:
https://github.com/weilueluo/overleaf-sync

### 5. 📨 Dropbox Sync (Legacy)

**Note:** Being phased out by Overleaf

If your institution still has it:
1. Link Dropbox in Overleaf settings
2. Projects sync to Dropbox folder
3. Edit locally via Dropbox

## Comparison Table

| Method | Cost | Two-way | Auto | Difficulty |
|--------|------|---------|------|------------|
| Git Bridge | Premium | ✅ | ✅ | Medium |
| GitHub Sync | Premium | ✅ | ✅ | Easy |
| Manual Upload | Free | ✅ | ❌ | Easy |
| overleaf-sync | Free | ✅ | ⚠️ | Medium |
| Dropbox | Varies | ✅ | ✅ | Easy |

## Recommended Approach

### If you have Premium (check with your university!)
1. Use **Git Bridge** for full control
2. Run `./overleaf_git_setup.sh` once
3. Use `./overleaf_git_workflow.sh` for daily work

### If you have Free account
1. Use the **manual workflow** we set up
2. Run `./prepare_for_overleaf.sh` to upload
3. Run `./sync_from_overleaf.sh` to download

## API Access

Overleaf has limited API access:

### Official API (Very Limited)
- Only for enterprise/institutional accounts
- Mainly for user management
- Not for project manipulation

### Unofficial Methods

**Cookie-based automation:**
```python
# Using browser automation (Selenium)
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://overleaf.com/login")
# ... login and download via browser automation
```

**REST endpoints (undocumented):**
```bash
# Some endpoints exist but are unofficial
curl -X GET "https://www.overleaf.com/project/PROJECT_ID/download/zip" \
  -H "Cookie: your-session-cookie"
```

⚠️ **Warning:** Unofficial methods may break without notice

## GitHub Actions Integration

For automated workflows, create `.github/workflows/overleaf-sync.yml`:

```yaml
name: Sync with Overleaf

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    if: secrets.OVERLEAF_EMAIL != ''

    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install pandas numpy matplotlib
        # ... other dependencies

    - name: Generate figures
      run: |
        python scripts/generate_all_figures.py

    - name: Sync to Overleaf
      env:
        OVERLEAF_EMAIL: ${{ secrets.OVERLEAF_EMAIL }}
        OVERLEAF_PASSWORD: ${{ secrets.OVERLEAF_PASSWORD }}
      run: |
        # Use git bridge or overleaf-sync
        git push overleaf master
```

## Tips for Collaboration

### 1. Communication Protocol
```markdown
# In paper.tex comments
% TODO(advisor): Please review this section
% CHANGED(student): Updated based on your feedback
% QUESTION(advisor): Should we include X?
```

### 2. Version Tags
```bash
# Before major editing session
git tag -a "v1.0-pre-advisor-review" -m "Version before advisor review"

# After incorporating feedback
git tag -a "v1.1-post-advisor-review" -m "Incorporated advisor feedback"
```

### 3. Branch Strategy
```
master          - Complete project (code + paper)
overleaf-sync   - Paper files only for Overleaf
advisor-edits   - Temporary branch for major revisions
```

## Troubleshooting

### "Merge conflicts" in Overleaf
1. Download both versions
2. Use diff tool: `diff -u overleaf/paper.tex local/paper.tex`
3. Manually merge
4. Re-upload

### "Project too large" error
1. Ensure no data files in upload
2. Check figure sizes (convert to PDF, compress)
3. Remove auxiliary files (.aux, .log)

### Git bridge authentication fails
1. Check if using correct email
2. Try generating app-specific password
3. Ensure Premium account is active

### Sync gets out of sync
1. Create checkpoint: `git tag checkpoint-$(date +%Y%m%d)`
2. Force push clean version: `git push --force overleaf master`
3. Re-download from Overleaf to verify

## Quick Decision Tree

```
Do you have Overleaf Premium?
├─ YES → Use Git Bridge (best option)
│   └─ Run: ./overleaf_git_setup.sh
└─ NO →
    ├─ Is project on GitHub?
    │   ├─ YES → Ask advisor to connect Overleaf to GitHub
    │   └─ NO → Use manual workflow
    │       └─ Run: ./prepare_for_overleaf.sh
    └─ Need automation?
        ├─ YES → Consider overleaf-sync tool
        └─ NO → Stick with manual (most reliable)
```

## Summary

**For most users:** The manual workflow (`prepare_for_overleaf.sh` / `sync_from_overleaf.sh`) is sufficient and reliable.

**For power users with Premium:** Git bridge provides the best integration.

**Key insight:** Tables/figures are generated locally, text editing happens on Overleaf. This separation makes any integration method work.