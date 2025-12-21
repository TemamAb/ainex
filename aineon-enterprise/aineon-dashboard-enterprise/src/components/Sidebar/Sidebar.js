import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  CogIcon,
  HomeIcon,
  ArrowTrendingUpIcon,
  WalletIcon,
  ShieldCheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CubeIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const navigation = [
    {
      name: 'Dashboard',
      href: '/',
      icon: HomeIcon,
      current: location.pathname === '/'
    },
    {
      name: 'Profit Analytics',
      href: '/analytics',
      icon: ChartBarIcon,
      current: location.pathname === '/analytics'
    },
    {
      name: 'Live Engines',
      href: '/engines',
      icon: CubeIcon,
      current: location.pathname === '/engines'
    },
    {
      name: 'Blockchain Monitor',
      href: '/blockchain',
      icon: GlobeAltIcon,
      current: location.pathname === '/blockchain'
    },
    {
      name: 'Withdrawal Controls',
      href: '/withdrawals',
      icon: WalletIcon,
      current: location.pathname === '/withdrawals'
    },
    {
      name: 'Real-Time Transactions',
      href: '/transactions',
      icon: ArrowTrendingUpIcon,
      current: location.pathname === '/transactions'
    },
    {
      name: 'System Security',
      href: '/security',
      icon: ShieldCheckIcon,
      current: location.pathname === '/security'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: CogIcon,
      current: location.pathname === '/settings'
    }
  ];

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  return (
    <div className={`bg-gray-900 text-white transition-all duration-300 ease-in-out ${
      collapsed ? 'w-16' : 'w-64'
    } min-h-screen relative flex flex-col`}>
      
      {/* Header with Logo and Toggle */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className={`flex items-center space-x-3 ${collapsed ? 'justify-center' : ''}`}>
          {/* Ainex Logo Placeholder */}
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">A</span>
          </div>
          {!collapsed && (
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Ainex
              </h1>
              <p className="text-xs text-gray-400">Enterprise Dashboard</p>
            </div>
          )}
        </div>
        
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
        >
          {collapsed ? (
            <ChevronRightIcon className="h-5 w-5" />
          ) : (
            <ChevronLeftIcon className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* System Status Indicator */}
      <div className="px-4 py-3">
        <div className={`bg-green-500/20 border border-green-500/30 rounded-lg p-3 ${collapsed ? 'text-center' : ''}`}>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            {!collapsed && (
              <>
                <span className="text-green-400 text-sm font-medium">LIVE</span>
                <span className="text-gray-400 text-xs">$310K+ Generated</span>
              </>
            )}
          </div>
          {!collapsed && (
            <p className="text-xs text-gray-400 mt-1">
              2 Engines Active • 89.9% Success Rate
            </p>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`
                group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200
                ${item.current
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }
                ${collapsed ? 'justify-center' : ''}
              `}
              title={collapsed ? item.name : ''}
            >
              <Icon
                className={`flex-shrink-0 h-5 w-5 ${
                  item.current ? 'text-white' : 'text-gray-400 group-hover:text-white'
                }`}
              />
              {!collapsed && (
                <span className="ml-3 truncate">{item.name}</span>
              )}
              {!collapsed && item.current && (
                <div className="ml-auto w-2 h-2 bg-white rounded-full"></div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Quick Stats Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-gray-700">
          <div className="bg-gray-800 rounded-lg p-3">
            <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
              Quick Stats
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">Total Profit</span>
                <span className="text-xs font-medium text-green-400">$310,818</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">Success Rate</span>
                <span className="text-xs font-medium text-blue-400">89.9%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">ETH Transferred</span>
                <span className="text-xs font-medium text-purple-400">59.08</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live Profit Indicator */}
      <div className="p-4">
        <div className={`bg-gradient-to-r from-green-600 to-blue-600 rounded-lg p-3 ${
          collapsed ? 'text-center' : ''
        }`}>
          <div className="flex items-center space-x-2">
            <CurrencyDollarIcon className="h-5 w-5 text-white" />
            {!collapsed && (
              <>
                <div>
                  <p className="text-white text-sm font-medium">Live Profit Rate</p>
                  <p className="text-green-100 text-xs">$65,831/hour</p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;