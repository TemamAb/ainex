'use client';
import { useState, useEffect } from 'react';
import { ProfitMetrics, BotStatus, FlashLoanProvider } from '../types/dashboard';

export const useRealMetrics = () => {
  const [metrics, setMetrics] = useState<ProfitMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRealMetrics = async () => {
      try {
        const response = await fetch('/api/engine/real-time-metrics');
        if (!response.ok) throw new Error('Real data endpoint unavailable');
        
        const data = await response.json();
        if (!data.source || data.source !== 'live_blockchain') {
          throw new Error('Invalid data source: Not from live blockchain');
        }
        
        setMetrics(data.metrics);
      } catch (error) {
        console.error('REAL DATA PROTOCOL VIOLATION:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRealMetrics();
    const interval = setInterval(fetchRealMetrics, 2000);
    return () => clearInterval(interval);
  }, []);

  return { metrics, loading };
};

export const useRealBotStatus = () => {
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);

  useEffect(() => {
    const fetchBotStatus = async () => {
      try {
        const response = await fetch('/api/bots/status');
        const data = await response.json();
        if (data.success) setBotStatus(data.status);
      } catch (error) {
        console.error('Failed to fetch bot status:', error);
      }
    };

    fetchBotStatus();
    const interval = setInterval(fetchBotStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return { botStatus };
};

export const useRealFlashLoanData = () => {
  const [flashData, setFlashData] = useState<FlashLoanProvider[] | null>(null);

  useEffect(() => {
    const fetchFlashData = async () => {
      try {
        const response = await fetch('/api/flash-loan/providers');
        const data = await response.json();
        if (data.success) setFlashData(data.providers);
      } catch (error) {
        console.error('Failed to fetch flash loan data:', error);
      }
    };

    fetchFlashData();
    const interval = setInterval(fetchFlashData, 15000);
    return () => clearInterval(interval);
  }, []);

  return { flashData };
};
