/**
 * AINEON Enterprise - Institutional Dashboard Core
 * Chief Architect: Non-invasive institutional overlay system
 * Phase 3 Implementation
 */

class InstitutionalDashboard {
    constructor() {
        this.modules = {
            compliance: null,
            team: null,
            reporting: null,
            risk: null
        };
        
        this.currentUser = null;
        this.engineAPI = null;
        this.config = {};
        
        this.init();
    }
    
    async init() {
        console.log('íº€ Initializing Institutional Dashboard...');
        
        try {
            // Load configuration
            await this.loadConfig();
            
            // Connect to existing engine API
            this.connectToEngine();
            
            // Initialize user session
            await this.initUserSession();
            
            // Setup UI
            this.setupUI();
            
            // Initialize modules
            await this.initModules();
            
            // Start background services
            this.startBackgroundServices();
            
            console.log('âœ… Institutional Dashboard initialized successfully');
            
        } catch (error) {
            console.error('âŒ Failed to initialize Institutional Dashboard:', error);
            this.showError('Failed to initialize dashboard. Please refresh the page.');
        }
    }
    
    async loadConfig() {
        // Load institutional configuration from localStorage or default
        const savedConfig = localStorage.getItem('aineon-institutional-config');
        
        if (savedConfig) {
            this.config = JSON.parse(savedConfig);
        } else {
            // Default configuration
            this.config = {
                compliance: {
                    enabled: true,
                    providers: ['chainalysis', 'elliptic'],
                    autoScreen: true,
                    riskThreshold: 70
                },
                team: {
                    enabled: true,
                    maxUsers: 50,
                    defaultRole: 'VIEWER'
                },
                reporting: {
                    enabled: true,
                    autoGenerate: false,
                    retentionDays: 365
                },
                risk: {
                    enabled: true,
                    monitoringInterval: 30000, // 30 seconds
                    alertThresholds: {
                        portfolio: 0.05, // 5%
                        individual: 0.10  // 10%
                    }
                }
            };
            this.saveConfig();
        }
    }
    
    saveConfig() {
        localStorage.setItem('aineon-institutional-config', JSON.stringify(this.config));
    }
    
    connectToEngine() {
        // Connect to existing Phase 1/2 engine API
        if (window.engineAPI) {
            this.engineAPI = window.engineAPI;
            console.log('í´— Connected to existing engine API');
        } else {
            // Fallback to direct API calls
            this.engineAPI = this.createFallbackAPI();
            console.log('âš ï¸ Using fallback API adapter');
        }
    }
    
    createFallbackAPI() {
        // Create a fallback API adapter for testing
        return {
            getTransactions: async () => {
                return await this.fetchFromEngine('/api/transactions');
            },
            getWalletInfo: async (address) => {
                return await this.fetchFromEngine(`/api/wallet/${address}`);
            },
            getFlashLoans: async () => {
                return await this.fetchFromEngine('/api/flash-loans');
            },
            getMarketData: async () => {
                return await this.fetchFromEngine('/api/market-data');
            }
        };
    }
    
    async fetchFromEngine(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn(`Failed to fetch from ${endpoint}:`, error);
            return null;
        }
    }
    
    async initUserSession() {
        // Get current user from localStorage or create default
        const savedUser = localStorage.getItem('aineon-current-user');
        
        if (savedUser) {
            this.currentUser = JSON.parse(savedUser);
        } else {
            // Default institutional user
            this.currentUser = {
                id: 'user_' + Math.random().toString(36).substr(2, 9),
                name: 'Institutional User',
                email: 'user@ainex.enterprise',
                role: 'ADMIN',
                permissions: ['read', 'write', 'execute', 'approve', 'configure'],
                lastLogin: new Date().toISOString()
            };
            localStorage.setItem('aineon-current-user', JSON.stringify(this.currentUser));
        }
        
        // Update UI
        this.updateUserDisplay();
    }
    
    updateUserDisplay() {
        const userElement = document.getElementById('current-user');
        if (userElement && this.currentUser) {
            userElement.textContent = `${this.currentUser.name} (${this.currentUser.role})`;
        }
    }
    
    setupUI() {
        // Setup navigation
        this.setupNavigation();
        
        // Setup module switching
        this.setupModuleSwitching();
        
        // Setup responsive behavior
        this.setupResponsiveBehavior();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    setupNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn');
        navButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const module = e.currentTarget.dataset.module;
                this.switchModule(module);
            });
        });
    }
    
    switchModule(moduleName) {
        // Update active nav button
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.module === moduleName);
        });
        
        // Show selected module, hide others
        document.querySelectorAll('.institutional-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `${moduleName}-module`);
        });
        
        // Initialize module if not already loaded
        this.initializeModule(moduleName);
        
        // Track module view
        this.trackAnalytics('module_view', { module: moduleName });
    }
    
    async initializeModule(moduleName) {
        if (this.modules[moduleName]) return;
        
        switch (moduleName) {
            case 'compliance':
                const { ComplianceModule } = await import('./compliance-engine.js');
                this.modules.compliance = new ComplianceModule(this);
                break;
                
            case 'team':
                const { TeamManager } = await import('./team-manager.js');
                this.modules.team = new TeamManager(this);
                break;
                
            case 'reporting':
                const { ReportingEngine } = await import('./reporting-engine.js');
                this.modules.reporting = new ReportingEngine(this);
                break;
                
            case 'risk':
                const { RiskManager } = await import('./risk-manager.js');
                this.modules.risk = new RiskManager(this);
                break;
        }
    }
    
    async initModules() {
        // Initialize all modules (can be lazy loaded)
        for (const moduleName of Object.keys(this.modules)) {
            await this.initializeModule(moduleName);
        }
    }
    
    setupResponsiveBehavior() {
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => this.handleResize(), 250);
        });
    }
    
    handleResize() {
        const width = window.innerWidth;
        
        // Adjust layout for mobile
        if (width < 768) {
            document.body.classList.add('mobile-view');
        } else {
            document.body.classList.remove('mobile-view');
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + 1-4 for module switching
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case '1':
                        e.preventDefault();
                        this.switchModule('compliance');
                        break;
                    case '2':
                        e.preventDefault();
                        this.switchModule('team');
                        break;
                    case '3':
                        e.preventDefault();
                        this.switchModule('reporting');
                        break;
                    case '4':
                        e.preventDefault();
                        this.switchModule('risk');
                        break;
                }
            }
        });
    }
    
    startBackgroundServices() {
        // Start compliance monitoring if enabled
        if (this.config.compliance.enabled && this.config.compliance.autoScreen) {
            this.startComplianceMonitoring();
        }
        
        // Start risk monitoring if enabled
        if (this.config.risk.enabled) {
            this.startRiskMonitoring();
        }
        
        // Start periodic data sync
        this.startDataSync();
    }
    
    startComplianceMonitoring() {
        setInterval(async () => {
            if (this.modules.compliance) {
                await this.modules.compliance.monitorTransactions();
            }
        }, 60000); // Every minute
    }
    
    startRiskMonitoring() {
        setInterval(async () => {
            if (this.modules.risk) {
                await this.modules.risk.updateRiskMetrics();
            }
        }, this.config.risk.monitoringInterval);
    }
    
    startDataSync() {
        setInterval(async () => {
            await this.syncWithEngine();
        }, 30000); // Every 30 seconds
    }
    
    async syncWithEngine() {
        try {
            // Sync transaction data
            const transactions = await this.engineAPI.getTransactions();
            this.storeData('transactions', transactions);
            
            // Sync market data
            const marketData = await this.engineAPI.getMarketData();
            this.storeData('market-data', marketData);
            
            console.log('í´„ Data sync completed');
        } catch (error) {
            console.warn('Data sync failed:', error);
        }
    }
    
    storeData(key, data) {
        // Store data in IndexedDB or localStorage
        const storageKey = `aineon-${key}`;
        localStorage.setItem(storageKey, JSON.stringify({
            data,
            timestamp: Date.now()
        }));
    }
    
    getStoredData(key) {
        const storageKey = `aineon-${key}`;
        const stored = localStorage.getItem(storageKey);
        return stored ? JSON.parse(stored) : null;
    }
    
    trackAnalytics(event, data = {}) {
        // Track user interactions (anonymous)
        const analyticsData = {
            event,
            timestamp: Date.now(),
            userId: this.currentUser?.id,
            userRole: this.currentUser?.role,
            ...data
        };
        
        // Store locally
        const analyticsLog = JSON.parse(localStorage.getItem('aineon-analytics') || '[]');
        analyticsLog.push(analyticsData);
        
        // Keep only last 1000 events
        if (analyticsLog.length > 1000) {
            analyticsLog.splice(0, analyticsLog.length - 1000);
        }
        
        localStorage.setItem('aineon-analytics', JSON.stringify(analyticsLog));
        
        // Could also send to analytics service (with user consent)
        if (this.config.analyticsEnabled) {
            this.sendToAnalyticsService(analyticsData);
        }
    }
    
    sendToAnalyticsService(data) {
        // Implementation for external analytics service
        // This would require user consent per GDPR/MiCA
    }
    
    showError(message, duration = 5000) {
        // Create error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
            <button class="close-btn">&times;</button>
        `;
        
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f8d7da;
            color: #721c24;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 10001;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(errorDiv);
        
        // Add close button handler
        errorDiv.querySelector('.close-btn').onclick = () => {
            errorDiv.remove();
        };
        
        // Auto-remove after duration
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, duration);
    }
    
    showSuccess(message, duration = 3000) {
        // Create success notification
        const successDiv = document.createElement('div');
        successDiv.className = 'success-notification';
        successDiv.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
            <button class="close-btn">&times;</button>
        `;
        
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #d4edda;
            color: #155724;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 10001;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(successDiv);
        
        // Add close button handler
        successDiv.querySelector('.close-btn').onclick = () => {
            successDiv.remove();
        };
        
        // Auto-remove after duration
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, duration);
    }
    
    // Utility methods
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }
    
    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
    
    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }
    
    encryptData(data, key) {
        // Simple encryption for sensitive data (for demonstration)
        // In production, use Web Crypto API
        return btoa(JSON.stringify(data));
    }
    
    decryptData(encrypted, key) {
        try {
            return JSON.parse(atob(encrypted));
        } catch (error) {
            console.error('Decryption failed:', error);
            return null;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.institutionalDashboard = new InstitutionalDashboard();
});

// Export for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { InstitutionalDashboard };
}
