export interface BotStatus {
  id: string;
  name: string;
  type: 'EXECUTOR' | 'SCANNER' | 'VALIDATOR';
  tier: 'TIER_1' | 'TIER_2' | 'TIER_3';
  status: 'ONLINE' | 'OFFLINE' | 'WARNING';
  uptime: string;
  efficiency: number;
}

export interface TradeLog {
  id: string;
  timestamp: string;
  pair: string;
  dex: string[];
  profit: number;
  gas: number;
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
}

export interface RiskMetric {
  metric: string;
  value: number;
  threshold: number;
  status: 'SAFE' | 'CAUTION' | 'CRITICAL';
}

export type View = 'OVERVIEW' | 'BOTS' | 'AI_COPILOT' | 'FLASH' | 'RISK' | 'TREASURY';

export type Currency = 'USD' | 'ETH';
export type ExecutionMode = 'SIMULATION' | 'LIVE';
export type RefreshRate = 1000 | 5000 | 10000;

export interface ProjectStats {
  totalFiles: number;
  totalDirectories: number;
  extensions: Record<string, number>;
  topDirectories: Record<string, number>;
}

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  extension?: string;
}

export interface WalletState {
  isConnected: boolean;
  address: string | null;
  type: 'EOA' | 'SMART_WALLET' | null;
  balance: number;
}