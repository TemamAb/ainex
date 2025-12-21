import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar/Sidebar';
import Header from './components/Header/Header';
import Dashboard from './pages/Dashboard/Dashboard';
import Engines from './pages/Engines/Engines';
import Transactions from './pages/Transactions/Transactions';
import Withdrawals from './pages/Withdrawals/Withdrawals';
import Blockchain from './pages/Blockchain/Blockchain';
import Settings from './pages/Settings/Settings';
import { ProfitProvider } from './context/ProfitContext';
import './App.css';

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <ProfitProvider>
      <Router>
        <div className="app">
          <Sidebar 
            collapsed={sidebarCollapsed} 
            toggleSidebar={toggleSidebar}
            isConnected={isConnected}
          />
          <div className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
            <Header 
              toggleSidebar={toggleSidebar}
              isConnected={isConnected}
              setIsConnected={setIsConnected}
            />
            <div className="content-area">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/engines" element={<Engines />} />
                <Route path="/transactions" element={<Transactions />} />
                <Route path="/withdrawals" element={<Withdrawals />} />
                <Route path="/blockchain" element={<Blockchain />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </div>
        </div>
      </Router>
    </ProfitProvider>
  );
}

export default App;