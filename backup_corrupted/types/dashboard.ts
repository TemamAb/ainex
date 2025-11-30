export interface ProfitMetrics {
  total: number;
  daily: number;
  profitPerTrade: number;
  tradesPerHour: number;
  winRate: number;
}

export interface FlashLoanProvider {
  name: string;
  liquidity: number;
  utilization: number;
  cost: number;
  health: number;
}

export interface BotStatus {
  seekers: { online: number; total: number; scanning: boolean };
  relayers: { online: number; total: number; executing: boolean };
  orchestrator: { status: string; strategy: string; health: number };
}

export interface SecurityStatus {
  score: number;
  threats: number;
  lastIncident: string;
  mevProtection: boolean;
}

export interface AIOptimizationStatus {
  lastRun: string;
  nextRun: string;
  improvement: number;
  activeStrategies: number;
  confidence: number;
}
