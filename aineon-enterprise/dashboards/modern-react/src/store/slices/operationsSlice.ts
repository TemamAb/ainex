import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface OperationsMetrics {
  rpc: Array<{
    provider: string
    status: 'healthy' | 'degraded' | 'failed'
    latency: number
    uptime: number
    lastCheck: string
  }>
  paymaster: {
    status: 'active' | 'paused' | 'error'
    balance: number
    costToday: number
    sponsorRate: number
  }
  gas: {
    currentPrice: number
    predicted: number
    trend: 'up' | 'down' | 'stable'
    savings: number
  }
  bundles: {
    created: number
    successful: number
    failed: number
    avgTime: number
  }
  errors: Array<{
    id: string
    timestamp: string
    component: string
    message: string
    severity: 'low' | 'medium' | 'high'
  }>
}

interface OperationsState {
  metrics: OperationsMetrics | null
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
}

const initialState: OperationsState = {
  metrics: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
}

export const fetchOperations = createAsyncThunk(
  'operations/fetchOperations',
  async () => {
    const response = await api.get('/api/operations')
    return response.data
  }
)

const operationsSlice = createSlice({
  name: 'operations',
  initialState,
  reducers: {
    updateMetrics: (state, action) => {
      state.metrics = action.payload
      state.lastUpdated = new Date().toISOString()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchOperations.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchOperations.fulfilled, (state, action) => {
        state.isLoading = false
        state.metrics = action.payload
        state.lastUpdated = new Date().toISOString()
      })
      .addCase(fetchOperations.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch operations'
      })
  },
})

export const { updateMetrics } = operationsSlice.actions
export default operationsSlice.reducer
