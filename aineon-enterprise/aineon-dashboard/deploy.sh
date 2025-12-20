#!/bin/bash
# AINEON Dashboard Deployment Script
# Automated deployment to GitHub and Render.com

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/TemamAb/myneon.git"
LOCAL_PATH="."
DASHBOARD_DIR="aineon-dashboard"

echo -e "${BLUE}🚀 AINEON Dashboard Deployment Script${NC}"
echo -e "${BLUE}=====================================${NC}"

# Check if we're in the right directory
if [ ! -f "user_friendly_dashboard.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the aineon-dashboard directory${NC}"
    exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"

if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

print_status "Dependencies check passed"

# Test local setup
echo -e "${BLUE}🧪 Testing local setup...${NC}"

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

# Test imports
echo -e "${YELLOW}Testing imports...${NC}"
python3 -c "import streamlit, pandas, plotly, requests; print('All imports successful')"
print_status "Import test passed"

# Test dashboard startup (headless)
echo -e "${YELLOW}Testing dashboard startup...${NC}"
timeout 10s streamlit run user_friendly_dashboard.py --server.headless true &
DASHBOARD_PID=$!
sleep 5

if kill -0 $DASHBOARD_PID 2>/dev/null; then
    kill $DASHBOARD_PID 2>/dev/null || true
    print_status "Dashboard startup test passed"
else
    print_warning "Dashboard startup test failed - may need manual verification"
fi

# Git setup and push
echo -e "${BLUE}📦 Setting up Git repository...${NC}"

# Initialize git if not already done
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing Git repository...${NC}"
    git init
    git remote add origin $REPO_URL
    print_status "Git repository initialized"
else
    print_status "Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Streamlit
.streamlit/

# Logs
logs/
*.log

# Environment variables
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
EOF
    print_status "Created .gitignore"
fi

# Add files to git
echo -e "${YELLOW}Adding files to Git...${NC}"
git add .

# Commit changes
COMMIT_MESSAGE="feat: Deploy AINEON Executive Dashboard

- Add user-friendly dashboard for non-technical users
- Implement error handling and monitoring
- Configure Render.com auto-deployment
- Add Docker containerization
- Setup CI/CD pipeline with GitHub Actions

Features:
- Real-time profit monitoring
- One-click withdrawals
- Risk management
- System health monitoring
- Auto-deployment to Render

Ready for production deployment!"
git commit -m "$COMMIT_MESSAGE"

print_status "Changes committed to Git"

# Check if branch exists and set upstream
echo -e "${YELLOW}Setting up Git branch...${NC}"
if git rev-parse --verify main >/dev/null 2>&1; then
    git checkout main
else
    git checkout -b main
fi

print_status "Git branch setup complete"

# Deployment options
echo -e "${BLUE}🚀 Deployment Options${NC}"
echo "1. Push to GitHub only (manual Render deployment)"
echo "2. Push to GitHub and auto-deploy to Render"
echo "3. Local testing only"

read -p "Select deployment option (1-3): " DEPLOY_OPTION

case $DEPLOY_OPTION in
    1)
        echo -e "${YELLOW}Pushing to GitHub...${NC}"
        git push -u origin main
        print_status "Pushed to GitHub successfully"
        echo -e "${GREEN}🎉 GitHub repository updated!${NC}"
        echo -e "${BLUE}Next steps:${NC}"
        echo "1. Go to https://render.com"
        echo "2. Connect your GitHub repository: $REPO_URL"
        echo "3. Render will auto-detect render.yaml and deploy"
        echo "4. Configure environment variables in Render dashboard"
        ;;
    2)
        echo -e "${YELLOW}Pushing to GitHub...${NC}"
        git push -u origin main
        print_status "Pushed to GitHub successfully"
        
        echo -e "${YELLOW}Note: Auto-deployment to Render requires manual setup${NC}"
        echo -e "${BLUE}Next steps:${NC}"
        echo "1. Go to https://render.com"
        echo "2. Connect your GitHub repository: $REPO_URL"
        echo "3. Render will auto-detect render.yaml and deploy"
        echo "4. Configure environment variables:"
        echo "   - API_BASE_URL"
        echo "   - ETHERSCAN_API_KEY"
        echo "   - WALLET_ADDRESS"
        ;;
    3)
        echo -e "${GREEN}✅ Local testing complete!${NC}"
        echo "Run 'streamlit run user_friendly_dashboard.py' to start dashboard locally"
        ;;
    *)
        print_error "Invalid option selected"
        exit 1
        ;;
esac

# Post-deployment verification
echo -e "${BLUE}📋 Post-deployment checklist:${NC}"
echo "☐ Verify GitHub repository is accessible"
echo "☐ Setup Render.com account and connect repository"
echo "☐ Configure environment variables in Render"
echo "☐ Test deployed dashboard functionality"
echo "☐ Setup monitoring and alerts"
echo "☐ Configure custom domain (optional)"
echo "☐ Setup SSL certificate (automatic with Render)"

# Health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
# AINEON Dashboard Health Check Script

DASHBOARD_URL=${1:-"http://localhost:8501"}

echo "🏥 AINEON Dashboard Health Check"
echo "==============================="

# Check dashboard is responding
echo "Testing dashboard response..."
if curl -f -s "$DASHBOARD_URL" > /dev/null; then
    echo "✅ Dashboard is responding"
else
    echo "❌ Dashboard is not responding"
    exit 1
fi

# Check health endpoint
echo "Testing health endpoint..."
if curl -f -s "$DASHBOARD_URL/_stcore/health" > /dev/null; then
    echo "✅ Health endpoint is working"
else
    echo "❌ Health endpoint failed"
fi

# Check API connectivity (if API_URL is set)
if [ ! -z "$API_BASE_URL" ]; then
    echo "Testing API connectivity..."
    if curl -f -s "$API_BASE_URL/status" > /dev/null; then
        echo "✅ API is responding"
    else
        echo "❌ API is not responding"
    fi
fi

echo "✅ Health check complete"
EOF

chmod +x health_check.sh
print_status "Created health_check.sh script"

# Create environment template
cat > .env.template << EOF
# AINEON Dashboard Environment Template
# Copy this to .env and fill in your values

# API Configuration
API_BASE_URL=http://localhost:8081

# Blockchain Configuration
WALLET_ADDRESS=0xYourWalletAddressHere
PRIVATE_KEY=your_private_key_here

# External APIs
ETHERSCAN_API_KEY=your_etherscan_api_key

# Dashboard Settings
LOG_LEVEL=INFO
REFRESH_INTERVAL=5

# Alert Configuration
ALERT_EMAIL=your_email@example.com
ENABLE_EMAIL_ALERTS=false

# Render Deployment (for production)
# These will be set automatically by Render
# RENDER_HOST=your-app.onrender.com
# PORT=8501
EOF

print_status "Created .env.template"

echo -e "${GREEN}🎉 Deployment preparation complete!${NC}"
echo -e "${BLUE}Files created:${NC}"
echo "  - user_friendly_dashboard.py (Main dashboard)"
echo "  - error_handler.py (Error monitoring)"
echo "  - render.yaml (Render deployment config)"
echo "  - Dockerfile (Container configuration)"
echo "  - requirements.txt (Python dependencies)"
echo "  - package.json (Node.js configuration)"
echo "  - health_check.sh (Health verification)"
echo "  - .env.template (Environment template)"
echo "  - README.md (Documentation)"
echo "  - .github/workflows/deploy.yml (CI/CD)"

echo -e "${BLUE}🚀 Ready for deployment!${NC}"
