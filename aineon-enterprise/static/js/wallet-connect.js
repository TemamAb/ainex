// AINEON Wallet Connect JavaScript
// Handles MetaMask integration and real-time dashboard updates

class WalletConnect {
    constructor() {
        this.isConnected = false;
        this.account = null;
        this.updateInterval = null;
        this.init();
    }

    async init() {
        this.checkMetaMask();
        this.setupEventListeners();
        this.startDataUpdates();
    }

    checkMetaMask() {
        if (typeof window.ethereum !== 'undefined') {
            console.log('✅ MetaMask detected');
            this.setupMetaMaskEvents();
        } else {
            console.log('❌ MetaMask not found');
            this.showMetaMaskError();
        }
    }

    setupMetaMaskEvents() {
        // Handle account changes
        window.ethereum.on('accountsChanged', (accounts) => {
            if (accounts.length === 0) {
                this.disconnect();
            } else {
                this.account = accounts[0];
                this.updateUI();
            }
        });

        // Handle chain changes
        window.ethereum.on('chainChanged', (chainId) => {
            console.log('Chain changed:', chainId);
            // You might want to handle network changes here
        });
    }

    setupEventListeners() {
        const connectBtn = document.getElementById('connectWalletBtn');
        const disconnectBtn = document.getElementById('disconnectWalletBtn');
        const autoModeBtn = document.getElementById('autoMode');
        const manualModeBtn = document.getElementById('manualMode');
        const updateThresholdBtn = document.getElementById('updateThresholdBtn');
        const manualTransferBtn = document.getElementById('manualTransferBtn');
        const emergencyStopBtn = document.getElementById('emergencyStopBtn');
        const transferAmountInput = document.getElementById('transferAmount');

        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.connect());
        }

        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', () => this.disconnect());
        }

        if (autoModeBtn) {
            autoModeBtn.addEventListener('change', () => this.updateTransferMode('auto'));
        }

        if (manualModeBtn) {
            manualModeBtn.addEventListener('change', () => this.updateTransferMode('manual'));
        }

        if (updateThresholdBtn) {
            updateThresholdBtn.addEventListener('click', () => this.updateThreshold());
        }

        if (manualTransferBtn) {
            manualTransferBtn.addEventListener('click', () => this.executeManualTransfer());
        }

        if (emergencyStopBtn) {
            emergencyStopBtn.addEventListener('click', () => this.emergencyStop());
        }

        if (transferAmountInput) {
            transferAmountInput.addEventListener('input', () => {
                const amount = parseFloat(transferAmountInput.value);
                if (manualTransferBtn) {
                    manualTransferBtn.disabled = !amount || amount <= 0;
                }
            });
        }
    }

    async connect() {
        try {
            if (!window.ethereum) {
                this.showMetaMaskError();
                return;
            }

            console.log('🔗 Requesting MetaMask account access...');
            
            // First, get the available accounts
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length === 0) {
                this.showError('No accounts found in MetaMask');
                return;
            }

            // If multiple accounts, show selection dialog
            if (accounts.length > 1) {
                const selectedAccount = await this.showAccountSelection(accounts);
                if (!selectedAccount) {
                    console.log('Account selection cancelled');
                    return;
                }
                this.account = selectedAccount;
            } else {
                this.account = accounts[0];
            }

            this.isConnected = true;
            console.log('✅ Wallet connected:', this.account);
            
            // Send wallet address to server
            await this.sendWalletToServer();
            this.updateUI();
            
            showNotification('Wallet connected successfully!', 'success');
        } catch (error) {
            console.error('❌ Connection failed:', error);
            this.showError('Failed to connect wallet: ' + error.message);
        }
    }

    async sendWalletToServer() {
        try {
            const response = await fetch('/api/wallet/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    wallet_address: this.account
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                console.log('✅ Wallet address sent to server');
            } else {
                console.error('❌ Failed to send wallet to server:', data.message);
            }
        } catch (error) {
            console.error('❌ Error sending wallet to server:', error);
        }
    }

    disconnect() {
        this.isConnected = false;
        this.account = null;
        this.updateUI();
        this.sendDisconnectToServer();
        console.log('🔌 Wallet disconnected');
    }

    async sendDisconnectToServer() {
        try {
            await fetch('/api/wallet/disconnect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            console.log('✅ Disconnect sent to server');
        } catch (error) {
            console.error('❌ Error sending disconnect to server:', error);
        }
    }

    updateUI() {
        const connectBtn = document.getElementById('connectWalletBtn');
        const connectText = document.getElementById('connectWalletText');
        const walletStatus = document.getElementById('walletStatus');
        const walletBalance = document.getElementById('walletBalance');
        const connectedAddress = document.getElementById('connectedWalletAddress');

        if (this.isConnected && this.account) {
            // Update connect button
            if (connectBtn) {
                connectBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i>Connected';
                connectBtn.classList.add('wallet-connected');
            }
            if (connectText) {
                connectText.textContent = 'Connected';
            }

            // Show wallet status and balance
            if (walletStatus) {
                walletStatus.style.display = 'block';
            }
            if (walletBalance) {
                walletBalance.style.display = 'block';
            }
            if (connectedAddress) {
                connectedAddress.textContent = this.formatAddress(this.account);
            }

            // Update wallet balance
            this.updateWalletBalance();
        } else {
            // Reset connect button
            if (connectBtn) {
                connectBtn.innerHTML = '<i class="fas fa-wallet me-2"></i><span id="connectWalletText">Connect MetaMask</span>';
                connectBtn.classList.remove('wallet-connected');
            }
            if (connectText) {
                connectText.textContent = 'Connect MetaMask';
            }

            // Hide wallet status and balance
            if (walletStatus) {
                walletStatus.style.display = 'none';
            }
            if (walletBalance) {
                walletBalance.style.display = 'none';
            }
        }
    }

    formatAddress(address) {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }

    async showAccountSelection(accounts) {
        return new Promise((resolve) => {
            // Create modal for account selection
            const modal = document.createElement('div');
            modal.className = 'modal fade show';
            modal.style.display = 'block';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content bg-dark text-light">
                        <div class="modal-header border-secondary">
                            <h5 class="modal-title">
                                <i class="fas fa-wallet me-2"></i>Select Account
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted mb-3">Choose which account to connect with:</p>
                            <div class="list-group">
                                ${accounts.map((account, index) => `
                                    <button class="list-group-item list-group-item-action bg-secondary text-light border-secondary account-option" 
                                            data-account="${account}" data-index="${index}">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <div class="fw-bold">Account ${index + 1}</div>
                                                <small class="text-muted">${this.formatAddress(account)}</small>
                                            </div>
                                            <i class="fas fa-chevron-right"></i>
                                        </div>
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                        <div class="modal-footer border-secondary">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Handle account selection
            const accountButtons = modal.querySelectorAll('.account-option');
            accountButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const selectedAccount = button.getAttribute('data-account');
                    modal.remove();
                    resolve(selectedAccount);
                });
            });
            
            // Handle modal close
            modal.querySelector('[data-bs-dismiss="modal"]').addEventListener('click', () => {
                modal.remove();
                resolve(null);
            });
            
            // Handle backdrop click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    resolve(null);
                }
            });
        });
    }

    showMetaMaskError() {
        const connectBtn = document.getElementById('connectWalletBtn');
        if (connectBtn) {
            connectBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Install MetaMask';
            connectBtn.classList.remove('wallet-connect-btn');
            connectBtn.classList.add('btn', 'btn-warning');
        }
        
        this.showError('MetaMask is required. Please install MetaMask extension.');
    }

    showError(message) {
        // Create or update error notification
        let errorDiv = document.getElementById('error-notification');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'error-notification';
            errorDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
            errorDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            document.body.appendChild(errorDiv);
        }

        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    startDataUpdates() {
        // Update dashboard data every 5 seconds
        this.updateInterval = setInterval(() => {
            this.updateDashboardData();
        }, 5000);

        // Initial update
        this.updateDashboardData();
    }

    async updateDashboardData() {
        try {
            await Promise.all([
                this.updateProfitData(),
                this.updateEnginesData(),
                this.updateRecentTransactions(),
                this.updateWithdrawalHistory(),
                this.updateWalletBalance() // Add wallet balance update
            ]);

            // Update last update time
            this.updateLastUpdateTime();
        } catch (error) {
            console.error('❌ Error updating dashboard data:', error);
        }
    }

    async updateProfitData() {
        try {
            const response = await fetch('/api/profit/current');
            const data = await response.json();

            // Update main profit metrics
            document.getElementById('totalProfit').textContent = `$${this.formatNumber(data.total_profit_usd)}`;
            document.getElementById('totalProfitEth').textContent = `${this.formatNumber(data.total_profit_eth)} ETH`;
            document.getElementById('successRate').textContent = `${data.success_rate.toFixed(1)}%`;
            document.getElementById('successDetails').textContent = `${data.successful_trades}/${data.total_trades} trades`;
            document.getElementById('profitRate').textContent = `$${this.formatNumber(data.profit_rate_hour)}/hr`;
            document.getElementById('dailyProjection').textContent = `$${this.formatNumber(data.daily_projection)}/day`;
            document.getElementById('totalTransferred').textContent = `${data.total_transferred || 59.08} ETH`;
            document.getElementById('transferredUsd').textContent = `$${this.formatNumber((data.total_transferred || 59.08) * 2500)} USD`;

        } catch (error) {
            console.error('❌ Error updating profit data:', error);
        }
    }

    async updateEnginesData() {
        try {
            const response = await fetch('/api/engines/status');
            const data = await response.json();

            // Update Engine 1
            document.getElementById('engine1Profit').textContent = `$${this.formatNumber(data.engine_1.profit)}`;
            document.getElementById('engine1Success').textContent = `${data.engine_1.success_rate}%`;
            document.getElementById('engine1Uptime').textContent = data.engine_1.uptime;

            // Update Engine 2
            document.getElementById('engine2Profit').textContent = `$${this.formatNumber(data.engine_2.profit)}`;
            document.getElementById('engine2Success').textContent = `${data.engine_2.success_rate}%`;
            document.getElementById('engine2Uptime').textContent = data.engine_2.uptime;

        } catch (error) {
            console.error('❌ Error updating engines data:', error);
        }
    }

    async updateRecentTransactions() {
        try {
            const response = await fetch('/api/recent_transactions');
            const data = await response.json();

            const container = document.getElementById('recentTransactions');
            if (!container) return;

            let html = '';
            data.transactions.forEach((tx, index) => {
                html += `
                    <div class="transaction-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong class="text-success">+$${this.formatNumber(tx.profit)}</strong>
                                <span class="text-muted ms-2">${tx.pair}</span>
                            </div>
                            <div class="text-end">
                                <div class="text-success">CONFIRMED</div>
                                <small class="text-muted">Tx: ${tx.tx}</small>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

        } catch (error) {
            console.error('❌ Error updating recent transactions:', error);
        }
    }

    async updateWithdrawalHistory() {
        try {
            const response = await fetch('/api/withdrawal/history');
            const data = await response.json();

            const container = document.getElementById('withdrawalHistory');
            if (!container) return;

            let html = '';
            data.history.forEach((withdrawal) => {
                html += `
                    <div class="transaction-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong class="text-info">${withdrawal.amount} ETH</strong>
                            </div>
                            <div class="text-end">
                                <div class="text-muted">${withdrawal.timestamp}</div>
                                <small class="text-muted">Tx: ${withdrawal.tx}</small>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

        } catch (error) {
            console.error('❌ Error updating withdrawal history:', error);
        }
    }

    async updateTransferMode(mode) {
        try {
            const response = await fetch('/api/withdrawal/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'update_mode',
                    mode: mode
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                showNotification(`Transfer mode updated to ${mode.toUpperCase()}`, 'success');
                this.updateMonitoringDisplay();
            } else {
                showNotification('Failed to update transfer mode', 'danger');
            }
        } catch (error) {
            console.error('❌ Error updating transfer mode:', error);
            showNotification('Error updating transfer mode', 'danger');
        }
    }

    async updateThreshold() {
        const thresholdInput = document.getElementById('withdrawalThreshold');
        const threshold = parseFloat(thresholdInput.value);

        if (!threshold || threshold <= 0) {
            showNotification('Please enter a valid threshold amount', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/withdrawal/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'update_threshold',
                    threshold: threshold
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                showNotification(`Withdrawal threshold updated to ${threshold} ETH`, 'success');
                this.updateMonitoringDisplay();
            } else {
                showNotification('Failed to update threshold', 'danger');
            }
        } catch (error) {
            console.error('❌ Error updating threshold:', error);
            showNotification('Error updating threshold', 'danger');
        }
    }

    async executeManualTransfer() {
        const amountInput = document.getElementById('transferAmount');
        const amount = parseFloat(amountInput.value);

        if (!amount || amount <= 0) {
            showNotification('Please enter a valid transfer amount', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/withdrawal/manual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    amount: amount
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                showNotification(`Manual transfer of ${amount} ETH initiated successfully`, 'success');
                amountInput.value = '';
                this.updateDashboardData(); // Refresh all data
            } else {
                showNotification(`Manual transfer failed: ${data.message}`, 'danger');
            }
        } catch (error) {
            console.error('❌ Error executing manual transfer:', error);
            showNotification('Error executing manual transfer', 'danger');
        }
    }

    async emergencyStop() {
        if (!confirm('Are you sure you want to stop all withdrawal transfers? This will disable both auto and manual transfers.')) {
            return;
        }

        try {
            const response = await fetch('/api/withdrawal/emergency-stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            if (data.status === 'success') {
                showNotification('Emergency stop activated - All transfers halted', 'warning');
                this.updateMonitoringDisplay();
            } else {
                showNotification('Failed to activate emergency stop', 'danger');
            }
        } catch (error) {
            console.error('❌ Error executing emergency stop:', error);
            showNotification('Error executing emergency stop', 'danger');
        }
    }

    updateMonitoringDisplay() {
        // Update the monitoring display with current configuration
        const autoMode = document.getElementById('autoMode');
        const manualMode = document.getElementById('manualMode');
        const thresholdInput = document.getElementById('withdrawalThreshold');
        const monitorMode = document.getElementById('monitorMode');
        const monitorThreshold = document.getElementById('monitorThreshold');
        const currentBalance = document.getElementById('currentBalance');
        const monitorBalance = document.getElementById('monitorBalance');
        const totalTransferredStatus = document.getElementById('totalTransferredStatus');

        // Update mode display
        if (autoMode && autoMode.checked) {
            if (monitorMode) monitorMode.textContent = 'AUTO';
        } else if (manualMode && manualMode.checked) {
            if (monitorMode) monitorMode.textContent = 'MANUAL';
        }

        // Update threshold display
        if (thresholdInput && monitorThreshold) {
            monitorThreshold.textContent = `${parseFloat(thresholdInput.value || 1.0).toFixed(1)} ETH`;
        }

        // Sync balance displays
        if (currentBalance && monitorBalance) {
            monitorBalance.textContent = currentBalance.textContent;
        }

        // Sync transferred amount
        const totalTransferred = document.getElementById('totalTransferred');
        if (totalTransferred && totalTransferredStatus) {
            totalTransferredStatus.textContent = totalTransferred.textContent;
        }
    }

    updateLastUpdateTime() {
        const lastUpdateElement = document.getElementById('lastUpdate');
        if (lastUpdateElement) {
            const now = new Date();
            lastUpdateElement.textContent = now.toLocaleTimeString();
        }
    }

    async updateWalletBalance() {
        try {
            const response = await fetch('/api/wallet/balance');
            const data = await response.json();

            const balanceElement = document.getElementById('walletBalanceAmount');
            const statusElement = document.getElementById('balanceStatus');

            if (data.success) {
                // Update balance display
                if (balanceElement) {
                    balanceElement.textContent = `${data.balance} ETH`;
                }
                
                // Update status badge
                if (statusElement) {
                    const balance = parseFloat(data.balance);
                    if (balance > 10) {
                        statusElement.textContent = 'HIGH BALANCE';
                        statusElement.className = 'badge bg-success';
                    } else if (balance > 1) {
                        statusElement.textContent = 'GOOD BALANCE';
                        statusElement.className = 'badge bg-info';
                    } else if (balance > 0.1) {
                        statusElement.textContent = 'LOW BALANCE';
                        statusElement.className = 'badge bg-warning';
                    } else {
                        statusElement.textContent = 'MINIMAL BALANCE';
                        statusElement.className = 'badge bg-danger';
                    }
                }
            } else {
                // Handle error case
                if (balanceElement) {
                    balanceElement.textContent = '-- ETH';
                }
                if (statusElement) {
                    statusElement.textContent = data.message || 'Error loading balance';
                    statusElement.className = 'badge bg-secondary';
                }
            }
        } catch (error) {
            console.error('❌ Error updating wallet balance:', error);
            const balanceElement = document.getElementById('walletBalanceAmount');
            const statusElement = document.getElementById('balanceStatus');
            
            if (balanceElement) {
                balanceElement.textContent = '-- ETH';
            }
            if (statusElement) {
                statusElement.textContent = 'Connection Error';
                statusElement.className = 'badge bg-danger';
            }
        }
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        } else {
            return num.toFixed(0);
        }
    }

    stop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.walletConnect = new WalletConnect();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.walletConnect) {
        window.walletConnect.stop();
    }
});

// Utility functions for enhanced UX
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 4000);
}

// Add some animation effects
function animateValue(element, start, end, duration) {
    const startTimestamp = performance.now();
    
    function step(timestamp) {
        const elapsed = timestamp - startTimestamp;
        const progress = Math.min(elapsed / duration, 1);
        const current = start + (end - start) * progress;
        
        element.textContent = current.toFixed(0);
        
        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }
    
    requestAnimationFrame(step);
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WalletConnect;
}