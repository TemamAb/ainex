import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { ProfitMetrics } from '../../types'
import { profitAPI } from '../../services/api'

interface ProfitState {
  metrics: ProfitMetrics | null
  isLoading: boolean
  error: string | null
}

const initialState: ProfitState = {
  metrics: null,
  isLoading: false,
  error: null,
}

export const fetchMetrics = createAsyncThunk(
  'profit/fetchMetrics',
  async (_, { rejectWithValue }) => {
    try {
      const response = await profitAPI.metrics()
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch metrics')
    }
  }
)

const profitSlice = createSlice({
  name: 'profit',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchMetrics.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchMetrics.fulfilled, (state, action) => {
        state.isLoading = false
        state.metrics = action.payload
      })
      .addCase(fetchMetrics.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  },
})

export default profitSlice.reducer
