import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginData, RegisterData } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('ainex_token');
        if (token) {
          // TODO: Validate token with backend
          // For now, simulate authenticated user
          const mockUser: User = {
            id: '1',
            email: 'user@ainex.com',
            username: 'ainex_user',
            firstName: 'AINEX',
            lastName: 'User',
            walletAddress: '0x1234567890abcdef',
            riskTolerance: 'HIGH',
            isActive: true,
            createdAt: new Date().toISOString()
          };
          setUser(mockUser);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (data: LoginData) => {
    setIsLoading(true);
    try {
      // TODO: Implement actual login API call
      // For now, simulate login
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockUser: User = {
        id: '1',
        email: data.email,
        username: 'ainex_user',
        firstName: 'AINEX',
        lastName: 'User',
        walletAddress: '0x1234567890abcdef',
        riskTolerance: 'HIGH',
        isActive: true,
        createdAt: new Date().toISOString()
      };

      setUser(mockUser);
      localStorage.setItem('ainex_token', 'mock_token');
    } catch (error) {
      throw new Error('Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    setIsLoading(true);
    try {
      // TODO: Implement actual register API call
      // For now, simulate registration
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockUser: User = {
        id: '1',
        email: data.email,
        username: data.username,
        firstName: data.firstName,
        lastName: data.lastName,
        walletAddress: data.walletAddress,
        riskTolerance: data.riskTolerance,
        isActive: false, // Requires admin approval
        createdAt: new Date().toISOString()
      };

      setUser(mockUser);
      localStorage.setItem('ainex_token', 'mock_token');
    } catch (error) {
      throw new Error('Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('ainex_token');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export { AuthContext };
