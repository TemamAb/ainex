#!/bin/bash

# AINEX SECURITY AUDIT PIPELINE
# Tools: Slither (Static Analysis), Mythril (Symbolic Execution)

echo "🛡️ STARTING SECURITY AUDIT..."

# Check for Slither
if ! command -v slither &> /dev/null
then
    echo "⚠️  Slither not found. Please install: pip3 install slither-analyzer"
else
    echo "🔍 Running Slither..."
    slither . --exclude-dependencies --print human-summary
    echo "✅ Slither Complete."
fi

# Check for Mythril
if ! command -v myth &> /dev/null
then
    echo "⚠️  Mythril not found. Please install: pip3 install mythril"
else
    echo "🔍 Running Mythril..."
    myth analyze core-logic/contracts/ApexFlashAggregator.sol --solc-json mythril.config.json
    echo "✅ Mythril Complete."
fi

echo "=================================================="
echo "📝 AUDIT SUMMARY"
echo "If any critical vulnerabilities were found, FIX THEM IMMEDIATELY."
echo "Refer to: https://github.com/crytic/slither/wiki/Detector-Documentation"
echo "=================================================="
