export class AIOptimizerService {
  private optimizationInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.setupScheduledOptimization();
  }

  async getOptimizationStatus() {
    try {
      const response = await fetch('/api/ai/status');
      const data = await response.json();
      return {
        status: data.status,
        strategies: data.strategies,
        performance: data.performance,
        nextOptimization: this.calculateNextOptimizationTime()
      };
    } catch (error) {
      console.error('Failed to get AI optimization status:', error);
      throw error;
    }
  }

  async runOptimizationCycle() {
    try {
      const response = await fetch('/api/ai/optimize', { method: 'POST' });
      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Optimization cycle failed:', error);
      throw error;
    }
  }

  private setupScheduledOptimization() {
    // Run every 15 minutes
    this.optimizationInterval = setInterval(() => {
      this.runOptimizationCycle().catch(console.error);
    }, 15 * 60 * 1000);
  }

  private calculateNextOptimizationTime(): Date {
    const now = new Date();
    return new Date(now.getTime() + 15 * 60 * 1000);
  }

  destroy() {
    if (this.optimizationInterval) {
      clearInterval(this.optimizationInterval);
    }
  }
}
