import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface AuditEntry {
  id: string
  timestamp: string
  action: string
  component: string
  status: 'success' | 'failed' | 'pending'
  details: string
  user?: string
}

export interface ComplianceMetrics {
  auditTrail: AuditEntry[]
  compliance: {
    status: 'compliant' | 'warning' | 'violation'
    score: number
    lastAudit: string
  }
  verification: {
    etherscan: boolean
    lastVerified: string
    transactionsVerified: number
  }
  reports: Array<{
    id: string
    type: string
    period: string
    status: 'draft' | 'completed' | 'exported'
    generatedAt: string
  }>
  protocols: Array<{
    name: string
    riskScore: number
    status: 'active' | 'monitoring' | 'suspended'
    liquidationCount: number
  }>
  exports: Array<{
    id: string
    type: 'xlsx' | 'pdf'
    name: string
    createdAt: string
    size: number
  }>
}

interface ComplianceState {
  metrics: ComplianceMetrics | null
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
}

const initialState: ComplianceState = {
  metrics: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
}

export const fetchCompliance = createAsyncThunk(
  'compliance/fetchCompliance',
  async () => {
    const response = await api.get('/api/compliance')
    return response.data
  }
)

const complianceSlice = createSlice({
  name: 'compliance',
  initialState,
  reducers: {
    updateMetrics: (state, action) => {
      state.metrics = action.payload
      state.lastUpdated = new Date().toISOString()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCompliance.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchCompliance.fulfilled, (state, action) => {
        state.isLoading = false
        state.metrics = action.payload
        state.lastUpdated = new Date().toISOString()
      })
      .addCase(fetchCompliance.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch compliance'
      })
  },
})

export const { updateMetrics } = complianceSlice.actions
export default complianceSlice.reducer
