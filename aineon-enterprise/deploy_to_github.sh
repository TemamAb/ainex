#!/bin/bash
# AINEON Flash Loan Engine - GitHub Deployment Script
# This script prepares and deploys the Flash Loan Engine to Render via GitHub

set -e  # Exit on any error

echo "🚀 AINEON Flash Loan Engine - GitHub Deployment Script"
echo "======================================================"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this script from the root of your git repository"
    exit 1
fi

# Check if GitHub remote exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "❌ Error: No GitHub remote found"
    echo "Please ensure your repository is connected to GitHub"
    exit 1
fi

# Get GitHub repository URL
GITHUB_URL=$(git remote get-url origin)
echo "📍 GitHub Repository: $GITHUB_URL"

# Check required files
echo ""
echo "🔍 Checking required deployment files..."

required_files=("render.yaml" "requirements.txt" "runtime.txt" "main.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    else
        echo "✅ $file"
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

# Validate render.yaml
echo ""
echo "🔍 Validating render.yaml configuration..."
if grep -q "flash-loan-engine" render.yaml && grep -q "python-3.10.12" render.yaml; then
    echo "✅ render.yaml configuration looks correct"
else
    echo "❌ render.yaml may have configuration issues"
    echo "Please check that it contains 'flash-loan-engine' and 'python-3.10.12'"
fi

# Check Python version compatibility
echo ""
echo "🔍 Checking Python version compatibility..."
if grep -q "python-3.10.12" runtime.txt; then
    echo "✅ Python version specified correctly"
else
    echo "❌ Python version may be incorrect in runtime.txt"
fi

# Validate FastAPI app structure
echo ""
echo "🔍 Validating FastAPI application..."
python3 -c "
from main import app
routes = [route.path for route in app.routes]
required_routes = ['/', '/health', '/status']
missing_routes = [route for route in required_routes if route not in routes]
if missing_routes:
    print(f'❌ Missing required routes: {missing_routes}')
    exit(1)
else:
    print('✅ All required API routes present')
"

# Create deployment commit
echo ""
echo "📝 Creating deployment commit..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    git commit -m "🚀 Configure Flash Loan Engine for Render deployment

- Updated render.yaml with enterprise-grade configuration
- Fixed Python 3.10+ compatibility in requirements.txt
- Created FastAPI web service entry point
- Added health check and monitoring endpoints
- Configured for github.com/TemamAb/myneon deployment

Target: Zero-downtime deployment to Render"
    echo "✅ Deployment commit created"
fi

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
if git push origin main; then
    echo "✅ Successfully pushed to GitHub"
else
    echo "❌ Failed to push to GitHub"
    echo "Please check your git configuration and try again"
    exit 1
fi

# Display deployment information
echo ""
echo "🎉 DEPLOYMENT PREPARATION COMPLETE!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo "1. Go to https://dashboard.render.com/"
echo "2. Create a new Web Service"
echo "3. Connect your GitHub account and select the myneon repository"
echo "4. Configure the service with the settings from render.yaml"
echo "5. Set environment variables in Render dashboard"
echo "6. Deploy and monitor the service"
echo ""
echo "🔗 Useful Links:"
echo "- Render Dashboard: https://dashboard.render.com/"
echo "- Deployment Guide: RENDER_DEPLOYMENT_GUIDE.md"
echo "- GitHub Repository: $GITHUB_URL"
echo ""
echo "📊 API Endpoints (once deployed):"
echo "- GET / - Service information"
echo "- GET /health - Health check"
echo "- GET /status - System status"
echo "- POST /start - Start arbitrage engine"
echo "- POST /stop - Stop arbitrage engine"
echo "- GET /metrics - Performance metrics"
echo ""
echo "✅ Ready for Render deployment!"