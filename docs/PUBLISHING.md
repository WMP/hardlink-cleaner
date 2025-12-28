# Publishing to GitHub Checklist

## Before Publishing

- [x] Create `pyproject.toml` with metadata
- [x] Create README.md with examples
- [x] Create LICENSE file
- [x] Create .gitignore
- [x] Rename script to `hardlink_cleaner.py` (underscores)
- [x] Add `main_entry()` function
- [x] Test package builds (`python3 -m build`)

## Steps to Publish

### 1. Update pyproject.toml

Replace placeholders in `pyproject.toml`:
```toml
authors = [{name = "Your Name", email = "your.email@example.com"}]
```

Update URLs:
```toml
[project.urls]
Homepage = "https://github.com/YOURUSERNAME/hardlink-cleaner"
Repository = "https://github.com/YOURUSERNAME/hardlink-cleaner"
Issues = "https://github.com/YOURUSERNAME/hardlink-cleaner/issues"
```

### 2. Create GitHub Repository

```bash
# Go to https://github.com/new
# Repository name: hardlink-cleaner
# Description: Interactive TUI tool for finding and cleaning hardlinked files
# Public
# Don't initialize with README (already have one)
```

### 3. Push to GitHub

```bash
# Add remote (replace YOURUSERNAME)
git remote add origin https://github.com/YOURUSERNAME/hardlink-cleaner.git

# Push
git add .
git commit -m "Initial release v1.0.0"
git branch -M main
git push -u origin main
```

### 4. Create Release Tag

```bash
# Create tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 5. Create GitHub Release

1. Go to repository on GitHub
2. Click "Releases" → "Create a new release"
3. Choose tag: `v1.0.0`
4. Release title: `v1.0.0 - Initial Release`
5. Description:
```markdown
## 🎉 Initial Release

Interactive TUI tool for finding and cleaning hardlinked files to reclaim disk space.

### Features
- Interactive ncdu-style file browser
- Hardlink-aware size calculation
- Multiple cleanup modes
- Safe by default (dry-run, confirmations)
- Save/load scan results

### Installation
```bash
pipx install hardlink-cleaner
```

See [README.md](https://github.com/YOURUSERNAME/hardlink-cleaner/blob/main/README.md) for full documentation.
```
6. Attach files (optional): Upload `dist/*.whl` and `dist/*.tar.gz`
7. Click "Publish release"

### 6. Add Topics to Repository

On GitHub repository page:
- Click ⚙️ next to "About"
- Add topics: `python`, `tui`, `hardlink`, `disk-space`, `filesystem`, `cleanup`, `ncurses`, `storage`

### 7. Record asciinema Demo

```bash
# Install asciinema
sudo apt install asciinema
# or
pipx install asciinema

# Run demo
asciinema rec --idle-time-limit 2 -t "Hardlink Cleaner Demo" demo.cast

# Run the demo script
./demo.sh

# Stop recording: Ctrl+D

# Upload (optional)
asciinema upload demo.cast
```

Add to README.md:
```markdown
## 🎬 Demo

[![asciicast](https://asciinema.org/a/YOUR_CAST_ID.svg)](https://asciinema.org/a/YOUR_CAST_ID)
```

### 8. Optional: Publish to PyPI

See [INSTALL.md](INSTALL.md) for PyPI publishing instructions.

```bash
# Install twine
pip install twine

# Build
python3 -m build

# Upload to PyPI
python3 -m twine upload dist/*
```

Then users can install with:
```bash
pipx install hardlink-cleaner
```

### 9. Add Badges to README

Add at the top of README.md:

```markdown
[![PyPI version](https://badge.fury.io/py/hardlink-cleaner.svg)](https://badge.fury.io/py/hardlink-cleaner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
```

## Post-Publishing

### Share on Social Media / Communities

- Reddit: r/Python, r/commandline, r/linux
- Hacker News: news.ycombinator.com
- Twitter/X with hashtags: #Python #CLI #TUI
- Dev.to article

### Monitor

- Watch GitHub repository for issues/PRs
- Star your own repo (optional 😄)
- Add GitHub Actions for CI/CD (optional)

## Future Updates

### Version Bump Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md (if exists)
3. Commit changes
4. Create new tag: `git tag -a v1.0.1 -m "Release v1.0.1"`
5. Push: `git push && git push --tags`
6. Create GitHub release
7. Rebuild and upload to PyPI

## Quick Reference

```bash
# Build package
python3 -m build

# Test install locally
pip install dist/hardlink_cleaner-1.0.0-py3-none-any.whl

# Upload to PyPI
python3 -m twine upload dist/*

# Create and push tag
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```
