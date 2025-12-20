/**
 * AINEON Enterprise - Compliance Engine
 * Institutional Compliance Module
 * Phase 3 Implementation
 */

class ComplianceModule {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.screenings = new Map();
        this.watchlists = new Map();
        this.alerts = [];
        
        this.init();
    }
    
    async init() {
        console.log('í»¡ï¸ Initializing Compliance Module...');
        
        // Load saved screenings
        await this.loadScreenings();
        
        // Load watchlists
        await this.loadWatchlists();
        
        // Setup UI event handlers
        this.setupEventHandlers();
        
        // Initialize providers
        await this.initProviders();
        
        console.log('âœ… Compliance Module initialized');
    }
    
    async loadScreenings() {
        const saved = localStorage.getItem('aineon-compliance-screenings');
        if (saved) {
            const data = JSON.parse(saved);
            data.forEach(screening => {
                this.screenings.set(screening.wallet, screening);
            });
        }
        this.updateRecentScreeningsUI();
    }
    
    saveScreenings() {
        const screenings = Array.from(this.screenings.values());
        localStorage.setItem('aineon-compliance-screenings', JSON.stringify(screenings));
    }
    
    async loadWatchlists() {
        // Load OFAC, PEP, sanctions lists
        const lists = ['ofac', 'pep', 'eu_sanctions', 'un_sanctions'];
        
        for (const list of lists) {
            try {
                const response = await fetch(`/data/watchlists/${list}.json`);
                if (response.ok) {
                    const data = await response.json();
                    this.watchlists.set(list, new Set(data.addresses));
                }
            } catch (error) {
                console.warn(`Failed to load ${list} watchlist:`, error);
            }
        }
    }
    
    setupEventHandlers() {
        // Wallet screening button
        const screenBtn = document.getElementById('screen-wallet-btn');
        if (screenBtn) {
            screenBtn.addEventListener('click', () => this.showScreeningModal());
        }
        
        // Compliance report button
        const reportBtn = document.getElementById('compliance-report-btn');
        if (reportBtn) {
            reportBtn.addEventListener('click', () => this.generateComplianceReport());
        }
        
        // Real-time wallet input screening
        const walletInput = document.getElementById('wallet-address-input');
        if (walletInput) {
            walletInput.addEventListener('input', (e) => {
                this.debouncedScreening(e.target.value);
            });
        }
    }
    
    debouncedScreening = this.debounce((address) => {
        if (this.isValidAddress(address)) {
            this.quickScreen(address);
        }
    }, 500);
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    async initProviders() {
        // Initialize external compliance providers
        this.providers = {};
        
        // Load provider configurations
        const providerConfigs = this.dashboard.config.compliance.providers || [];
        
        for (const providerName of providerConfigs) {
            try {
                const module = await import(`../integrations/${providerName}-api.js`);
                this.providers[providerName] = new module.default();
                console.log(`âœ… Loaded compliance provider: ${providerName}`);
            } catch (error) {
                console.warn(`Failed to load provider ${providerName}:`, error);
            }
        }
    }
    
    async screenWallet(address) {
        if (!this.isValidAddress(address)) {
            throw new Error('Invalid wallet address');
        }
        
        // Check cache first
        const cached = this.screenings.get(address);
        if (cached && (Date.now() - cached.timestamp < 24 * 60 * 60 * 1000)) {
            console.log('í³Š Using cached screening result');
            return cached;
        }
        
        this.showLoadingState();
        
        try {
            // Screen with all providers
            const screeningPromises = [];
            
            // Internal watchlist screening
            screeningPromises.push(this.screenWithWatchlists(address));
            
            // External provider screenings
            for (const [name, provider] of Object.entries(this.providers)) {
                screeningPromises.push(
                    provider.screenAddress(address)
                        .then(result => ({ provider: name, result }))
                        .catch(error => ({ 
                            provider: name, 
                            result: { error: error.message } 
                        }))
                );
            }
            
            // Execute all screenings in parallel
            const results = await Promise.all(screeningPromises);
            
            // Aggregate results
            const screeningResult = this.aggregateResults(address, results);
            
            // Store result
            this.screenings.set(address, screeningResult);
            this.saveScreenings();
            
            // Update UI
            this.updateScreeningResultUI(screeningResult);
            this.updateRecentScreeningsUI();
            
            // Check for alerts
            if (screeningResult.riskScore >= this.dashboard.config.compliance.riskThreshold) {
                this.createAlert(address, screeningResult);
            }
            
            return screeningResult;
            
        } catch (error) {
            console.error('Screening failed:', error);
            this.dashboard.showError('Failed to screen wallet address');
            throw error;
        } finally {
            this.hideLoadingState();
        }
    }
    
    async screenWithWatchlists(address) {
        const normalizedAddress = address.toLowerCase();
        const matches = [];
        
        for (const [listName, addresses] of this.watchlists) {
            if (addresses.has(normalizedAddress)) {
                matches.push({
                    list: listName,
                    type: this.getListType(listName),
                    severity: this.getListSeverity(listName)
                });
            }
        }
        
        return {
            provider: 'internal_watchlists',
            result: {
                matches,
                riskLevel: matches.length > 0 ? 'HIGH' : 'LOW',
                confidence: 1.0
            }
        };
    }
    
    getListType(listName) {
        const types = {
            ofac: 'sanctions',
            pep: 'political_exposure',
            eu_sanctions: 'sanctions',
            un_sanctions: 'sanctions'
        };
        return types[listName] || 'other';
    }
    
    getListSeverity(listName) {
        const severities = {
            ofac: 100,
            pep: 70,
            eu_sanctions: 80,
            un_sanctions: 90
        };
        return severities[listName] || 50;
    }
    
    aggregateResults(address, providerResults) {
        let totalRiskScore = 0;
        let providerCount = 0;
        const details = {};
        const flags = [];
        
        for (const { provider, result } of providerResults) {
            if (result.error) continue;
            
            details[provider] = result;
            
            // Calculate risk contribution
            const riskContribution = this.calculateRiskContribution(provider, result);
            totalRiskScore += riskContribution;
            providerCount++;
            
            // Collect flags
            if (result.matches && result.matches.length > 0) {
                flags.push(...result.matches.map(m => ({
                    source: provider,
                    type: m.type,
                    severity: m.severity || 50
                })));
            }
            
            if (result.riskLevel === 'HIGH') {
                flags.push({
                    source: provider,
                    type: 'high_risk',
                    severity: 80
                });
            }
        }
        
        // Calculate average risk score
        const riskScore = providerCount > 0 ? totalRiskScore / providerCount : 0;
        
        // Adjust based on flag severity
        const flagAdjustment = flags.reduce((sum, flag) => sum + flag.severity, 0) / Math.max(1, flags.length);
        const adjustedRiskScore = Math.min(100, riskScore + flagAdjustment);
        
        return {
            wallet: address,
            timestamp: Date.now(),
            riskScore: Math.round(adjustedRiskScore),
            riskLevel: this.getRiskLevel(adjustedRiskScore),
            details,
            flags,
            providerCount,
            recommendations: this.generateRecommendations(adjustedRiskScore, flags)
        };
    }
    
    calculateRiskContribution(provider, result) {
        const baseScores = {
            internal_watchlists: 0, // Will be adjusted by matches
            chainalysis: result.riskScore || 50,
            elliptic: result.riskLevel === 'HIGH' ? 80 : 
                     result.riskLevel === 'MEDIUM' ? 50 : 20,
            trm: result.riskScore || 50
        };
        
        let score = baseScores[provider] || 50;
        
        // Adjust for matches
        if (result.matches && result.matches.length > 0) {
            score += result.matches.length * 10;
        }
        
        return Math.min(100, score);
    }
    
    getRiskLevel(score) {
        if (score >= 80) return 'HIGH';
        if (score >= 50) return 'MEDIUM';
        return 'LOW';
    }
    
    generateRecommendations(riskScore, flags) {
        const recommendations = [];
        
        if (riskScore >= 80) {
            recommendations.push({
                action: 'BLOCK',
                priority: 'HIGH',
                message: 'Immediate blocking recommended due to high risk score'
            });
        } else if (riskScore >= 50) {
            recommendations.push({
                action: 'REVIEW',
                priority: 'MEDIUM',
                message: 'Manual review required before proceeding'
            });
        }
        
        if (flags.some(f => f.type === 'sanctions')) {
            recommendations.push({
                action: 'REJECT',
                priority: 'CRITICAL',
                message: 'Address appears on sanctions list - regulatory compliance violation risk'
            });
        }
        
        if (flags.some(f => f.type === 'political_exposure')) {
            recommendations.push({
                action: 'ENHANCED_DUE_DILIGENCE',
                priority: 'HIGH',
                message: 'Politically Exposed Person detected - enhanced due diligence required'
            });
        }
        
        return recommendations;
    }
    
    isValidAddress(address) {
        // Basic Ethereum address validation
        if (!address) return false;
        
        // Check if it looks like an Ethereum address
        if (address.startsWith('0x') && address.length === 42) {
            return /^0x[0-9a-fA-F]{40}$/.test(address);
        }
        
        // Could add other chain address validations here
        return false;
    }
    
    async monitorTransactions() {
        // Monitor recent transactions for compliance
        try {
            const transactions = await this.dashboard.engineAPI.getTransactions();
            
            if (!transactions || !Array.isArray(transactions)) {
                return;
            }
            
            // Screen addresses from recent transactions
            const addresses = new Set();
            transactions.slice(0, 50).forEach(tx => {
                if (tx.from) addresses.add(tx.from);
                if (tx.to) addresses.add(tx.to);
            });
            
            // Screen addresses that haven't been screened recently
            for (const address of addresses) {
                if (this.isValidAddress(address)) {
                    const cached = this.screenings.get(address);
                    if (!cached || (Date.now() - cached.timestamp > 60 * 60 * 1000)) {
                        await this.screenWallet(address);
                        await this.delay(1000); // Rate limiting
                    }
                }
            }
            
        } catch (error) {
            console.warn('Transaction monitoring failed:', error);
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    createAlert(address, screeningResult) {
        const alert = {
            id: this.dashboard.generateId(),
            type: 'COMPLIANCE_ALERT',
            severity: screeningResult.riskLevel === 'HIGH' ? 'CRITICAL' : 'WARNING',
            address,
            riskScore: screeningResult.riskScore,
            timestamp: Date.now(),
            flags: screeningResult.flags,
            acknowledged: false
        };
        
        this.alerts.push(alert);
        this.saveAlerts();
        this.showAlertNotification(alert);
        
        return alert;
    }
    
    saveAlerts() {
        localStorage.setItem('aineon-compliance-alerts', JSON.stringify(this.alerts));
    }
    
    showAlertNotification(alert) {
        // Create alert notification
        const notification = document.createElement('div');
        notification.className = 'compliance-alert';
        notification.innerHTML = `
            <div class="alert-header">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Compliance Alert</span>
                <button class="close-btn">&times;</button>
            </div>
            <div class="alert-body">
                <p>High risk wallet detected: ${alert.address.substring(0, 8)}...${alert.address.substring(34)}</p>
                <p>Risk Score: <span class="risk-high">${alert.riskScore}</span></p>
                <button class="btn btn-sm btn-primary view-details">View Details</button>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            background: white;
            border-left: 4px solid #dc3545;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 10002;
            animation: slideInUp 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Setup event handlers
        notification.querySelector('.close-btn').onclick = () => notification.remove();
        notification.querySelector('.view-details').onclick = () => {
            this.showScreeningDetails(alert.address);
            notification.remove();
        };
        
        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 30000);
    }
    
    showScreeningModal() {
        // Create modal for wallet screening
        const modal = document.createElement('div');
        modal.className = 'compliance-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-search"></i> Screen Wallet Address</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="input-group">
                        <input type="text" 
                               id="modal-wallet-input" 
                               placeholder="Enter 0x wallet address..."
                               class="wallet-input">
                        <button id="modal-screen-btn" class="btn btn-primary">
                            <i class="fas fa-search"></i> Screen
                        </button>
                    </div>
                    <div class="result-container" id="modal-result-container">
                        <!-- Results will be displayed here -->
                    </div>
                </div>
            </div>
        `;
        
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10003;
            animation: fadeIn 0.3s ease;
        `;
        
        modal.querySelector('.modal-content').style.cssText = `
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            animation: scaleIn 0.3s ease;
        `;
        
        document.body.appendChild(modal);
        
        // Setup event handlers
        modal.querySelector('.close-modal').onclick = () => modal.remove();
        modal.querySelector('#modal-screen-btn').onclick = async () => {
            const address = modal.querySelector('#modal-wallet-input').value;
            if (this.isValidAddress(address)) {
                await this.screenWallet(address);
                modal.remove();
            } else {
                alert('Please enter a valid Ethereum address');
            }
        };
        
        // Close on background click
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };
    }
    
    showScreeningDetails(address) {
        const screening = this.screenings.get(address);
        if (!screening) {
            this.dashboard.showError('No screening data found for this address');
            return;
        }
        
        // Create details modal
        const modal = document.createElement('div');
        modal.className = 'screening-details-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-info-circle"></i> Screening Details</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="wallet-info">
                        <p><strong>Wallet:</strong> ${address}</p>
                        <p><strong>Screened:</strong> ${this.dashboard.formatDate(screening.timestamp)}</p>
                    </div>
                    <div class="risk-summary">
                        <h4>Risk Summary</h4>
                        <div class="risk-score-display ${screening.riskLevel.toLowerCase()}">
                            ${screening.riskScore} - ${screening.riskLevel}
                        </div>
                    </div>
                    ${this.renderProviderDetails(screening.details)}
                    ${this.renderFlags(screening.flags)}
                    ${this.renderRecommendations(screening.recommendations)}
                </div>
            </div>
        `;
        
        // Similar modal styling as above...
        document.body.appendChild(modal);
        
        // Setup close handler
        modal.querySelector('.close-modal').onclick = () => modal.remove();
    }
    
    renderProviderDetails(details) {
        let html = '<div class="provider-details"><h4>Provider Results</h4>';
        
        for (const [provider, result] of Object.entries(details)) {
            html += `
                <div class="provider-result">
                    <h5>${provider}</h5>
                    <p>Risk Level: <span class="risk-${result.riskLevel?.toLowerCase() || 'unknown'}">
                        ${result.riskLevel || 'N/A'}
                    </span></p>
                    ${result.matches ? `<p>Matches: ${result.matches.length}</p>` : ''}
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    renderFlags(flags) {
        if (!flags || flags.length === 0) return '';
        
        let html = '<div class="flags-section"><h4>Risk Flags</h4><ul>';
        
        flags.forEach(flag => {
            html += `
                <li>
                    <span class="flag-type ${flag.type}">${flag.type}</span>
                    <span class="flag-severity severity-${Math.floor(flag.severity / 25)}">
                        Severity: ${flag.severity}
                    </span>
                    <span class="flag-source">Source: ${flag.source}</span>
                </li>
            `;
        });
        
        html += '</ul></div>';
        return html;
    }
    
    renderRecommendations(recommendations) {
        if (!recommendations || recommendations.length === 0) return '';
        
        let html = '<div class="recommendations-section"><h4>Recommendations</h4><ul>';
        
        recommendations.forEach(rec => {
            html += `
                <li class="recommendation ${rec.priority.toLowerCase()}">
                    <strong>${rec.action}:</strong> ${rec.message}
                    <span class="priority-badge ${rec.priority.toLowerCase()}">
                        ${rec.priority}
                    </span>
                </li>
            `;
        });
        
        html += '</ul></div>';
        return html;
    }
    
    showLoadingState() {
        const resultContainer = document.getElementById('modal-result-container') || 
                               document.querySelector('.screening-results');
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Screening wallet address...</p>
                </div>
            `;
        }
    }
    
    hideLoadingState() {
        // Implementation for hiding loading state
    }
    
    updateScreeningResultUI(result) {
        // Update risk score display
        const riskDisplay = document.getElementById('risk-score-display');
        if (riskDisplay) {
            riskDisplay.textContent = result.riskScore;
            riskDisplay.className = `risk-score ${result.riskLevel.toLowerCase()}`;
        }
        
        // Update KYC status
        const kycStatus = document.getElementById('kyc-status');
        if (kycStatus) {
            kycStatus.textContent = result.riskLevel === 'LOW' ? 
                'KYC Verified' : 'Manual Review Required';
            kycStatus.className = `status-indicator ${
                result.riskLevel === 'LOW' ? 'success' : 
                result.riskLevel === 'MEDIUM' ? 'warning' : 'error'
            }`;
        }
    }
    
    updateRecentScreeningsUI() {
        const recentList = document.getElementById('recent-screens');
        if (!recentList) return;
        
        const recentScreenings = Array.from(this.screenings.values())
            .sort((a, b) => b.timestamp - a.timestamp)
            .slice(0, 5);
        
        if (recentScreenings.length === 0) {
            recentList.innerHTML = '<p class="empty-state">No recent screenings</p>';
            return;
        }
        
        let html = '<div class="recent-list">';
        recentScreenings.forEach(screening => {
            const shortAddress = `${screening.wallet.substring(0, 6)}...${screening.wallet.substring(38)}`;
            html += `
                <div class="recent-item">
                    <span class="recent-address">${shortAddress}</span>
                    <span class="risk-badge risk-${screening.riskLevel.toLowerCase()}">
                        ${screening.riskScore}
                    </span>
                    <span class="recent-time">${this.formatRelativeTime(screening.timestamp)}</span>
                </div>
            `;
        });
        html += '</div>';
        
        recentList.innerHTML = html;
    }
    
    formatRelativeTime(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }
    
    async generateComplianceReport() {
        try {
            this.showLoadingState();
            
            const report = {
                id: this.dashboard.generateId(),
                timestamp: Date.now(),
                period: 'last_30_days',
                summary: await this.generateReportSummary(),
                screenings: Array.from(this.screenings.values())
                    .filter(s => Date.now() - s.timestamp < 30 * 24 * 60 * 60 * 1000),
                alerts: this.alerts.filter(a => !a.acknowledged),
                recommendations: this.generateComplianceRecommendations()
            };
            
            // Download report
            this.downloadReport(report);
            
            this.dashboard.showSuccess('Compliance report generated successfully');
            
        } catch (error) {
            console.error('Failed to generate compliance report:', error);
            this.dashboard.showError('Failed to generate compliance report');
        } finally {
            this.hideLoadingState();
        }
    }
    
    async generateReportSummary() {
        const recentScreenings = Array.from(this.screenings.values())
            .filter(s => Date.now() - s.timestamp < 30 * 24 * 60 * 60 * 1000);
        
        const highRisk = recentScreenings.filter(s => s.riskLevel === 'HIGH').length;
        const mediumRisk = recentScreenings.filter(s => s.riskLevel === 'MEDIUM').length;
        const lowRisk = recentScreenings.filter(s => s.riskLevel === 'LOW').length;
        
        return {
            totalScreenings: recentScreenings.length,
            riskBreakdown: { highRisk, mediumRisk, lowRisk },
            complianceRate: ((lowRisk + mediumRisk * 0.5) / recentScreenings.length * 100) || 0,
            alertsGenerated: this.alerts.length,
            avgRiskScore: recentScreenings.reduce((sum, s) => sum + s.riskScore, 0) / recentScreenings.length || 0
        };
    }
    
    generateComplianceRecommendations() {
        const recommendations = [];
        
        // Analyze screening patterns
        const recentScreenings = Array.from(this.screenings.values())
            .filter(s => Date.now() - s.timestamp < 30 * 24 * 60 * 60 * 1000);
        
        const highRiskPercentage = recentScreenings.filter(s => s.riskLevel === 'HIGH').length / recentScreenings.length * 100;
        
        if (highRiskPercentage > 10) {
            recommendations.push({
                action: 'ENHANCE_SCREENING',
                priority: 'HIGH',
                description: 'High percentage of risky addresses detected. Consider implementing additional screening measures.',
                impact: 'Reduces regulatory risk'
            });
        }
        
        if (this.alerts.length > 5) {
            recommendations.push({
                action: 'REVIEW_ALERT_THRESHOLDS',
                priority: 'MEDIUM',
                description: 'Multiple compliance alerts generated. Review alert thresholds to reduce false positives.',
                impact: 'Improves operational efficiency'
            });
        }
        
        return recommendations;
    }
    
    downloadReport(report) {
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-report-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    async quickScreen(address) {
        // Quick screening for real-time validation
        if (!this.isValidAddress(address)) return;
        
        try {
            const normalized = address.toLowerCase();
            
            // Check watchlists first (fast)
            for (const [listName, addresses] of this.watchlists) {
                if (addresses.has(normalized)) {
                    // Immediate high risk detection
                    this.showQuickAlert(address, listName);
                    return;
                }
            }
            
            // Quick provider check if available
            if (this.providers.chainalysis) {
                const result = await this.providers.chainalysis.quickScreen(address);
                if (result.riskLevel === 'HIGH') {
                    this.showQuickAlert(address, 'chainalysis');
                }
            }
            
        } catch (error) {
            // Silent fail for quick screening
            console.debug('Quick screening failed:', error);
        }
    }
    
    showQuickAlert(address, source) {
        // Show subtle notification for quick screening results
        const notification = document.createElement('div');
        notification.className = 'quick-alert';
        notification.textContent = `âš ï¸ ${source.toUpperCase()}: Potential risk detected`;
        notification.style.cssText = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: #fff3cd;
            color: #856404;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9rem;
            z-index: 10000;
            animation: slideInUp 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Export for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ComplianceModule };
}
