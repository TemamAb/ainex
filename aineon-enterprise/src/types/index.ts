export interface ProfitData {
  timestamp: string;
  current_profit: number;
  profit_rate: number;
  status: 'active' | 'paused' | 'error';
  metrics?: {
    transactions: number;
    volume: number;
    efficiency: number;
  };
}

export interface DashboardConfig {
  profit_threshold: number;
  auto_trading: boolean;
  alert_level: 'low' | 'medium' | 'high';
}
