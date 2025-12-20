#!/bin/bash

################################################################################
# AINEON PHASE 2 EXECUTION LAUNCHER
# Multi-Chain Arbitrage Engine Deployment
# Chief Architect Authorization: ✅ APPROVED
################################################################################

echo "════════════════════════════════════════════════════════════════════════════════"
echo "                     AINEON PHASE 2 EXECUTION INITIATION"
echo "                      Multi-Chain Arbitrage Engine v2.0"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Check environment
echo -e "${CYAN}[PHASE 2] Checking environment...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Using .env.example as reference.${NC}"
    echo -e "${YELLOW}   Please configure your environment variables.${NC}"
fi

# Check Python version
echo -e "${CYAN}[PHASE 2] Validating Python environment...${NC}"
python3 --version

# Check required files
echo -e "${CYAN}[PHASE 2] Verifying Phase 2 files...${NC}"
if [ -f "core/layer2_atomic_executor.py" ]; then
    echo -e "${GREEN}✅ layer2_atomic_executor.py found${NC}"
else
    echo -e "${RED}❌ layer2_atomic_executor.py NOT found${NC}"
    exit 1
fi

if [ -f "core/multi_chain_orchestrator_integration.py" ]; then
    echo -e "${GREEN}✅ multi_chain_orchestrator_integration.py found${NC}"
else
    echo -e "${RED}❌ multi_chain_orchestrator_integration.py NOT found${NC}"
    exit 1
fi

if [ -f "core/layer2_scanner.py" ]; then
    echo -e "${GREEN}✅ layer2_scanner.py found${NC}"
else
    echo -e "${RED}❌ layer2_scanner.py NOT found${NC}"
    exit 1
fi

if [ -f "core/bridge_monitor.py" ]; then
    echo -e "${GREEN}✅ bridge_monitor.py found${NC}"
else
    echo -e "${RED}❌ bridge_monitor.py NOT found${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}[PHASE 2] Configuration Summary:${NC}"
echo "  Investment: \$50K"
echo "  Timeline: 8 weeks (Jan 16 - Mar 15)"
echo "  Target: 290-425 ETH/day (+110-200 from Phase 1)"
echo "  TAM Expansion: \$100M → \$425M (4.25x)"
echo "  ROI: 1,605x"
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}[PHASE 2] EXECUTION AUTHORIZED - STARTING ENGINE${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Start the engine
echo -e "${BOLD}${CYAN}Launching AINEON with Phase 2 multi-chain support...${NC}${BOLD}"
echo ""

# Run main.py with phase 2 active
python3 -m core.main

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ AINEON Phase 2 execution completed successfully${NC}"
else
    echo -e "${RED}❌ AINEON Phase 2 execution ended with code: $exit_code${NC}"
fi

exit $exit_code
