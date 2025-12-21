#!/bin/bash
"""
AINEON MASTER DASHBOARD - TEST DEPLOYMENT SCRIPT
Safely deploys master dashboard to isolated ports for testing
Run this first to test without conflicts
"""

echo "🚀 AINEON MASTER DASHBOARD - TEST DEPLOYMENT"
echo "============================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Step 1: Check if master dashboard files exist
echo "Step 1: Verifying Master Dashboard Files"
echo "========================================"

required_files=(
    "master_dashboard.html"
    "master_dashboard_backup.py"
    "dashboard_launcher.py"
    "backup_dashboard.html"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "Found: $file"
    else
        print_error "Missing: $file"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    print_error "Some required files are missing. Please ensure all master dashboard files are present."
    exit 1
fi

echo ""

# Step 2: Check for port conflicts
echo "Step 2: Checking for Port Conflicts"
echo "==================================="

test_ports=(9001 9002 9003 9004)
port_conflicts=false

for port in "${test_ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        print_warning "Port $port is already in use"
        port_conflicts=true
    else
        print_status "Port $port is available"
    fi
done

if [ "$port_conflicts" = true ]; then
    print_warning "Some test ports are in use. Existing services may be affected."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled by user"
        exit 1
    fi
fi

echo ""

# Step 3: Kill any existing test deployments
echo "Step 3: Cleaning Up Previous Test Deployments"
echo "============================================="

# Kill any existing HTTP servers on test ports
for port in "${test_ports[@]}"; do
    pid=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        kill $pid 2>/dev/null
        print_status "Killed process on port $port (PID: $pid)"
    fi
done

# Kill any existing master dashboard processes
pkill -f "master_dashboard_backup.py" 2>/dev/null && print_status "Stopped existing backup dashboard"
pkill -f "dashboard_launcher.py" 2>/dev/null && print_status "Stopped existing launcher"

# Clean up PID files
rm -f master_dashboard_pids.txt

echo ""

# Step 4: Install Python dependencies if needed
echo "Step 4: Checking Python Dependencies"
echo "===================================="

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.7+"
    exit 1
fi

print_status "Using Python: $($PYTHON_CMD --version)"

# Check for required packages
missing_packages=()

if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
    missing_packages+=("flask")
fi

if ! $PYTHON_CMD -c "import flask_socketio" 2>/dev/null; then
    missing_packages+=("flask-socketio")
fi

if [ ${#missing_packages[@]} -gt 0 ]; then
    print_warning "Missing packages: ${missing_packages[*]}"
    print_info "Installing missing packages..."
    
    $PYTHON_CMD -m pip install flask flask-socketio gunicorn
    
    if [ $? -eq 0 ]; then
        print_status "Packages installed successfully"
    else
        print_error "Failed to install packages. Backup dashboard may not work."
        print_info "Primary dashboard (HTML) will still work without dependencies."
    fi
else
    print_status "All required packages are installed"
fi

echo ""

# Step 5: Deploy Primary Dashboard (HTML)
echo "Step 5: Deploying Primary Dashboard (HTML)"
echo "========================================="

print_info "Starting HTTP server for HTML dashboard on port 9001..."

# Start HTTP server in background
$PYTHON_CMD -m http.server 9001 > master_dashboard_server.log 2>&1 &
PRIMARY_PID=$!
echo $PRIMARY_PID > master_dashboard_pids.txt

# Wait a moment for server to start
sleep 2

# Check if server is running
if curl -s http://localhost:9001/master_dashboard.html > /dev/null; then
    print_status "Primary dashboard started successfully (PID: $PRIMARY_PID)"
    print_info "Access URL: http://localhost:9001/master_dashboard.html"
else
    print_error "Primary dashboard failed to start"
    kill $PRIMARY_PID 2>/dev/null
    exit 1
fi

echo ""

# Step 6: Deploy Backup Dashboard (Python)
echo "Step 6: Deploying Backup Dashboard (Python)"
echo "=========================================="

print_info "Starting Python backup dashboard on port 9002..."

# Set environment variables
export DASHBOARD_PORT=9002
export DASHBOARD_DEBUG=False
export DASHBOARD_HOST=0.0.0.0

# Start backup dashboard in background
$PYTHON_CMD master_dashboard_backup.py > master_dashboard_backup.log 2>&1 &
BACKUP_PID=$!
echo $BACKUP_PID >> master_dashboard_pids.txt

# Wait for startup
print_info "Waiting for backup dashboard to initialize..."
sleep 5

# Check if backup dashboard is responding
if curl -s http://localhost:9002/health > /dev/null; then
    print_status "Backup dashboard started successfully (PID: $BACKUP_PID)"
    print_info "Access URL: http://localhost:9002"
else
    print_warning "Backup dashboard may not be fully ready yet"
    print_info "Check logs: tail -f master_dashboard_backup.log"
fi

echo ""

# Step 7: Test Dashboard Accessibility
echo "Step 7: Testing Dashboard Accessibility"
echo "======================================="

# Test primary dashboard
echo -n "Primary Dashboard (HTML): "
if curl -s http://localhost:9001/master_dashboard.html | grep -q "AINEON Master Dashboard"; then
    print_status "ACCESSIBLE"
else
    print_error "NOT ACCESSIBLE"
fi

# Test backup dashboard
echo -n "Backup Dashboard (Python): "
if curl -s http://localhost:9002/api/status | grep -q "online"; then
    print_status "ACCESSIBLE"
else
    print_error "NOT ACCESSIBLE"
fi

# Test smart launcher
echo -n "Smart Launcher: "
if $PYTHON_CMD dashboard_launcher.py --test > /dev/null 2>&1; then
    print_status "WORKING"
else
    print_error "NOT WORKING"
fi

echo ""

# Step 8: Create Monitoring Script
echo "Step 8: Creating Monitoring Script"
echo "================================="

cat > monitor_master_dashboard.sh << 'EOF'
#!/bin/bash
echo "🔍 AINEON Master Dashboard Status Monitor"
echo "========================================"

# Check if processes are running
echo "Process Status:"
if ps -p $(sed -n '1p' master_dashboard_pids.txt 2>/dev/null) > /dev/null 2>&1; then
    echo "✅ Primary Dashboard (HTTP Server): RUNNING"
else
    echo "❌ Primary Dashboard (HTTP Server): STOPPED"
fi

if ps -p $(sed -n '2p' master_dashboard_pids.txt 2>/dev/null) > /dev/null 2>&1; then
    echo "✅ Backup Dashboard (Python): RUNNING"
else
    echo "❌ Backup Dashboard (Python): STOPPED"
fi

echo ""
echo "Service Accessibility:"

# Test primary dashboard
if curl -s http://localhost:9001/master_dashboard.html > /dev/null 2>&1; then
    echo "✅ Primary Dashboard: ACCESSIBLE (http://localhost:9001/master_dashboard.html)"
else
    echo "❌ Primary Dashboard: NOT ACCESSIBLE"
fi

# Test backup dashboard
if curl -s http://localhost:9002/api/status > /dev/null 2>&1; then
    echo "✅ Backup Dashboard: ACCESSIBLE (http://localhost:9002)"
else
    echo "❌ Backup Dashboard: NOT ACCESSIBLE"
fi

echo ""
echo "Quick Actions:"
echo "- Stop all: ./stop_master_dashboard_test.sh"
echo "- Test launcher: python dashboard_launcher.py --test"
echo "- Check status: python dashboard_launcher.py --status"
echo "- View logs: tail -f master_dashboard*.log"

EOF

chmod +x monitor_master_dashboard.sh
print_status "Monitoring script created: ./monitor_master_dashboard.sh"

echo ""

# Step 9: Create Stop Script
echo "Step 9: Creating Stop Script"
echo "==========================="

cat > stop_master_dashboard_test.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping AINEON Master Dashboard Test Deployment"
echo "=================================================="

# Kill processes using PID file
if [ -f "master_dashboard_pids.txt" ]; then
    while IFS= read -r pid; do
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null
            echo "Stopped process (PID: $pid)"
        fi
    done < master_dashboard_pids.txt
    
    rm -f master_dashboard_pids.txt
    print_status "All test processes stopped"
else
    print_warning "PID file not found, attempting manual cleanup..."
    
    # Manual cleanup
    pkill -f "http.server 9001" 2>/dev/null && echo "Stopped HTTP server on port 9001"
    pkill -f "master_dashboard_backup.py" 2>/dev/null && echo "Stopped backup dashboard"
    pkill -f "dashboard_launcher.py" 2>/dev/null && echo "Stopped launcher"
fi

# Clean up log files
rm -f master_dashboard_server.log master_dashboard_backup.log

print_status "Test deployment stopped and cleaned up"

EOF

chmod +x stop_master_dashboard_test.sh
print_status "Stop script created: ./stop_master_dashboard_test.sh"

echo ""

# Step 10: Final Status Report
echo "Step 10: Deployment Complete - Status Report"
echo "============================================"

print_status "🎉 MASTER DASHBOARD TEST DEPLOYMENT SUCCESSFUL!"
echo ""

echo "📊 DEPLOYMENT SUMMARY:"
echo "====================="
echo "✅ Primary Dashboard (HTML): http://localhost:9001/master_dashboard.html"
echo "✅ Backup Dashboard (Python): http://localhost:9002"
echo "✅ Smart Launcher: python dashboard_launcher.py"
echo "✅ Emergency Dashboard: Available in backup_dashboard.html"
echo ""

echo "🛠️  MANAGEMENT COMMANDS:"
echo "========================"
echo "• Monitor status: ./monitor_master_dashboard.sh"
echo "• Stop deployment: ./stop_master_dashboard_test.sh"
echo "• Test launcher: python dashboard_launcher.py --test"
echo "• Check health: python dashboard_launcher.py --status"
echo "• Force backup: python dashboard_launcher.py --force-backup"
echo "• Emergency mode: python dashboard_launcher.py --emergency"
echo ""

echo "📁 FILES CREATED:"
echo "================"
echo "• master_dashboard_pids.txt - Process IDs for management"
echo "• monitor_master_dashboard.sh - Status monitoring script"
echo "• stop_master_dashboard_test.sh - Cleanup script"
echo "• master_dashboard_server.log - HTTP server logs"
echo "• master_dashboard_backup.log - Python dashboard logs"
echo ""

echo "🧪 NEXT STEPS:"
echo "============="
echo "1. Test all dashboard features manually"
echo "2. Run comprehensive tests: ./test_*.sh scripts"
echo "3. Compare with existing dashboards"
echo "4. Validate performance and functionality"
echo "5. Proceed with migration if satisfied"
echo ""

print_info "Test deployment is now running on isolated ports."
print_info "Existing dashboards on ports 8000, 8080, 8501 remain unaffected."
print_info "You can safely test the master dashboard system without conflicts."

# Show running processes
echo ""
echo "🔍 RUNNING PROCESSES:"
echo "==================="
ps aux | grep -E "(http.server|master_dashboard)" | grep -v grep || echo "No dashboard processes found"

echo ""
print_status "Deployment completed successfully! 🎯"