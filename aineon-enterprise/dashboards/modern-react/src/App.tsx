import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from './store/store'
import { getMe } from './store/slices/authSlice'

// Pages
import LoginForm from './components/auth/LoginForm'
import Dashboard from './components/dashboard/Dashboard'
import AdminDashboard from './pages/AdminDashboard'
import ProtectedRoute from './components/auth/ProtectedRoute'
import MainLayout from './layouts/MainLayout'

const App: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth)

  useEffect(() => {
    const token = localStorage.getItem('accessToken')
    if (token && !isAuthenticated) {
      dispatch(getMe())
    }
  }, [dispatch, isAuthenticated])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-aineon-dark flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginForm />} />
        
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="ADMIN">
              <MainLayout>
                <AdminDashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  )
}

export default App
