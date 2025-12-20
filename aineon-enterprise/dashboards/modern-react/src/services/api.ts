import axios, { AxiosInstance, AxiosError } from 'axios'
import { LoginPayload, RegisterPayload } from '../types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8081/api'

const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (!refreshToken) throw new Error('No refresh token')
        
        const response = await axios.post(`${API_BASE}/auth/refresh-token`, {
          refreshToken,
        })
        localStorage.setItem('accessToken', response.data.accessToken)
        return api(originalRequest)
      } catch {
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth endpoints
export const authAPI = {
  register: (payload: RegisterPayload) => api.post('/auth/register', payload),
  login: (payload: LoginPayload) => api.post('/auth/login', payload),
  verifyEmail: (token: string) => api.get(`/auth/verify-email?token=${token}`),
  logout: () => api.post('/auth/logout'),
  refreshToken: (token: string) => api.post('/auth/refresh-token', { refreshToken: token }),
  me: () => api.get('/auth/me'),
}

// System endpoints
export const systemAPI = {
  health: () => api.get('/health'),
  status: () => api.get('/status'),
}

// Profit endpoints
export const profitAPI = {
  metrics: () => api.get('/profit'),
  config: (payload: any) => api.post('/settings/profit-config', payload),
}

// Opportunities endpoints
export const opportunitiesAPI = {
  list: () => api.get('/opportunities'),
}

// Audit endpoints
export const auditAPI = {
  data: () => api.get('/audit'),
  report: () => api.get('/audit/report'),
}

// Admin endpoints
export const adminAPI = {
  pendingUsers: (params?: any) => api.get('/admin/users/pending', { params }),
  users: (params?: any) => api.get('/admin/users', { params }),
  userDetail: (userId: string) => api.get(`/admin/users/${userId}`),
  approveUser: (userId: string, payload: any) => api.post(`/admin/users/${userId}/approve`, payload),
  rejectUser: (userId: string, payload: any) => api.post(`/admin/users/${userId}/reject`, payload),
  suspendUser: (userId: string, payload: any) => api.post(`/admin/users/${userId}/suspend`, payload),
  unsuspendUser: (userId: string) => api.post(`/admin/users/${userId}/unsuspend`),
  assignRole: (userId: string, roleId: string) => api.post(`/admin/users/${userId}/assign-role`, { roleId }),
  stats: () => api.get('/admin/stats'),
  auditLog: (params?: any) => api.get('/admin/audit-log', { params }),
}

// User endpoints
export const userAPI = {
  profile: () => api.get('/users/profile'),
  updateProfile: (payload: any) => api.put('/users/profile', payload),
  generateApiKey: () => api.post('/users/api-keys/generate'),
  listApiKeys: () => api.get('/users/api-keys'),
  revokeApiKey: (keyId: string) => api.delete(`/users/api-keys/${keyId}`),
  teamMembers: () => api.get('/users/organization/members'),
  subscription: () => api.get('/users/billing/subscription'),
  usage: () => api.get('/users/usage'),
}

export default api
