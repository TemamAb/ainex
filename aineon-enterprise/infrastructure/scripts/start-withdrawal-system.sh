#!/bin/bash
cd ~/Desktop/aineon-enterprise

echo "íº€ Starting AINEON Withdrawal System..."
echo "======================================="

# Start main backend (if not running)
echo "Starting main backend..."
python app.py &
MAIN_PID=$!
echo "Main backend started (PID: $MAIN_PID)"

# Start withdrawal API
echo "Starting withdrawal API..."
python withdrawal_api.py &
WITHDRAWAL_PID=$!
echo "Withdrawal API started (PID: $WITHDRAWAL_PID)"

# Wait for services to start
sleep 5

echo ""
echo "âœ… SERVICES RUNNING:"
echo "   Main Backend:    http://localhost:8080"
echo "   Withdrawal API:  http://localhost:8081"
echo ""
echo "í³Š DASHBOARDS:"
echo "   â€¢ dashboard-with-withdrawal.html - Full withdrawal system"
echo "   â€¢ ultimate-dashboard.html - Original dashboard"
echo ""
echo "âš¡ OPEN DASHBOARD:"
echo "   start dashboard-with-withdrawal.html"
echo ""
echo "Press Ctrl+C to stop all services"
wait
