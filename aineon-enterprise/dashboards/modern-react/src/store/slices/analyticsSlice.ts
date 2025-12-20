import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface AnalyticsMetrics {
  deepRL: {
    accuracy: number
    confidence: number
    trend: number[]
  }
  marketRegime: {
    current: string
    volatility: number
    type: 'stable' | 'volatile' | 'trending' | 'choppy' | 'extreme'
  }
  transformer: {
    profitPrediction: number
    opportunityScore: number
    directionBias: string
    liquidityTrend: number
  }
  strategies: Array<{
    name: string
    weight: number
    winRate: number
    profitContribution: number
  }>
  latency: {
    p50: number
    p95: number
    p99: number
    target: number
  }
}

interface AnalyticsState {
  metrics: AnalyticsMetrics | null
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
}

const initialState: AnalyticsState = {
  metrics: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
}

export const fetchAnalytics = createAsyncThunk(
  'analytics/fetchAnalytics',
  async () => {
    const response = await api.get('/api/analytics')
    return response.data
  }
)

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    updateMetrics: (state, action) => {
      state.metrics = action.payload
      state.lastUpdated = new Date().toISOString()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAnalytics.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchAnalytics.fulfilled, (state, action) => {
        state.isLoading = false
        state.metrics = action.payload
        state.lastUpdated = new Date().toISOString()
      })
      .addCase(fetchAnalytics.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch analytics'
      })
  },
})

export const { updateMetrics } = analyticsSlice.actions
export default analyticsSlice.reducer
