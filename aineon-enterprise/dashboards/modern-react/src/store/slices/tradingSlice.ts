import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface TradingMetrics {
  flashLoans: Array<{
    id: string
    provider: string
    amount: number
    fee: number
    status: 'active' | 'repaid' | 'failed'
    timestamp: string
  }>
  mev: {
    totalCaptured: number
    captureRate: number
    bundles: number
    avgProfit: number
  }
  liquidations: Array<{
    id: string
    protocol: string
    amount: number
    profit: number
    status: 'pending' | 'executed' | 'failed'
    timestamp: string
  }>
  multiChain: {
    ethereum: {
      trades: number
      profit: number
      status: 'active' | 'inactive'
    }
    arbitrum: {
      trades: number
      profit: number
      status: 'active' | 'inactive'
    }
    optimism: {
      trades: number
      profit: number
      status: 'active' | 'inactive'
    }
    polygon: {
      trades: number
      profit: number
      status: 'active' | 'inactive'
    }
  }
  bridges: Array<{
    protocol: string
    volume: number
    fees: number
    status: 'active' | 'monitoring'
  }>
}

interface TradingState {
  metrics: TradingMetrics | null
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
}

const initialState: TradingState = {
  metrics: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
}

export const fetchTrading = createAsyncThunk(
  'trading/fetchTrading',
  async () => {
    const response = await api.get('/api/trading')
    return response.data
  }
)

const tradingSlice = createSlice({
  name: 'trading',
  initialState,
  reducers: {
    updateMetrics: (state, action) => {
      state.metrics = action.payload
      state.lastUpdated = new Date().toISOString()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTrading.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchTrading.fulfilled, (state, action) => {
        state.isLoading = false
        state.metrics = action.payload
        state.lastUpdated = new Date().toISOString()
      })
      .addCase(fetchTrading.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch trading metrics'
      })
  },
})

export const { updateMetrics } = tradingSlice.actions
export default tradingSlice.reducer
