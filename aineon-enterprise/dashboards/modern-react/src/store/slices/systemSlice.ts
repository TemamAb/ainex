import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { SystemStatus } from '../../types'
import { systemAPI } from '../../services/api'

interface SystemState {
  status: SystemStatus | null
  isLoading: boolean
  error: string | null
}

const initialState: SystemState = {
  status: null,
  isLoading: false,
  error: null,
}

export const fetchStatus = createAsyncThunk(
  'system/fetchStatus',
  async (_, { rejectWithValue }) => {
    try {
      const response = await systemAPI.status()
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch status')
    }
  }
)

const systemSlice = createSlice({
  name: 'system',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchStatus.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchStatus.fulfilled, (state, action) => {
        state.isLoading = false
        state.status = action.payload
      })
      .addCase(fetchStatus.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  },
})

export default systemSlice.reducer
