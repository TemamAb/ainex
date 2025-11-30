export class FlashLoanService {
  async getProviderMetrics() {
    try {
      const response = await fetch('/api/flash-loan/metrics');
      const data = await response.json();
      return data.providers;
    } catch (error) {
      console.error('Failed to fetch flash loan metrics:', error);
      throw error;
    }
  }

  async getOptimalLoanSize(opportunity: any) {
    try {
      const response = await fetch('/api/flash-loan/calculate-size', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ opportunity })
      });
      const data = await response.json();
      return data.optimalSize;
    } catch (error) {
      console.error('Failed to calculate optimal loan size:', error);
      throw error;
    }
  }
}
