#!/bin/bash

#===============================================================================
# AINEON Terminal Profit Monitor - Linux/Mac Script
# Real-time profit metrics display with manual withdrawal mode
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
echo -e "${CYAN}║     AINEON TERMINAL PROFIT MONITOR - MANUAL WITHDRAWAL MODE        ║${NC}"
echo -e "${CYAN}║                   Real-time Profit Display                         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR]${NC} .env file not found"
    echo -e "${BLUE}[INFO]${NC} Please copy .env.example to .env and configure it first"
    exit 1
fi

# Source environment
set -a
source .env
set +a

# Verify RPC is configured
if [ -z "$ETH_RPC_URL" ]; then
    echo -e "${RED}[ERROR]${NC} ETH_RPC_URL not configured in .env"
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} Environment loaded"
echo -e "${BLUE}RPC:${NC}     ${ETH_RPC_URL:0:40}..."
echo -e "${BLUE}Wallet:${NC}  ${WALLET_ADDRESS:0:10}..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 not found in PATH"
    echo -e "${BLUE}[INFO]${NC} Please install Python 3.9 or higher"
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} Starting terminal profit monitor..."
echo -e "${GREEN}[INFO]${NC} Press Ctrl+C to stop"
echo ""
sleep 2

# Run the monitor
python3 terminal_profit_monitor.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}[SUCCESS]${NC} Monitor stopped cleanly"
else
    echo -e "${RED}[ERROR]${NC} Monitor encountered an error (exit code: $exit_code)"
fi

exit $exit_code
