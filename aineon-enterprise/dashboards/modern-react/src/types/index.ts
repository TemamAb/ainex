// User & Auth Types
export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  organizationId: string
  organizationName: string
  role: 'SUPER_ADMIN' | 'ADMIN' | 'TRADER' | 'AUDITOR' | 'VIEWER'
  status: 'PENDING_VERIFICATION' | 'PENDING_APPROVAL' | 'ACTIVE' | 'SUSPENDED'
  emailVerified: boolean
  twoFactorEnabled: boolean
  createdAt: string
  lastLogin?: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  accessToken: string | null
  refreshToken: string | null
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  firstName: string
  lastName: string
  organizationName: string
  country: string
  useCase: string
  subscriptionTier: 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE'
  termsAccepted: boolean
}

// System Status Types
export interface SystemStatus {
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED'
  mode: 'LIVE_MODE' | 'TEST_MODE'
  chainId: number
  aiActive: boolean
  gaslessMode: boolean
  flashLoansActive: boolean
  scannersActive: boolean
  orchestratorsActive: boolean
  executorsActive: boolean
  autoAiActive: boolean
  monitoringMode: boolean
  executionMode: boolean
  tier: string
}

// Profit Types
export interface ProfitMetrics {
  accumulatedEthVerified: number
  accumulatedUsdVerified: number
  accumulatedEthPending: number
  accumulatedUsdPending: number
  accumulatedEthTotal: number
  thresholdEth: number
  autoTransferEnabled: boolean
  activeTrades: number
  successfulTrades: number
  ethPrice: number
  targetWallet: string
  etherscanEnabled: boolean
  verificationStatus: string
  auditInfo: {
    totalTransactionsAudited: number
    verifiedCount: number
    pendingCount: number
  }
}

// Opportunity Types
export interface Opportunity {
  pair: string
  dex: string
  profit: number
  confidence: number
  tx: string
  timestamp: number
}

export interface OpportunitiesResponse {
  opportunities: Opportunity[]
  totalFound: number
  scanTimestamp: number
}

// Trade History Types
export interface Trade {
  id: string
  pair: string
  dexBuy: string
  dexSell: string
  profitEth: number
  profitUsd: number
  confidence: number
  executedAt: string
  status: 'PENDING' | 'SUCCESS' | 'FAILED'
  txHash?: string
}

// AI Metrics Types
export interface AIMetrics {
  accuracy: number
  confidence: number
  marketRegime: number
  strategyId: number
  performanceScore: number
  predictionOutputs: number[]
}

// Risk Metrics Types
export interface RiskMetrics {
  positions: Position[]
  concentration: number
  drawdown: number
  maxPosition: number
  valueAtRisk: number
  circuitBreakerStatus: string
}

export interface Position {
  symbol: string
  amount: number
  value: number
  chain: string
  concentration: number
}

// Admin Types
export interface PendingUser {
  id: string
  email: string
  firstName: string
  lastName: string
  organizationName: string
  country: string
  subscriptionTier: string
  useCase: string
  appliedAt: string
  emailVerified: boolean
  riskFlag?: string
}

export interface ApprovalPayload {
  reason: string
}

// Audit Types
export interface AuditLog {
  id: string
  userId: string
  userEmail: string
  action: string
  resourceType: string
  resourceId: string
  changes: Record<string, any>
  ipAddress: string
  timestamp: string
  status: 'SUCCESS' | 'FAILURE'
}

// Health Check Types
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: number
  rpcConnected: boolean
}
