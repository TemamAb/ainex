#!/bin/bash

# Ainex Deployment Readiness Fix Script
# 1. Installs dependencies
# 2. Compiles Smart Contracts
# 3. Deploys to Local Hardhat Network

echo "=========================================="
echo "   AINEX ARBITRAGE FLASH LOAN FIXER       "
echo "=========================================="

# 1. Install Dependencies
echo "[1/3] Installing Dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "Error: npm install failed."
    exit 1
fi

# 2. Compile Contracts
echo "[2/3] Compiling Smart Contracts..."
npx hardhat compile --config hardhat.config.cjs
if [ $? -ne 0 ]; then
    echo "Error: Hardhat compilation failed."
    exit 1
fi

# 3. Deploy to Local Network
echo "[3/3] Deploying to Local Hardhat Network..."
# We use the default hardhat network which spins up, deploys, and tears down.
# This verifies the deployment script works.
npx hardhat run core-logic/scripts/deploy.cjs --config hardhat.config.cjs
if [ $? -ne 0 ]; then
    echo "Error: Deployment failed."
    echo "Tip: Ensure ALCHEMY_MAINNET_URL is set in .env if forking is enabled."
    exit 1
fi

echo "=========================================="
echo "   SUCCESS: READY FOR DEPLOYMENT          "
echo "=========================================="
