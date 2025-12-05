import { BotStatus, TradeLog } from './types';

export const APP_NAME = "AiNex Engine";

// PERFORMANCE CONFIDENCE CONSTANTS
export const PERFORMANCE_MODES = {
  SIM: 'SIM',
  LIVE: 'LIVE'
} as const;

export type PerformanceMode = typeof PERFORMANCE_MODES[keyof typeof PERFORMANCE_MODES];

export const CONFIDENCE_THRESHOLDS = {
  HIGH: 85,      // >85% confidence - excellent SIM accuracy
  MEDIUM: 70,    // 70-85% confidence - good SIM accuracy
  LOW: 50        // <70% confidence - caution advised
} as const;

export const VARIANCE_TARGETS = {
  NORMAL: 5.0,      // ±5% expected variance in normal conditions
  VOLATILE: 8.0,    // ±8% expected variance in volatile markets
  EXTREME: 15.0     // ±15% expected variance in extreme conditions
} as const;

export const MARKET_CONDITIONS = {
  NORMAL: { gasThreshold: 50, volatilityThreshold: 40 },
  VOLATILE: { gasThreshold: 100, volatilityThreshold: 70 },
  EXTREME: { gasThreshold: Infinity, volatilityThreshold: Infinity }
} as const;

// EDUCATIONAL TOOLTIPS
export const TOOLTIPS = {
  PROFIT_VELOCITY: {
    title: "Profit Velocity",
    description: "The rate at which the arbitrage engine generates profit. Shows hourly earnings, per-trade profit, and trade frequency.",
    example: "2.5 ETH/hour = earning 2.5 ETH every hour from arbitrage trades"
  },
  THEORETICAL_MAX: {
    title: "Theoretical Maximum",
    description: "The maximum possible profit per block under perfect conditions (zero gas, zero slippage, instant execution). This is the upper limit of what the engine could achieve.",
    example: "0.05 ETH/block = if every opportunity was captured perfectly"
  },
  TOTAL_PROFIT: {
    title: "Total Profit",
    description: "Cumulative profit earned since the engine started. This is the lifetime total of all successful arbitrage trades minus gas costs.",
    example: "15.8 ETH = total profit earned across all trades"
  },
  AI_OPTIMIZATION: {
    title: "AI Optimization",
    description: "How much better the AI-powered engine performs compared to a basic arbitrage bot. Shows the efficiency gain from machine learning optimizations.",
    example: "+12.5% = AI strategies earn 12.5% more than baseline"
  },
  CONFIDENCE_SCORE: {
    title: "Confidence Score",
    description: "Measures how reliable SIM mode predictions are. Higher confidence means SIM mode will more accurately predict LIVE mode performance. Must reach 85% to enable LIVE mode.",
    example: "85% confidence = SIM predictions within ±5-8% of actual LIVE results"
  },
  EXPECTED_VARIANCE: {
    title: "Expected Variance",
    description: "The anticipated difference between SIM mode predictions and actual LIVE mode results, even under perfect conditions. This accounts for unavoidable real-world factors.",
    example: "±6% variance = if SIM predicts 1 ETH profit, expect 0.94-1.06 ETH in LIVE"
  },
  MARKET_CONDITION: {
    title: "Market Condition",
    description: "Current market state based on gas prices and volatility. Affects expected variance and confidence scores.",
    example: "NORMAL = stable conditions, VOLATILE = high activity, EXTREME = chaotic markets"
  },
  GAS_COSTS: {
    title: "Gas Cost Variance",
    description: "Uncertainty in transaction gas costs due to network congestion and gas price fluctuations. Higher gas prices increase variance.",
    example: "±2.5% = gas costs could vary by 2.5% from estimates"
  },
  SLIPPAGE: {
    title: "Slippage Variance",
    description: "Price movement that occurs between when you submit a trade and when it executes. Higher in volatile markets or low liquidity pools.",
    example: "±1.5% = price could move 1.5% during trade execution"
  },
  MEV_RISK: {
    title: "MEV Risk (Maximal Extractable Value)",
    description: "The probability that bots or validators will front-run your transaction to extract profit, reducing your gains. Protected by Flashbots integration.",
    example: "±1.2% = MEV bots might reduce profit by up to 1.2%"
  },
  NETWORK_LATENCY: {
    title: "Network Latency",
    description: "Delays in transaction propagation and block inclusion. Affects timing-sensitive arbitrage opportunities.",
    example: "±0.75% = timing delays could impact profit by 0.75%"
  },
  PRICE_MOVEMENT: {
    title: "Price Movement",
    description: "Market price drift during the time between opportunity detection and execution. More significant in volatile markets.",
    example: "±1.5% = prices could move 1.5% while trade executes"
  },
  REVERSION_RISK: {
    title: "Reversion Risk",
    description: "Probability that a transaction will fail and revert. With mempool shadowing, failed trades don't cost gas, but opportunities are missed.",
    example: "±1.5% = some opportunities may fail, reducing overall profit"
  },
  SIM_MODE: {
    title: "SIM Mode (Simulation)",
    description: "Simulation mode runs on real blockchain data and real-time market prices, but doesn't execute actual trades. Used to validate strategies before going live.",
    example: "Tests strategies with zero risk using live market data"
  },
  LIVE_MODE: {
    title: "LIVE Mode",
    description: "Live trading mode executes real transactions on the blockchain with actual capital. Only available when confidence score reaches 85%.",
    example: "Real trades with real profit (and real risk)"
  },
  VARIANCE_VS_LIVE: {
    title: "Variance vs LIVE",
    description: "The expected performance difference between SIM mode predictions and actual LIVE mode results. Shown as a percentage range.",
    example: "±6.2% = LIVE results will be within 6.2% of SIM predictions"
  },
  CONFIDENCE_THRESHOLD: {
    title: "85% Confidence Threshold",
    description: "The minimum confidence score required to enable LIVE mode. This ensures SIM predictions are reliable enough to trust with real capital.",
    example: "Below 85% = stay in SIM mode, conditions too uncertain"
  },
  STRATEGY_WEIGHTS: {
    title: "Active Strategy Weights",
    description: "The AI's current allocation across different arbitrage strategies. Weights adjust dynamically based on market conditions and performance.",
    example: "DEX Arb: 45% = 45% of capital allocated to DEX arbitrage"
  }
} as const;

// AI TERMINAL CONSTANTS
export const AI_TERMINAL = {
  QUICK_QUERIES: [
    "What's the best opportunity now?",
    "How am I doing today?",
    "Explain MEV protection",
    "Should I trade during high gas?",
    "Predict next hour profit",
    "Give me a strategy tip"
  ],

  EXAMPLE_QUERIES: {
    OPPORTUNITIES: [
      "Show me profitable WETH trades",
      "Find arbitrage opportunities",
      "What's the best trade right now?",
      "Show me low-risk opportunities"
    ],
    PERFORMANCE: [
      "How am I doing today?",
      "Analyze my performance this week",
      "What's my success rate?",
      "Show me my best trades"
    ],
    STRATEGY: [
      "Should I increase my gas limit?",
      "What's the optimal strategy now?",
      "How can I improve my profit?",
      "Give me trading advice"
    ],
    EXPLANATIONS: [
      "Explain MEV protection",
      "What is a flash loan?",
      "How does confidence score work?",
      "What affects slippage?"
    ]
  },

  RESPONSE_TEMPLATES: {
    GREETING: "👋 Welcome to AI Terminal Assistant!",
    ERROR: "❌ Sorry, I encountered an error.",
    UNKNOWN: "I'm not sure how to help with that.",
    PROCESSING: "🤔 Analyzing..."
  }
} as const;


export const MOCK_BOTS: BotStatus[] = [
  // STRICT NO MOCK DATA: Bots must be registered dynamically by the execution engine
];

export const MOCK_TRADES: TradeLog[] = [
  // STRICT NO MOCK DATA: Trade logs must come from real blockchain events
];

export const SYSTEM_LOGS = [
  "[INFO] System initialized. Waiting for real-time events...",
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