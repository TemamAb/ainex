#!/bin/bash

echo "=== AINEX Change Creation & GitHub Push Script ==="

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check git status
echo "Checking git status..."
if git diff --quiet && git diff --staged --quiet; then
    echo "❌ No changes to commit. Please make some changes first."
    echo "Current status:"
    git status --porcelain
    exit 1
fi

echo "✅ Changes detected"

# Show current status
echo ""
echo "Current git status:"
git status --short

# Add all changes
echo ""
echo "Staging all changes..."
git add -A

# Get a commit message from user or use default
if [ -z "$1" ]; then
    echo ""
    echo "Enter commit message (or press Enter for default):"
    read -r commit_message
    if [ -z "$commit_message" ]; then
        commit_message="feat: update AINEX dashboard and services

- Updated dashboard components and services
- Improved real-time profit generation
- Enhanced blockchain integration
- Fixed TypeScript compilation issues"
    fi
else
    commit_message="$1"
fi

# Commit changes
echo ""
echo "Committing changes..."
if git commit -m "$commit_message"; then
    echo "✅ Changes committed successfully"
else
    echo "❌ Commit failed"
    exit 1
fi

# Push to GitHub
echo ""
echo "Pushing to GitHub..."
if git push origin main 2>/dev/null; then
    echo "✅ Successfully pushed to GitHub main branch"
elif git push origin master 2>/dev/null; then
    echo "✅ Successfully pushed to GitHub master branch"
else
    echo "❌ Push failed. You may need to:"
    echo "   1. Set up your GitHub remote: git remote add origin <your-repo-url>"
    echo "   2. Create and switch to main branch: git checkout -b main"
    echo "   3. Or push with upstream: git push -u origin main"
    exit 1
fi

# Show the commit hash
echo ""
echo "Latest commit hash:"
git log --oneline -1

echo ""
echo "🎉 Change creation and push completed successfully!"
echo "Your changes are now live on GitHub."
