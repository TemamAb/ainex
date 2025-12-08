import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, Wallet, User, AlertCircle, CheckCircle, Shield } from 'lucide-react';
import { RegisterData } from '../../types';

interface RegisterProps {
  onRegister: (data: RegisterData) => Promise<void>;
  onSwitchToLogin: () => void;
  isLoading: boolean;
  error: string | null;
}

const Register: React.FC<RegisterProps> = ({ onRegister, onSwitchToLogin, isLoading, error }) => {
  const [formData, setFormData] = useState<RegisterData>({
    email: '',
    username: '',
    firstName: '',
    lastName: '',
    password: '',
    walletAddress: '',
    riskTolerance: 'MEDIUM',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [walletConnected, setWalletConnected] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      await onRegister(formData);
    } catch (err) {
      // Error is handled by parent component
    }
  };

  const validateForm = () => {
    if (!formData.email || !formData.username || !formData.firstName || !formData.lastName || !formData.password || !formData.walletAddress) {
      return false;
    }
    if (formData.password !== confirmPassword) {
      return false;
    }
    if (!acceptedTerms) {
      return false;
    }
    return true;
  };

  const handleWalletConnect = async () => {
    try {
      // TODO: Implement real wallet connection
      // For now, simulate connection
      const mockAddress = '0x' + Math.random().toString(36).substr(2, 40);
      setFormData(prev => ({ ...prev, walletAddress: mockAddress }));
      setWalletConnected(true);
    } catch (err) {
      console.error('Wallet connection failed:', err);
    }
  };

  const handleInputChange = (field: keyof RegisterData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const getPasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  const passwordStrength = getPasswordStrength(formData.password);
  const passwordStrengthText = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'][passwordStrength - 1] || '';
  const passwordStrengthColor = ['text-red-400', 'text-orange-400', 'text-yellow-400', 'text-blue-400', 'text-green-400'][passwordStrength - 1] || '';

  return (
    <div className="min-h-screen bg-[#0b0c0e] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Join AINEX</h1>
          <p className="text-slate-400">Create your account to start trading</p>
        </div>

        {/* Register Form */}
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  First Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 w-4 h-4" />
                  <input
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => handleInputChange('firstName', e.target.value)}
                    className="w-full pl-9 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    placeholder="John"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Last Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 w-4 h-4" />
                  <input
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => handleInputChange('lastName', e.target.value)}
                    className="w-full pl-9 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    placeholder="Doe"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => handleInputChange('username', e.target.value)}
                  className="w-full pl-9 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  placeholder="johndoe_trader"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full pl-9 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  placeholder="john.doe@example.com"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className="w-full pl-9 pr-12 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  placeholder="Create a strong password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-500 hover:text-slate-400"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {formData.password && (
                <div className="mt-2">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          passwordStrength <= 2 ? 'bg-red-500' :
                          passwordStrength <= 3 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${(passwordStrength / 5) * 100}%` }}
                      />
                    </div>
                    <span className={`text-xs ${passwordStrengthColor}`}>
                      {passwordStrengthText}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-9 pr-12 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  placeholder="Confirm your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-500 hover:text-slate-400"
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {confirmPassword && formData.password !== confirmPassword && (
                <p className="mt-1 text-sm text-red-400">Passwords do not match</p>
              )}
            </div>

            {/* Risk Tolerance */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Risk Tolerance
              </label>
              <select
                value={formData.riskTolerance}
                onChange={(e) => handleInputChange('riskTolerance', e.target.value as 'LOW' | 'MEDIUM' | 'HIGH')}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                <option value="LOW">Low - Conservative trading</option>
                <option value="MEDIUM">Medium - Balanced approach</option>
                <option value="HIGH">High - Aggressive trading</option>
              </select>
            </div>

            {/* Wallet Connection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Wallet Address
              </label>
              <div className="space-y-3">
                <div className="relative">
                  <Wallet className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 w-4 h-4" />
                  <input
                    type="text"
                    value={formData.walletAddress}
                    onChange={(e) => handleInputChange('walletAddress', e.target.value)}
                    className="w-full pl-9 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono text-sm"
                    placeholder="0x..."
                    required
                  />
                </div>
                <button
                  type="button"
                  onClick={handleWalletConnect}
                  className={`w-full flex items-center justify-center gap-3 py-2 px-4 rounded-lg border transition-colors ${
                    walletConnected
                      ? 'bg-green-600/20 border-green-500 text-green-400'
                      : 'bg-slate-900/50 border-slate-600 text-slate-300 hover:border-slate-500'
                  }`}
                >
                  <Wallet size={16} />
                  {walletConnected ? (
                    <>
                      <CheckCircle size={14} />
                      Wallet Connected
                    </>
                  ) : (
                    'Connect Wallet'
                  )}
                </button>
              </div>
            </div>

            {/* Terms and Conditions */}
            <div>
              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  className="mt-1 w-4 h-4 bg-slate-900 border-slate-600 rounded focus:ring-blue-500 focus:ring-2"
                  required
                />
                <span className="text-sm text-slate-400">
                  I agree to the{' '}
                  <button type="button" className="text-blue-400 hover:text-blue-300 underline">
                    Terms of Service
                  </button>
                  {' '}and{' '}
                  <button type="button" className="text-blue-400 hover:text-blue-300 underline">
                    Privacy Policy
                  </button>
                </span>
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                <AlertCircle size={16} className="text-red-400" />
                <span className="text-sm text-red-400">{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || !validateForm()}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  <Shield size={18} />
                  Create Account
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <span className="text-slate-400">Already have an account? </span>
            <button
              onClick={onSwitchToLogin}
              className="text-blue-400 hover:text-blue-300 font-medium"
            >
              Sign in
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-slate-500">
          <p>Your account will be reviewed by our admin team before activation</p>
        </div>
      </div>
    </div>
  );
};

export default Register;
