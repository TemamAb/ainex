import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8082';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Interceptors for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.message);
    return Promise.reject(error);
  }
);

export const dashboardApi = {
  // Profit endpoints
  getProfit: () => api.get('/profit'),
  getStatus: () => api.get('/status'),
  getMetrics: () => api.get('/metrics'),
  
  // Control endpoints
  initialize: (data: any) => api.post('/initialize', data),
  startTrading: () => api.post('/start'),
  stopTrading: () => api.post('/stop'),
  
  // Configuration
  updateConfig: (config: any) => api.post('/config', config),
  
  // Real-time SSE
  subscribeToUpdates: (onUpdate: (data: any) => void) => {
    const eventSource = new EventSource(`${API_BASE}/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (error) {
        console.error('SSE parse error:', error);
      }
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      setTimeout(() => dashboardApi.subscribeToUpdates(onUpdate), 5000);
    };
    
    return () => eventSource.close();
  }
};
