import { BotStatus, TradeLog } from './types';

export const APP_NAME = "AiNex Engine";

export const MOCK_BOTS: BotStatus[] = [
  { id: 'b1', name: 'Alpha-Clone-01', type: 'SCANNER', tier: 'TIER_1', status: 'ONLINE', uptime: '48h 12m', efficiency: 98.5 },
  { id: 'b2', name: 'Mev-Shield-Core', type: 'VALIDATOR', tier: 'TIER_2', status: 'ONLINE', uptime: '120h 05m', efficiency: 99.9 },
  { id: 'b3', name: 'Execution-Agent-X', type: 'EXECUTOR', tier: 'TIER_3', status: 'WARNING', uptime: '4h 30m', efficiency: 78.2 },
  { id: 'b4', name: 'Liquidity-Sniper', type: 'SCANNER', tier: 'TIER_1', status: 'OFFLINE', uptime: '0m', efficiency: 0 },
];

export const MOCK_TRADES: TradeLog[] = [
  { id: 'tx-0x8a...29b', timestamp: '10:42:05', pair: 'WETH/USDC', dex: ['Uniswap V3', 'Curve'], profit: 1240.50, gas: 45.20, status: 'SUCCESS' },
  { id: 'tx-0x7b...11a', timestamp: '10:41:58', pair: 'WBTC/DAI', dex: ['SushiSwap', 'Balancer'], profit: 890.12, gas: 52.10, status: 'SUCCESS' },
  { id: 'tx-0x3c...99f', timestamp: '10:40:12', pair: 'LINK/WETH', dex: ['Uniswap V2', 'SushiSwap'], profit: 0, gas: 12.00, status: 'FAILED' },
  { id: 'tx-0x1d...44e', timestamp: '10:39:45', pair: 'AAVE/USDT', dex: ['Aave', 'Uniswap V3'], profit: 345.80, gas: 38.50, status: 'SUCCESS' },
  { id: 'tx-0x9e...22c', timestamp: '10:38:20', pair: 'MKR/DAI', dex: ['Balancer', 'Uniswap V3'], profit: 2100.00, gas: 110.00, status: 'SUCCESS' },
];

export const SYSTEM_LOGS = [
  "[INFO] 10:42:05 - Arbitrage opportunity detected on WETH/USDC (Spread: 0.8%)",
  "[EXEC] 10:42:05 - Flash loan initiated: 1,000,000 USDC via Aave Pool",
  "[EXEC] 10:42:06 - Swap executed on Uniswap V3 (Route: USDC -> WETH)",
  "[EXEC] 10:42:06 - Swap executed on Curve (Route: WETH -> USDC)",
  "[INFO] 10:42:07 - Loan repaid. Net Profit: 1240.50 USDC",
  "[RISK] 10:42:10 - Gas spike detected (55 gwei). Adjusting slipage tolerance.",
  "[WARN] 10:42:15 - Execution-Agent-X latency increased to 150ms.",
];

export const RAW_FILE_LIST = `
./.dockerignore
./.env
./.env.example
./.gitignore
./app/components/ActivationOverlay.tsx
./app/components/GrafanaCard.tsx
./app/components/layout/Header.tsx
./app/engine/EngineContext.tsx
./app/favicon.ico
./app/globals.css
./app/layout.tsx
./app/page.tsx
./apps/dashboard/src/app/ai/page.tsx
./apps/dashboard/src/app/bots/page.tsx
./apps/dashboard/src/app/chain/page.tsx
./apps/dashboard/src/app/flash/page.tsx
./apps/dashboard/src/app/page.tsx
./apps/dashboard/src/app/risk/page.tsx
./apps/dashboard/src/app/treasury/page.tsx
./apps/dashboard/src/app/wallet/page.tsx
./architecture.md
./build.js
./build.sh
./core-logic/agents/DecisionAgent.py
./core-logic/agents/DetectionAgent.py
./core-logic/agents/ExecutionAgent.py
./core-logic/agents/MultiAgentOrchestrator.py
./core-logic/ai/alpha-clone.py
./core-logic/ai/behavioral-models.py
./core-logic/ai/co-pilot-orchestrator.py
./core-logic/ai/market-analyzer.py
./core-logic/ai/predictive-analytics.py
./core-logic/ai/ainex-optimizer.py
./core-logic/ai/risk-intelligence.py
./core-logic/ai/strategy-optimizer.py
./core-logic/artifacts/contracts/ApexFlashLoan.sol/ApexFlashLoan.json
./core-logic/bots/executor-bot.js
./core-logic/bots/memory-pool.js
./core-logic/bots/message-broker.js
./core-logic/bots/scanner-bot.js
./core-logic/bots/validator-bot.js
./core-logic/contracts/ApexAccount.sol
./core-logic/contracts/ApexDEXRouter.sol
./core-logic/contracts/ApexFactory.sol
./core-logic/contracts/ApexFlashLoan.sol
./core-logic/contracts/MEVShield.sol
./core-logic/deployment/deployment-manager.js
./core-logic/deployment/environment-config.js
./core-logic/deployment/kubernetes-orchestration.yml
./core-logic/deployment/package.json
./core-logic/execution/atomic-cross-chain.js
./core-logic/execution/institutional-executor.js
./core-logic/execution/liquidity-optimizer.js
./core-logic/execution/mev-protector.js
./core-logic/infrastructure/bridge-manager.js
./core-logic/infrastructure/chain-dominance.js
./core-logic/infrastructure/cross-chain-monitor.js
./core-logic/infrastructure/multi-chain-router.js
./core-logic/infrastructure/rpc-optimizer.js
./core-logic/infrastructure/service-mesh.js
./core-logic/infrastructure/shared-cache.js
./core-logic/infrastructure/websocket-manager.js
./core-logic/infrastructure/worker-threads.js
./core-logic/monitoring/performance-tracker.js
./core-logic/platform/auth-system.js
./core-logic/platform/command-center.js
./core-logic/platform/compliance-engine.js
./core-logic/platform/latency-monitor.js
./core-logic/platform/real-time-metrics.js
./core-logic/platform/risk-monitor.js
./core-logic/scripts/verify-optimizations.js
./core-logic/security/admin-panel.js
./core-logic/security/capital-allocator.js
./core-logic/security/deposit-handler.js
./core-logic/security/profit-tracker.js
./core-logic/security/security-manager.js
./core-logic/security/threat-intelligence.js
./core-logic/security/wallet-connector.js
./core-logic/security/wallet-manager.js
./core-logic/security/withdrawal-manager.js
./core-logic/security/zero-trust-gateway.js
./docker-compose.yml
./Dockerfile
./eslint.config.mjs
./next.config.js
./next.config.ts
./next-env.d.ts
./package.json
./package-lock.json
./ainex-setup.sh
./README.md
./render.yaml
./requirements.txt
./tailwind.config.ts
`;