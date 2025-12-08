import { User, UserWallet, UserTradingStats, UserSecuritySettings, UserStatus } from '../types';

// Mock user database (in production, this would be a real database)
const USERS_STORAGE_KEY = 'ainex_users_db';
const PENDING_USERS_KEY = 'ainex_pending_users';

class UserService {
  private users: Map<string, User> = new Map();
  private pendingUsers: Map<string, User> = new Map();

  constructor() {
    this.loadFromStorage();
  }

  private loadFromStorage() {
    try {
      const usersData = localStorage.getItem(USERS_STORAGE_KEY);
      const pendingData = localStorage.getItem(PENDING_USERS_KEY);

      if (usersData) {
        const users = JSON.parse(usersData);
        this.users = new Map(Object.entries(users));
      }

      if (pendingData) {
        const pending = JSON.parse(pendingData);
        this.pendingUsers = new Map(Object.entries(pending));
      }
    } catch (error) {
      console.error('Error loading user data from storage:', error);
    }
  }

  private saveToStorage() {
    try {
      localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(Object.fromEntries(this.users)));
      localStorage.setItem(PENDING_USERS_KEY, JSON.stringify(Object.fromEntries(this.pendingUsers)));
    } catch (error) {
      console.error('Error saving user data to storage:', error);
    }
  }

  // User CRUD operations
  async createUser(userData: Omit<User, 'id' | 'joinDate' | 'lastLogin'>): Promise<User> {
    const user: User = {
      ...userData,
      id: 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      joinDate: new Date().toISOString(),
      lastLogin: new Date().toISOString(),
    };

    this.users.set(user.id, user);
    this.saveToStorage();
    return user;
  }

  async getUserById(id: string): Promise<User | null> {
    return this.users.get(id) || null;
  }

  async getUserByEmail(email: string): Promise<User | null> {
    for (const user of this.users.values()) {
      if (user.email === email) {
        return user;
      }
    }
    return null;
  }

  async getUserByWallet(walletAddress: string): Promise<User | null> {
    for (const user of this.users.values()) {
      if (user.walletAddress === walletAddress) {
        return user;
      }
    }
    return null;
  }

  async updateUser(id: string, updates: Partial<User>): Promise<User | null> {
    const user = this.users.get(id);
    if (!user) return null;

    const updatedUser = { ...user, ...updates };
    this.users.set(id, updatedUser);
    this.saveToStorage();
    return updatedUser;
  }

  async deleteUser(id: string): Promise<boolean> {
    const deleted = this.users.delete(id);
    if (deleted) {
      this.saveToStorage();
    }
    return deleted;
  }

  // Pending users (for approval workflow)
  async createPendingUser(userData: Omit<User, 'id' | 'joinDate' | 'lastLogin'>): Promise<User> {
    const user: User = {
      ...userData,
      id: 'pending_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      joinDate: new Date().toISOString(),
      lastLogin: new Date().toISOString(),
    };

    this.pendingUsers.set(user.id, user);
    this.saveToStorage();
    return user;
  }

  async getPendingUsers(): Promise<User[]> {
    return Array.from(this.pendingUsers.values());
  }

  async approveUser(id: string, adminId: string): Promise<User | null> {
    const pendingUser = this.pendingUsers.get(id);
    if (!pendingUser) return null;

    const approvedUser: User = {
      ...pendingUser,
      status: 'ACTIVE',
      approvedBy: adminId,
      approvedAt: new Date().toISOString(),
    };

    this.users.set(id, approvedUser);
    this.pendingUsers.delete(id);
    this.saveToStorage();

    // TODO: Send approval email notification
    console.log(`User ${approvedUser.email} approved by admin ${adminId}`);

    return approvedUser;
  }

  async rejectUser(id: string, reason: string, adminId: string): Promise<boolean> {
    const pendingUser = this.pendingUsers.get(id);
    if (!pendingUser) return false;

    const rejectedUser: User = {
      ...pendingUser,
      status: 'REJECTED',
      rejectionReason: reason,
    };

    this.users.set(id, rejectedUser);
    this.pendingUsers.delete(id);
    this.saveToStorage();

    // TODO: Send rejection email notification
    console.log(`User ${rejectedUser.email} rejected by admin ${adminId}. Reason: ${reason}`);

    return true;
  }

  // User statistics and data
  async getUserTradingStats(userId: string): Promise<UserTradingStats | null> {
    // TODO: Implement real trading stats retrieval
    // For now, return mock data
    return {
      totalTrades: 0,
      successfulTrades: 0,
      totalProfit: 0,
      winRate: 0,
      avgProfitPerTrade: 0,
      bestTrade: 0,
      worstTrade: 0,
      currentStreak: 0,
      lastUpdated: new Date().toISOString(),
    };
  }

  async updateUserTradingStats(userId: string, stats: Partial<UserTradingStats>): Promise<boolean> {
    // TODO: Implement real stats update
    console.log('Updating trading stats for user:', userId, stats);
    return true;
  }

  async getUserSecuritySettings(userId: string): Promise<UserSecuritySettings | null> {
    // TODO: Implement real security settings retrieval
    return {
      twoFactorEnabled: false,
      emailNotifications: true,
      tradeNotifications: true,
      securityAlerts: true,
      sessionTimeout: 30,
      ipWhitelist: [],
    };
  }

  async updateUserSecuritySettings(userId: string, settings: Partial<UserSecuritySettings>): Promise<boolean> {
    // TODO: Implement real security settings update
    console.log('Updating security settings for user:', userId, settings);
    return true;
  }

  // Admin functions
  async getAllUsers(): Promise<User[]> {
    return Array.from(this.users.values());
  }

  async getUsersByStatus(status: UserStatus): Promise<User[]> {
    return Array.from(this.users.values()).filter(user => user.status === status);
  }

  async getUsersByRole(role: 'USER' | 'ADMIN'): Promise<User[]> {
    return Array.from(this.users.values()).filter(user => user.role === role);
  }

  // Authentication helpers
  async validateCredentials(email: string, password: string): Promise<User | null> {
    // TODO: Implement real password validation
    // For now, just check if user exists
    return this.getUserByEmail(email);
  }

  async updateLastLogin(userId: string): Promise<void> {
    const user = await this.getUserById(userId);
    if (user) {
      await this.updateUser(userId, { lastLogin: new Date().toISOString() });
    }
  }

  // Utility functions
  async isWalletConnected(userId: string, walletAddress: string): Promise<boolean> {
    const user = await this.getUserById(userId);
    return user?.walletAddress === walletAddress;
  }

  async isEmailVerified(userId: string): Promise<boolean> {
    const user = await this.getUserById(userId);
    return user?.isEmailVerified || false;
  }

  async verifyEmail(userId: string): Promise<boolean> {
    return this.updateUser(userId, { isEmailVerified: true }) !== null;
  }
}

// Export singleton instance
export const userService = new UserService();
