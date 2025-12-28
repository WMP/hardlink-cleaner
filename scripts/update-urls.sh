#!/bin/bash
# Quick script to update GitHub username and author info

set -e

echo "========================================="
echo "Hardlink Cleaner - Update Configuration"
echo "========================================="
echo ""

# Get current values
CURRENT_USER=$(grep -m1 "yourusername" README.md 2>/dev/null | grep -o "yourusername" || echo "yourusername")
CURRENT_NAME=$(grep -m1 "Your Name" pyproject.toml 2>/dev/null | sed 's/.*name = "\([^"]*\)".*/\1/' || echo "Your Name")
CURRENT_EMAIL=$(grep -m1 "your.email@example.com" pyproject.toml 2>/dev/null | sed 's/.*email = "\([^"]*\)".*/\1/' || echo "your.email@example.com")

echo "Current configuration:"
echo "  GitHub username: $CURRENT_USER"
echo "  Author name: $CURRENT_NAME"
echo "  Author email: $CURRENT_EMAIL"
echo ""

# Ask for new values
read -p "Enter your GitHub username: " GITHUB_USER
if [ -z "$GITHUB_USER" ]; then
    echo "Error: GitHub username cannot be empty"
    exit 1
fi

read -p "Enter your full name: " AUTHOR_NAME
if [ -z "$AUTHOR_NAME" ]; then
    echo "Error: Author name cannot be empty"
    exit 1
fi

read -p "Enter your email: " AUTHOR_EMAIL
if [ -z "$AUTHOR_EMAIL" ]; then
    echo "Error: Email cannot be empty"
    exit 1
fi

echo ""
echo "New configuration:"
echo "  GitHub username: $GITHUB_USER"
echo "  Author name: $AUTHOR_NAME"
echo "  Author email: $AUTHOR_EMAIL"
echo ""
read -p "Update files with this configuration? [y/N]: " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Updating files..."

# Backup
BACKUP_DIR=".backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp pyproject.toml "$BACKUP_DIR/"
cp README.md "$BACKUP_DIR/"
cp CHANGELOG.md "$BACKUP_DIR/"
echo "  Backup created in $BACKUP_DIR/"

# Update GitHub username in all markdown files
echo "  Updating GitHub username..."
find . -maxdepth 1 -name "*.md" -type f -exec sed -i "s/yourusername/$GITHUB_USER/g" {} \;

# Update pyproject.toml
echo "  Updating pyproject.toml..."
sed -i "s|https://github.com/yourusername/|https://github.com/$GITHUB_USER/|g" pyproject.toml
sed -i "s/Your Name/$AUTHOR_NAME/g" pyproject.toml
sed -i "s/your.email@example.com/$AUTHOR_EMAIL/g" pyproject.toml

# Update CHANGELOG.md
echo "  Updating CHANGELOG.md..."
sed -i "s|https://github.com/yourusername/|https://github.com/$GITHUB_USER/|g" CHANGELOG.md

echo ""
echo "✓ Update complete!"
echo ""
echo "Updated files:"
echo "  - pyproject.toml"
echo "  - *.md files"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Rebuild package: python3 -m build"
echo "  3. Commit changes: git add . && git commit -m 'Update author and repository info'"
echo ""
echo "To restore from backup:"
echo "  cp $BACKUP_DIR/* ."
echo ""
