#!/bin/bash

echo "íº€ AINEON DASHBOARD LAUNCHER"
echo "============================="
echo ""
echo "Available Dashboards:"
echo "1. í¾¯ Phase 1: Engine Interface (phase1-standalone.html)"
echo "2. í¼ Phase 2: Multi-Chain (phase2-multichain.html)"
echo "3. í±‘ Master Dashboard (master-dashboard.html)"
echo "4. í²Ž Ultimate Dashboard (ultimate-dashboard.html)"
echo "5. í´§ Working Dashboard (working-dashboard.html)"
echo "6. í²° Withdrawal Dashboard (dashboard-with-withdrawal.html)"
echo "7. í¿¢ Enterprise Dashboard (enterprise-flashloan-dashboard.html)"
echo "8. í³‹ List All Dashboards"
echo "9. íºª Exit"
echo ""
read -p "Select dashboard [1-9]: " choice

case $choice in
    1)
        echo "Opening Phase 1 Dashboard..."
        [ -f "phase1-standalone.html" ] && open phase1-standalone.html || echo "File not found!"
        ;;
    2)
        echo "Opening Phase 2 Dashboard..."
        [ -f "phase2-multichain.html" ] && open phase2-multichain.html || echo "File not found!"
        ;;
    3)
        echo "Opening Master Dashboard..."
        [ -f "master-dashboard.html" ] && open master-dashboard.html || echo "File not found!"
        ;;
    4)
        echo "Opening Ultimate Dashboard..."
        [ -f "ultimate-dashboard.html" ] && open ultimate-dashboard.html || echo "File not found!"
        ;;
    5)
        echo "Opening Working Dashboard..."
        [ -f "working-dashboard.html" ] && open working-dashboard.html || echo "File not found!"
        ;;
    6)
        echo "Opening Withdrawal Dashboard..."
        [ -f "dashboard-with-withdrawal.html" ] && open dashboard-with-withdrawal.html || echo "File not found!"
        ;;
    7)
        echo "Opening Enterprise Dashboard..."
        [ -f "enterprise-flashloan-dashboard.html" ] && open enterprise-flashloan-dashboard.html || echo "File not found!"
        ;;
    8)
        echo ""
        echo "í³Š ALL DASHBOARD FILES:"
        echo "----------------------"
        ls -la *.html | grep -i dashboard
        echo ""
        echo "Total: $(ls *.html 2>/dev/null | grep -i dashboard | wc -l) dashboard files"
        ;;
    9)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac
