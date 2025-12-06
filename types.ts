export const ModuleStatus = {
  ACTIVE: 'ACTIVE',
  INACTIVE: 'INACTIVE',
  OPTIMIZING: 'OPTIMIZING',
  EXECUTING: 'EXECUTING',
  STANDBY: 'STANDBY',
  ERROR: 'ERROR'
} as const;

export type ModuleStatus = (typeof ModuleStatus)[keyof typeof ModuleStatus];

export type BotTier = 'TIER_1_ARBITRAGE' | 'TIER_2_LIQUIDATION' | 'TIER_3_MEV';

export type ModuleType = 'INFRA' | 'STRATEGY' | 'EXECUTION' | 'SECURITY' | 'MONITORING' | 'AI' | 'BLOCKCHAIN' | 'SERVICES';

export interface EngineModule {
  id: string;
  name: string;
  type: ModuleType;
  status: ModuleStatus;
  details: string;
  metrics?: string;
}

export interface TradeSignal {
  id: string;
  blockNumber: number;
  pair: string;
  chain: 'Ethereum' | 'Arbitrum' | 'Optimism' | 'Base';
  action: 'LONG' | 'SHORT' | 'FLASH_LOAN' | 'MEV_BUNDLE';
  confidence: number;
  expectedProfit: string;
  route: string[];
  timestamp: number;
  txHash?: string;
  status: 'DETECTED' | 'EXECUTING' | 'CONFIRMED' | 'COMPLETED' | 'FAILED';
  actualProfit?: string;
}

export interface AIStrategyResponse {
  sentiment: 'BULLISH' | 'BEARISH' | 'VOLATILE';
  recommendation: string;
  activePairs: string[];
  riskAdjustment: string;
  efficiencyScore: number;
}

export interface SmartWalletState {
  status: 'SEARCHING' | 'DEPLOYING' | 'ACTIVE';
  address: string | null;
  balance: string;
  paymaster: 'LINKED' | 'DISCONNECTED';
}

export interface AutoDepositConfig {
  isEnabled: boolean;
  targetAddress: string;
  profitThreshold: string; // e.g. "500" USDC
  checkInterval: string; // e.g. "15" minutes
  lastTransfer: number | null;
  totalWithdrawn: number;
}

export interface FlashLoanMetric {
  provider: string;
  utilization: number; // 0-100%
  liquidityAvailable: string;
}

export interface BotStatus {
  id: string;
  name: string;
  type: string;
  tier: string;
  status: string;
  uptime: string;
  efficiency: number;
}

export interface TradeLog {
  id: string;
  timestamp: number;
  pair: string;
  action: 'LONG' | 'SHORT' | 'FLASH_LOAN' | 'MEV_BUNDLE';
  profit: number;
  status: 'SUCCESS' | 'FAILED' | 'COMPLETED';
  gasUsed: string;
  txHash?: string;
}

export interface ProfitTargetSettings {
  // Optimal AI-calculated targets
  optimal: {
    hourly: string;
    daily: string;
    weekly: string;
    unit: 'ETH' | 'USD';
  };
  // User override settings
  override: {
    enabled: boolean;
    hourly: string;
    daily: string;
    weekly: string;
    unit: 'ETH' | 'USD';
  };
  // Dynamic adjustment factors
  dynamicAdjustment: {
    marketVolatility: number; // 0-1, affects target scaling
    opportunityDensity: number; // 0-1, number of arbitrage signals
    aiConfidence: number; // 0-1, AI performance score
    riskScore: number; // 0-1, current risk level
  };
  // Active target (optimal or override)
  active: {
    hourly: string;
    daily: string;
    weekly: string;
    unit: 'ETH' | 'USD';
  };
}

export interface TradeSettings {
  profitTarget: ProfitTargetSettings;
  reinvestmentRate: number;
  riskProfile: 'LOW' | 'MEDIUM' | 'HIGH';
  isAIConfigured: boolean;
  maxSlippage: number;
  gasLimitMultiplier: number;
}

export interface ProfitWithdrawalConfig {
  isEnabled: boolean;
  walletAddress: string;
  thresholdAmount: string; // in ETH or USDC
  maxTransferTime: number; // in minutes
  smartBalance: string; // current accumulated profit
  lastWithdrawal: number | null;
  totalWithdrawn: string;
  nextScheduledTransfer: number | null; // timestamp
}

export interface WithdrawalHistory {
  id: string;
  timestamp: number;
  amount: string;
  txHash: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  walletAddress: string;
}