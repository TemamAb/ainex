import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface WithdrawalTransaction {
  id: string
  timestamp: string
  amount: number
  asset: string
  status: 'pending' | 'completed' | 'failed'
  txHash?: string
  to: string
}

export interface WithdrawalMetrics {
  mode: 'auto' | 'manual'
  availableBalance: number
  pendingWithdrawals: number
  totalWithdrawn: number
  autoThreshold: number
  autoEnabled: boolean
  lastWithdrawal?: string
  history: WithdrawalTransaction[]
  stats: {
    dailyWithdrawn: number
    weeklyWithdrawn: number
    monthlyWithdrawn: number
    totalCount: number
    successRate: number
  }
}

interface WithdrawalState {
  metrics: WithdrawalMetrics | null
  isLoading: boolean
  isWithdrawing: boolean
  error: string | null
  lastUpdated: string | null
  successMessage: string | null
}

const initialState: WithdrawalState = {
  metrics: null,
  isLoading: false,
  isWithdrawing: false,
  error: null,
  lastUpdated: null,
  successMessage: null,
}

export const fetchWithdrawalMetrics = createAsyncThunk(
  'withdrawal/fetchMetrics',
  async () => {
    const response = await api.get('/api/withdrawal/metrics')
    return response.data
  }
)

export const executeManualWithdrawal = createAsyncThunk(
  'withdrawal/executeManual',
  async (payload: { amount: number; toAddress: string }, { rejectWithValue }) => {
    try {
      const response = await api.post('/api/withdrawal/manual', {
        amount: payload.amount,
        toAddress: payload.toAddress,
      })
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Withdrawal failed')
    }
  }
)

export const updateAutoWithdrawalConfig = createAsyncThunk(
  'withdrawal/updateAutoConfig',
  async (payload: { enabled: boolean; threshold: number }, { rejectWithValue }) => {
    try {
      const response = await api.post('/api/withdrawal/auto/config', payload)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Configuration update failed')
    }
  }
)

export const getWithdrawalHistory = createAsyncThunk(
  'withdrawal/getHistory',
  async (limit: number = 20) => {
    const response = await api.get(`/api/withdrawal/history?limit=${limit}`)
    return response.data
  }
)

const withdrawalSlice = createSlice({
  name: 'withdrawal',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    clearSuccessMessage: (state) => {
      state.successMessage = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Metrics
      .addCase(fetchWithdrawalMetrics.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchWithdrawalMetrics.fulfilled, (state, action) => {
        state.isLoading = false
        state.metrics = action.payload
        state.lastUpdated = new Date().toISOString()
      })
      .addCase(fetchWithdrawalMetrics.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch withdrawal metrics'
      })

      // Manual Withdrawal
      .addCase(executeManualWithdrawal.pending, (state) => {
        state.isWithdrawing = true
        state.error = null
      })
      .addCase(executeManualWithdrawal.fulfilled, (state, action) => {
        state.isWithdrawing = false
        state.successMessage = `Withdrawal of ${action.payload.amount} completed successfully`
        if (state.metrics) {
          state.metrics.availableBalance -= action.payload.amount
          state.metrics.totalWithdrawn += action.payload.amount
          state.metrics.lastWithdrawal = new Date().toISOString()
        }
      })
      .addCase(executeManualWithdrawal.rejected, (state, action) => {
        state.isWithdrawing = false
        state.error = action.payload as string
      })

      // Update Auto Config
      .addCase(updateAutoWithdrawalConfig.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(updateAutoWithdrawalConfig.fulfilled, (state, action) => {
        state.isLoading = false
        if (state.metrics) {
          state.metrics.autoEnabled = action.payload.enabled
          state.metrics.autoThreshold = action.payload.threshold
        }
        state.successMessage = 'Auto-withdrawal configuration updated'
      })
      .addCase(updateAutoWithdrawalConfig.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

      // Get History
      .addCase(getWithdrawalHistory.pending, (state) => {
        state.isLoading = true
      })
      .addCase(getWithdrawalHistory.fulfilled, (state, action) => {
        state.isLoading = false
        if (state.metrics) {
          state.metrics.history = action.payload.history
        }
      })
      .addCase(getWithdrawalHistory.rejected, (state) => {
        state.isLoading = false
      })
  },
})

export const { clearError, clearSuccessMessage } = withdrawalSlice.actions
export default withdrawalSlice.reducer
