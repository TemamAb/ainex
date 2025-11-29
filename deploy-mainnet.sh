#!/bin/bash

# Ainex Production Deployment Script
# This script deploys the Ainex arbitrage engine to Ethereum mainnet

set -e  # Exit on error

echo "=================================="
echo "🚀 AINEX DEPLOYMENT SCRIPT"
echo "=================================="
echo ""

# Check environment variables
if [ -z "$ALCHEMY_MAINNET_URL" ]; then
    echo "❌ Error: ALCHEMY_MAINNET_URL not set"
    echo "Please set: export ALCHEMY_MAINNET_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY"
    exit 1
fi

if [ -z "$PRIVATE_KEY" ]; then
    echo "❌ Error: PRIVATE_KEY not set"
    echo "Please set: export PRIVATE_KEY=0x..."
    exit 1
fi

echo "✅ Environment variables configured"
echo ""

# Step 1: Install dependencies
echo "📦 Installing dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""

# Step 2: Compile contracts
echo "🔨 Compiling smart contracts..."
npx hardhat compile
echo "✅ Contracts compiled"
echo ""

# Step 3: Run tests (optional but recommended)
read -p "Run tests before deployment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Running tests..."
    npx hardhat test
    echo "✅ Tests passed"
    echo ""
fi

# Step 4: Deploy to network
read -p "Deploy to MAINNET? This will cost real ETH. (yes/no) " -r
echo
if [[ $REPLY == "yes" ]]; then
    echo "🚀 Deploying to Ethereum Mainnet..."
    npx hardhat run core-logic/scripts/deploy.cjs --network mainnet
    echo "✅ Deployment complete!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Verify contracts on Etherscan"
    echo "2. Update .env with deployed contract addresses"
    echo "3. Configure bot system with contract addresses"
    echo "4. Start bot services"
else
    echo "❌ Deployment cancelled"
    exit 0
fi

echo ""
echo "=================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=================================="
