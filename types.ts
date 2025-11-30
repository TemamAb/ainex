export enum ModuleStatus {
  ACTIVE = 'ACTIVE',
  OPTIMIZING = 'OPTIMIZING',
  EXECUTING = 'EXECUTING',
  STANDBY = 'STANDBY',
  ERROR = 'ERROR'
}

export type BotTier = 'TIER_1_ARBITRAGE' | 'TIER_2_LIQUIDATION' | 'TIER_3_MEV';

export interface EngineModule {
  id: string;
  name: string;
  type: 'INFRA' | 'STRATEGY' | 'EXECUTION';
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
  status: 'DETECTED' | 'EXECUTING' | 'CONFIRMED';
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