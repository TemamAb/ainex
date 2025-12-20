#!/bin/bash
cd ~/Desktop/aineon-enterprise

echo "íº€ AINEON MASTER SYSTEM STARTUP"
echo "================================"

# Function to check and start service
start_service() {
    port=$1
    command=$2
    name=$3
    log_file=$4
    
    if ! lsof -i :$port >/dev/null 2>&1; then
        echo "Starting $name on port $port..."
        $command > $log_file 2>&1 &
        pid=$!
        echo $pid > $name.pid
        echo "âœ… $name started (PID: $pid)"
        sleep 2
    else
        echo "âœ… $name already running on :$port"
    fi
}

# Start all services
start_service 3000 "node server.js" "NodeJS" "node.log"
start_service 8080 "python app.py" "Python" "python.log"
start_service 8081 "python withdrawal_api.py" "WithdrawalAPI" "withdrawal.log"

# Wait for initialization
echo ""
echo "â³ Initializing backends..."
sleep 5

# Open dashboard
echo ""
echo "í³Š OPENING MASTER DASHBOARD..."
if command -v start >/dev/null 2>&1; then
    start master-dashboard.html
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open master-dashboard.html
elif command -v open >/dev/null 2>&1; then
    open master-dashboard.html
else
    echo "Please open: file://$(pwd)/master-dashboard.html"
fi

echo ""
echo "âœ… SYSTEM STARTUP COMPLETE!"
echo ""
echo "í³¡ BACKEND ENDPOINTS:"
echo "   http://localhost:3000  - Node.js API"
echo "   http://localhost:8080  - Python Backend"
echo "   http://localhost:8081  - Withdrawal API"
echo ""
echo "í³Š MASTER DASHBOARD: master-dashboard.html"
echo ""
echo "í»‘ To stop all services:"
echo "   pkill -f 'node.*server'"
echo "   pkill -f 'python.*(app|withdrawal)'"
echo "   rm -f *.pid *.log"
