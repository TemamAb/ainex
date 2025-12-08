import React, { useState, useEffect } from 'react';
import {
  User, Settings, Shield, Wallet, TrendingUp, Activity,
  Mail, Phone, MapPin, Calendar, Key, Bell, Eye, EyeOff,
  Edit3, Save, X, CheckCircle, AlertTriangle, Clock
} from 'lucide-react';

interface UserProfile {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  joinDate: string;
  lastLogin: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'PENDING';
  role: 'USER' | 'ADMIN';
  tradingLevel: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | 'EXPERT';
  riskTolerance: 'LOW' | 'MEDIUM' | 'HIGH';
  preferredCurrency: 'ETH' | 'USD';
  timezone: string;
  language: string;
}

interface WalletInfo {
  address: string;
  balance: string;
  network: string;
  isVerified: boolean;
  lastTransaction: string;
}

interface TradingStats {
  totalTrades: number;
  successfulTrades: number;
  totalProfit: number;
  winRate: number;
  avgProfitPerTrade: number;
  bestTrade: number;
  worstTrade: number;
  currentStreak: number;
}

interface SecuritySettings {
  twoFactorEnabled: boolean;
  emailNotifications: boolean;
  tradeNotifications: boolean;
  securityAlerts: boolean;
  sessionTimeout: number;
  ipWhitelist: string[];
}

const UserProfile: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'trading' | 'security' | 'settings'>('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [showPrivateKey, setShowPrivateKey] = useState(false);

  // Mock user data - in real app, this would come from API
  const [userProfile, setUserProfile] = useState<UserProfile>({
    id: 'user_12345',
    email: 'john.doe@example.com',
    username: 'johndoe_trader',
    firstName: 'John',
    lastName: 'Doe',
    joinDate: '2024-01-15',
    lastLogin: '2024-12-19T10:30:00Z',
    status: 'ACTIVE',
    role: 'USER',
    tradingLevel: 'ADVANCED',
    riskTolerance: 'MEDIUM',
    preferredCurrency: 'ETH',
    timezone: 'UTC-5',
    language: 'en'
  });

  const [walletInfo, setWalletInfo] = useState<WalletInfo>({
    address: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
    balance: '2.45',
    network: 'Ethereum',
    isVerified: true,
    lastTransaction: '2024-12-19T09:15:00Z'
  });

  const [tradingStats, setTradingStats] = useState<TradingStats>({
    totalTrades: 1247,
    successfulTrades: 892,
    totalProfit: 15.67,
    winRate: 71.5,
    avgProfitPerTrade: 0.0126,
    bestTrade: 2.34,
    worstTrade: -0.89,
    currentStreak: 5
  });

  const [securitySettings, setSecuritySettings] = useState<SecuritySettings>({
    twoFactorEnabled: true,
    emailNotifications: true,
    tradeNotifications: true,
    securityAlerts: true,
    sessionTimeout: 30,
    ipWhitelist: ['192.168.1.1', '10.0.0.1']
  });

  const tabs = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'trading', label: 'Trading', icon: TrendingUp },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'text-green-400 bg-green-500/20';
      case 'SUSPENDED': return 'text-red-400 bg-red-500/20';
      case 'PENDING': return 'text-yellow-400 bg-yellow-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW': return 'text-green-400';
      case 'MEDIUM': return 'text-yellow-400';
      case 'HIGH': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="bg-slate-800/50 rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <User size={32} className="text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">{userProfile.firstName} {userProfile.lastName}</h2>
              <p className="text-slate-400">@{userProfile.username}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(userProfile.status)}`}>
                  {userProfile.status}
                </span>
                <span className="text-slate-500">•</span>
                <span className="text-slate-400 text-sm">Joined {new Date(userProfile.joinDate).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg flex items-center gap-2 transition-colors"
          >
            <Edit3 size={16} />
            {isEditing ? 'Cancel' : 'Edit Profile'}
          </button>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800/50 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <TrendingUp className="text-green-400" size={24} />
            <div>
              <div className="text-2xl font-bold text-green-400">{tradingStats.totalProfit.toFixed(4)}</div>
              <div className="text-sm text-slate-400">Total Profit (ETH)</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Activity className="text-blue-400" size={24} />
            <div>
              <div className="text-2xl font-bold text-blue-400">{tradingStats.totalTrades}</div>
              <div className="text-sm text-slate-400">Total Trades</div>
            </div>
