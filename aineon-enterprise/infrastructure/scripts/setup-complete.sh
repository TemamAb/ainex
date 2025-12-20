#!/bin/bash

#===============================================================================
# AINEON Complete Setup - Linux/Mac
# Reads .env, configures manual withdrawal, and starts monitoring
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          AINEON COMPLETE SETUP - MANUAL WITHDRAWAL MODE           ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR]${NC} .env file not found"
    echo -e "${BLUE}[INFO]${NC} Please create .env file with your configuration first"
    exit 1
fi

echo -e "${GREEN}[STEP 1]${NC} Validating .env file..."
python3 setup_manual_withdrawal.py

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Setup configuration failed"
    exit 1
fi

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         SETUP COMPLETE - READY TO DEPLOY AND MONITOR              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}[NEXT STEPS]${NC}"
echo ""
echo "1. Deploy AINEON Engine:"
echo "   ${CYAN}./deploy-production.sh${NC}"
echo ""
echo "2. Start Terminal Profit Monitor (in another terminal):"
echo "   ${CYAN}./run-terminal-monitor.sh${NC}"
echo ""
echo "3. Watch real-time profit metrics accumulate"
echo ""
echo "4. When profit reaches 5.0 ETH, withdraw manually:"
echo "   ${CYAN}curl -X POST http://localhost:8081/withdraw${NC}"
echo ""
