import { TradeSignal, BotStatus, TradeLog } from '../types';

// Historical Data Service for SIM Mode
// Provides 30 days of historical trading data for simulation

export interface HistoricalDataPoint {
  date: string;
  trades: TradeLog[];
  signals: TradeSignal[];
  bots: BotStatus[];
  profit: number;
  volume: number;
  successRate: number;
}

export interface HistoricalMetrics {
  totalDays: number;
  totalTrades: number;
  totalProfit: number;
  averageDailyProfit: number;
  successRate: number;
  bestDay: { date: string; profit: number };
  worstDay: { date: string; profit: number };
  volatility: number;
}

// Generate 30 days of historical trading data
export const generateHistoricalData = (): HistoricalDataPoint[] => {
  const data: HistoricalDataPoint[] = [];
  const now = new Date();

  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    // Generate daily trades (5-15 trades per day)
    const dailyTrades = generateDailyTrades(date);
    const dailySignals = generateDailySignals(date);
    const dailyBots = generateDailyBotStatuses(date);

    // Calculate daily metrics
    const successfulTrades = dailyTrades.filter(t => t.status === 'SUCCESS');
    const dailyProfit = successfulTrades.reduce((sum, t) => sum + t.profit, 0);
    const dailyVolume = dailyTrades.reduce((sum, t) => sum + Math.abs(t.profit) + t.gas, 0);
    const dailySuccessRate = dailyTrades.length > 0 ? (successfulTrades.length / dailyTrades.length) * 100 : 0;

    data.push({
      date: dateStr,
      trades: dailyTrades,
      signals: dailySignals,
      bots: dailyBots,
      profit: dailyProfit,
      volume: dailyVolume,
      successRate: dailySuccessRate
    });
  }

  return data;
};

// Generate trades for a specific day
const generateDailyTrades = (date: Date): TradeLog[] => {
  const trades: TradeLog[] = [];
  const numTrades = 5 + Math.floor(Math.random() * 10); // 5-15 trades

  for (let i = 0; i < numTrades; i++) {
    const tradeTime = new Date(date);
    tradeTime.setHours(9 + Math.floor(Math.random() * 10), Math.floor(Math.random() * 60));

    const pairs = ['ETH/USDC', 'ARB/ETH', 'BTC/USDT', 'LINK/ETH'];
    const dexs = ['Uniswap', 'Sushiswap', 'PancakeSwap'];

    const profit = Math.random() > 0.8 ? Math.random() * 0.5 : -Math.random() * 0.1;
    const gas = Math.random() * 0.01;

    trades.push({
      id: `trade-${date.getTime()}-${i}`,
      timestamp: tradeTime.toISOString(),
      pair: pairs[Math.floor(Math.random() * pairs.length)],
      dex: dexs.slice(0, 1 + Math.floor(Math.random() * 3)),
      profit: profit,
      gas: gas,
      status: profit > 0 ? 'SUCCESS' : 'FAILED'
    });
  }

  return trades;
};

// Generate signals for a specific day
const generateDailySignals = (date: Date): TradeSignal[] => {
  const signals: TradeSignal[] = [];
  const numSignals = Math.floor(Math.random() * 5); // 0-4 signals

  for (let i = 0; i < numSignals; i++) {
    const signalTime = new Date(date);
    signalTime.setHours(9 + Math.floor(Math.random() * 10), Math.floor(Math.random() * 60));

    signals.push({
      id: `signal-${date.getTime()}-${i}`,
      blockNumber: 18000000 + Math.floor(Math.random() * 100000),
      pair: ['ETH/USDC', 'ARB/ETH', 'BTC/USDT'][Math.floor(Math.random() * 3)],
      chain: ['Ethereum', 'Arbitrum', 'Base'][Math.floor(Math.random() * 3)] as any,
      action: ['FLASH_LOAN', 'MEV_BUNDLE', 'ARBITRAGE'][Math.floor(Math.random() * 3)] as any,
      confidence: 70 + Math.random() * 25,
      expectedProfit: (0.001 + Math.random() * 0.1).toFixed(4),
      route: ['Uniswap', 'Sushiswap', 'PancakeSwap'].slice(0, 1 + Math.floor(Math.random() * 3)),
      timestamp: signalTime.getTime(),
      status: 'DETECTED'
    });
  }

  return signals;
};

// Generate bot statuses for a specific day
const generateDailyBotStatuses = (date: Date): BotStatus[] => {
  return [
    {
      id: 'bot-1',
      name: 'Arbitrage Hunter',
      type: 'ARBITRAGE',
      tier: 'TIER_1_ARBITRAGE',
      status: Math.random() > 0.1 ? 'ACTIVE' : 'MAINTENANCE',
      uptime: (98 + Math.random() * 2).toFixed(1) + '%',
      efficiency: 85 + Math.floor(Math.random() * 10)
    },
    {
      id: 'bot-2',
      name: 'Liquidation Engine',
      type: 'LIQUIDATION',
      tier: 'TIER_2_LIQUIDATION',
      status: Math.random() > 0.05 ? 'ACTIVE' : 'OPTIMIZING',
      uptime: (99 + Math.random() * 1).toFixed(1) + '%',
      efficiency: 90 + Math.floor(Math.random() * 8)
    },
    {
      id: 'bot-3',
      name: 'MEV Protector',
      type: 'MEV',
      tier: 'TIER_3_MEV',
      status: Math.random() > 0.02 ? 'ACTIVE' : 'ACTIVE',
      uptime: '99.9%',
      efficiency: 95 + Math.floor(Math.random() * 5)
    }
  ];
};

// Calculate historical metrics
export const calculateHistoricalMetrics = (data: HistoricalDataPoint[]): HistoricalMetrics => {
  const totalDays = data.length;
  const totalTrades = data.reduce((sum, day) => sum + day.trades.length, 0);
  const totalProfit = data.reduce((sum, day) => sum + day.profit, 0);
  const averageDailyProfit = totalProfit / totalDays;

  const successRates = data.map(day => day.successRate);
  const successRate = successRates.reduce((sum, rate) => sum + rate, 0) / successRates.length;

  const profits = data.map(day => day.profit);
  const bestDay = {
    date: data[profits.indexOf(Math.max(...profits))].date,
    profit: Math.max(...profits)
  };
  const worstDay = {
    date: data[profits.indexOf(Math.min(...profits))].date,
    profit: Math.min(...profits)
  };

  // Calculate volatility (standard deviation of daily profits)
  const mean = averageDailyProfit;
  const variance = profits.reduce((sum, profit) => sum + Math.pow(profit - mean, 2), 0) / profits.length;
  const volatility = Math.sqrt(variance);

  return {
    totalDays,
    totalTrades,
    totalProfit,
    averageDailyProfit,
    successRate,
    bestDay,
    worstDay,
    volatility
  };
};
