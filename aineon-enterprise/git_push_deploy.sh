#!/bin/bash
# AINEON Engine - GitHub Push & Render Deploy Script
# This script prepares and deploys the AINEON Flash Loan Engine to GitHub and Render

set -e  # Exit on any error

echo "🚀 AINEON Flash Loan Engine - GitHub Push & Deploy Script"
echo "=========================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.env.local
.env.production

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Data files
data/
*.csv
*.json

# Model files
models/
*.pkl
*.joblib

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
tmp/
temp/
EOF
fi

# Add all files
echo "📦 Adding files to git..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "⚠️  No changes to commit"
else
    # Commit changes
    echo "💾 Committing changes..."
    git commit -m "Production deployment: AINEON Flash Loan Engine with Render configuration"
fi

# Set main branch if not already set
if ! git rev-parse --abbrev-ref HEAD | grep -q "main"; then
    echo "🌿 Creating main branch..."
    git branch -M main
fi

# Add remote origin if not exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "🔗 Adding GitHub remote..."
    read -p "Enter your GitHub username (for repository TemamAb/myneon): " username
    git remote add origin https://github.com/${username}/myneon.git
    echo "✅ Remote added: https://github.com/${username}/myneon.git"
else
    echo "✅ Remote already exists"
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
if git push -u origin main; then
    echo "✅ Successfully pushed to GitHub!"
else
    echo "❌ Failed to push to GitHub"
    echo "💡 Make sure you have access to the repository and the correct remote URL"
    exit 1
fi

echo ""
echo "🎉 GitHub deployment complete!"
echo ""
echo "Next steps:"
echo "1. 🌐 Go to https://render.com"
echo "2. 🔗 Connect your GitHub account"
echo "3. 📦 Deploy from the 'myneon' repository"
echo "4. ⚙️  Configure environment variables (see DEPLOYMENT_GUIDE.md)"
echo ""
echo "📚 For detailed instructions, see: DEPLOYMENT_GUIDE.md"
echo ""
echo "🔧 Your local engine continues running on current ports"
echo "   - Main engine: Current terminals (unaffected)"
echo "   - Production API: Available at http://localhost:8000 (when started)"
echo "   - Production Dashboard: Available at http://localhost:8501 (when started)"
echo ""
echo "⚡ AINEON Flash Loan Engine ready for cloud deployment!"