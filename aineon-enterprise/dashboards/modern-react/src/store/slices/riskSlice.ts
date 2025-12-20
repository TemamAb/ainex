import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface RiskMetrics {
  positions: Array<{
    chain: string
    asset: string
    amount: number
    value: number
    concentration: number
  }>
  concentration: {
    highestPool: number
    averageConcentration: number
    riskLevel: 'low' | 'medium' | 'high'
    limit: number
  }
  drawdown: {
    current: number
    max: number
    daily: number
    weekly: number
    monthly: number
  }
  circuitBreaker: {
    status: 'active' | 'triggered' | 'recovery'
    dailyLoss: number
    dailyLimit: number
    recoveryProgress: number
  }
  valueAtRisk: {
    var95: number
    var99: number
    expectedShortfall: number
  }
  slippage: {
    average: number
    max: number
    protectionActive: boolean
  }
}

interface RiskState {
  metrics: RiskMetrics | null
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
}

const initialState: RiskState = {
  metrics: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
}

export const fetchRisk = createAsyncThunk(
  'risk/fetchRisk',
  async () => {
    const response = await api.get('/api/risk')
    return response.data
  }
)

const riskSlice = createSlice({
  name: 'risk',
  initialState,
  reducers: {
    updateMetrics: (state, action) => {
      state.metrics = action.payload
      state.lastUpdated = new Date().toISOString()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRisk.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchRisk.fulfilled, (state, action) => {
        state.isLoading = false
        state.metrics = action.payload
        state.lastUpdated = new Date().toISOString()
      })
      .addCase(fetchRisk.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch risk metrics'
      })
  },
})

export const { updateMetrics } = riskSlice.actions
export default riskSlice.reducer
