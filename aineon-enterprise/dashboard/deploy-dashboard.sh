#!/bin/bash
# Ì∫Ä AINEON ENTERPRISE DASHBOARD DEPLOYMENT

echo "================================================="
echo "Ì∫Ä DEPLOYING AINEON ENTERPRISE DASHBOARD"
echo "================================================="

# Navigate to dashboard
cd ~/Desktop/aineon-enterprise/dashboard

# Install dependencies
echo "Ì≥¶ Installing dependencies..."
npm install

# Build the dashboard
echo "Ì¥® Building dashboard..."
npm run build

# Start the backend if not running
echo "‚öôÔ∏è Starting backend services..."
cd ..
if [ -f "app.py" ]; then
    echo "Starting Python backend..."
    python app.py &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
fi

# Start the dashboard
echo "Ìºê Starting dashboard..."
cd dashboard
npm run dev &

echo ""
echo "================================================="
echo "‚úÖ DEPLOYMENT COMPLETE!"
echo "================================================="
echo ""
echo "Ìºê ACCESS POINTS:"
echo "   Dashboard:      http://localhost:3000"
echo "   Backend API:    http://localhost:8080"
echo "   Flask API:      http://localhost:5000"
echo ""
echo "Ì≥ä FEATURES DEPLOYED:"
echo "   ‚Ä¢ Real-time profit tracking"
echo "   ‚Ä¢ Multi-DEX arbitrage monitoring"
echo "   ‚Ä¢ Flash loan opportunities"
echo "   ‚Ä¢ MEV bot control"
echo "   ‚Ä¢ Portfolio management"
echo "   ‚Ä¢ Risk analytics"
echo "   ‚Ä¢ AI optimizer"
echo ""
echo "‚ö° Quick commands:"
echo "   View logs:      tail -f logs/*.log"
echo "   Stop all:       pkill -f 'node\|python'"
echo ""
