import React, { useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { RootState, AppDispatch } from '../store/store'
import { logout } from '../store/slices/authSlice'

interface MainLayoutProps {
  children: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const { user } = useSelector((state: RootState) => state.auth)

  const handleLogout = async () => {
    await dispatch(logout())
    navigate('/login')
  }

  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'ADMIN'

  return (
    <div className="min-h-screen bg-aineon-dark text-white">
      {/* Header */}
      <header className="bg-white/5 backdrop-blur border-b border-white/10">
        <div className="flex items-center justify-between h-16 px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-400 hover:text-white"
            >
              ☰
            </button>
            <h1 className="text-2xl font-bold">AINEON</h1>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 rounded text-sm font-medium transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        {sidebarOpen && (
          <aside className="w-64 bg-white/5 border-r border-white/10 min-h-[calc(100vh-64px)]">
            <nav className="p-6 space-y-4">
              <a
                href="/dashboard"
                className="block px-4 py-2 rounded hover:bg-white/10 transition-colors"
              >
                📊 Dashboard
              </a>
              
              {isAdmin && (
                <>
                  <hr className="border-white/10" />
                  <p className="text-xs font-semibold text-gray-400 uppercase">Admin</p>
                  <a
                    href="/admin"
                    className="block px-4 py-2 rounded hover:bg-white/10 transition-colors"
                  >
                    👥 User Management
                  </a>
                </>
              )}

              <hr className="border-white/10" />
              <a
                href="#"
                className="block px-4 py-2 rounded hover:bg-white/10 transition-colors"
              >
                ⚙️ Settings
              </a>
            </nav>
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

export default MainLayout
