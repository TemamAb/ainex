// App Type Definitions
export interface WalletState {
  isConnected: boolean;
  address: string;
  type: 'EOA' | 'SMART_WALLET';
  balance: number;
  chainId?: number;
}

export interface UserProfile {
  id?: string;
  name: string;
  email: string;
  avatar?: string;
  riskProfile?: 'LOW' | 'MEDIUM' | 'HIGH';
  createdAt?: Date;
  updatedAt?: Date;
}

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: Date;
  children?: FileNode[];
}

export interface MetricsData {
  balance: number;
  latencyMs: number;
  mevBlocked: number;
  aiEfficiencyDelta: number;
  gasPrice: number;
  ethPrice: number;
  volatility: number;
  theoreticalMaxProfit: number;
  aiCapturedProfit: number;
  profitPerHour: number;
  profitPerTrade: number;
  tradesPerHour: number;
  totalProfitCumulative: number;
}
