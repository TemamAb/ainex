/**
 * AINEON Enterprise - Enterprise Dashboard Core
 * Chief Architect: Enterprise Scaling & High Availability
 * Phase 4 Implementation - Enterprise Grade
 */

class EnterpriseDashboard {
    constructor() {
        this.socket = null;
        this.metrics = {};
        this.alerts = [];
        this.systemStatus = {};
        this.config = {};
        
        this.initialize();
    }
    
    async initialize() {
        console.log('Ì∫Ä Initializing AINEON Enterprise Dashboard...');
        
        try {
            // Load configuration
            await this.loadConfig();
            
            // Initialize WebSocket connection
            await this.initWebSocket();
            
            // Initialize dashboard components
            this.initDashboard();
            
            // Start real-time updates
            this.startRealTimeUpdates();
            
            // Initialize modules
            await this.initModules();
            
            // Start background services
            this.startBackgroundServices();
            
            console.log('‚úÖ Enterprise Dashboard initialized successfully');
            
        } catch (error) {
            console.error('‚ùå Failed to initialize Enterprise Dashboard:', error);
            this.showCriticalError('System initialization failed. Please contact support.');
        }
    }
    
    async loadConfig() {
        // Load enterprise configuration
        const savedConfig = localStorage.getItem('aineon-enterprise-config');
        
        if (savedConfig) {
            this.config = JSON.parse(savedConfig);
        } else {
            // Default enterprise configuration
            this.config = {
                system: {
                    regions: ['us-east-1', 'eu-west-1', 'asia-northeast1'],
                    autoScaling: true,
                    monitoringInterval: 5000,
                    alertThresholds: {
                        cpu: 80,
                        memory: 85,
                        latency: 100,
                        errorRate: 1
                    }
                },
                security: {
                    encryptionLevel: 'enterprise',
                    auditLogging: true,
                    intrusionDetection: true,
                    complianceMonitoring: true
                },
                api: {
                    rateLimiting: true,
                    requestLogging: true,
                    apiKeys: [],
                    webhooks: []
                },
                monitoring: {
                    metricsRetention: '30d',
                    alertRetention: '90d',
                    logRetention: '365d'
                }
            };
            this.saveConfig();
        }
    }
    
    saveConfig() {
        localStorage.setItem('aineon-enterprise-config', JSON.stringify(this.config));
    }
    
    async initWebSocket() {
        // Initialize WebSocket connection for real-time updates
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('Ì¥ó WebSocket connection established');
            this.updateConnectionStatus(true);
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.socket.onclose = () => {
            console.log('Ì¥å WebSocket connection closed');
            this.updateConnectionStatus(false);
            // Attempt reconnection
            setTimeout(() => this.initWebSocket(), 5000);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showError('Real-time updates temporarily unavailable');
        };
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text strong');
        
        if (connected) {
            indicator.classList.add('active');
            indicator.classList.remove('error');
            statusText.textContent = 'OPERATIONAL';
            statusText.className = 'success';
        } else {
            indicator.classList.remove('active');
            indicator.classList.add('error');
            statusText.textContent = 'DISCONNECTED';
            statusText.className = 'error';
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'metrics_update':
                this.updateMetrics(data.payload);
                break;
            case 'alert':
                this.handleNewAlert(data.payload);
                break;
            case 'system_status':
                this.updateSystemStatus(data.payload);
                break;
            case 'incident':
                this.handleIncident(data.payload);
                break;
            case 'security_event':
                this.handleSecurityEvent(data.payload);
                break;
        }
    }
    
    updateMetrics(metrics) {
        this.metrics = { ...this.metrics, ...metrics };
        this.updateMetricsDisplay();
    }
    
    updateMetricsDisplay() {
        // Update real-time metrics display
        const updateTime = document.getElementById('metrics-update-time');
        if (updateTime) {
            updateTime.textContent = new Date().toLocaleTimeString();
        }
        
        // Update specific metrics
        this.updateMetric('requests-per-second', this.metrics.rps);
        this.updateMetric('active-users', this.metrics.activeUsers);
        this.updateMetric('avg-latency', this.metrics.avgLatency);
        this.updateMetric('error-rate', this.metrics.errorRate);
        
        // Update charts if they exist
        if (this.performanceChart) {
            this.updatePerformanceChart();
        }
    }
    
    updateMetric(elementId, value) {
        const element = document.getElementById(elementId);
        if (element && value !== undefined) {
            element.textContent = this.formatMetricValue(value, elementId);
        }
    }
    
    formatMetricValue(value, metricType) {
        switch (metricType) {
            case 'requests-per-second':
                return `${Math.round(value).toLocaleString()}/s`;
            case 'avg-latency':
                return `${value}ms`;
            case 'error-rate':
                return `${value}%`;
            default:
                return value.toLocaleString();
        }
    }
    
    handleNewAlert(alert) {
        this.alerts.push(alert);
        this.updateAlertsDisplay();
        this.showAlertNotification(alert);
        
        // Play alert sound for critical alerts
        if (alert.severity === 'critical') {
            this.playAlertSound();
        }
    }
    
    updateAlertsDisplay() {
        const alertCount = document.getElementById('alert-count');
        if (alertCount) {
            const criticalCount = this.alerts.filter(a => a.severity === 'critical').length;
            alertCount.textContent = criticalCount || '';
            alertCount.style.display = criticalCount > 0 ? 'flex' : 'none';
        }
        
        const recentAlerts = document.getElementById('recent-alerts');
        if (recentAlerts) {
            recentAlerts.innerHTML = this.alerts
                .slice(0, 5)
                .map(alert => this.createAlertHTML(alert))
                .join('');
        }
    }
    
    createAlertHTML(alert) {
        const timeAgo = this.getTimeAgo(alert.timestamp);
        const severityClass = alert.severity || 'warning';
        
        return `
            <div class="alert-item">
                <div class="alert-icon ${severityClass}">
                    <i class="fas fa-exclamation-circle"></i>
                </div>
                <div class="alert-content">
                    <span class="alert-title">${alert.title}</span>
                    <span class="alert-time">${timeAgo}</span>
                </div>
            </div>
        `;
    }
    
    getTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        
        if (minutes < 1) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${Math.floor(hours / 24)}d ago`;
    }
    
    showAlertNotification(alert) {
        // Create notification
        const notification = document.createElement('div');
        notification.className = `alert-notification ${alert.severity}`;
        notification.innerHTML = `
            <div class="notification-header">
                <i class="fas fa-bell"></i>
                <span>System Alert</span>
                <button class="close-btn">&times;</button>
            </div>
            <div class="notification-body">
                <p>${alert.title}</p>
                <p class="notification-description">${alert.description || ''}</p>
                <button class="btn btn-sm view-details">View Details</button>
            </div>
        `;
        
        // Style notification
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            width: 350px;
            background: var(--primary-dark);
            border-left: 4px solid ${this.getAlertColor(alert.severity)};
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-xl);
            z-index: 2000;
            animation: slideInRight 0.3s ease;
            backdrop-filter: blur(10px);
        `;
        
        document.body.appendChild(notification);
        
        // Add event listeners
        notification.querySelector('.close-btn').onclick = () => notification.remove();
        notification.querySelector('.view-details').onclick = () => {
            this.showAlertDetails(alert);
            notification.remove();
        };
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 10000);
    }
    
    getAlertColor(severity) {
        switch (severity) {
            case 'critical': return 'var(--error-red)';
            case 'warning': return 'var(--warning-orange)';
            default: return 'var(--info-cyan)';
        }
    }
    
    playAlertSound() {
        // Play alert sound for critical alerts
        const audio = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEAQB8AAEAfAAABAAgAZGF0YQ');
        audio.volume = 0.3;
        audio.play().catch(() => {
            // Ignore errors if audio can't play
        });
    }
    
    updateSystemStatus(status) {
        this.systemStatus = status;
        this.updateHealthDisplay();
    }
    
    updateHealthDisplay() {
        // Update service health indicators
        const services = ['api-gateway', 'database', 'cache', 'cdn', 'monitoring', 'security'];
        
        services.forEach(service => {
            const element = document.querySelector(`[data-service="${service}"]`);
            if (element && this.systemStatus[service]) {
                const status = this.systemStatus[service];
                element.className = `service-status ${status.health}`;
                element.querySelector('.status-dot').className = `status-dot ${status.health}`;
                element.querySelector('span:last-child').textContent = status.message;
            }
        });
    }
    
    initDashboard() {
        // Initialize tab switching
        this.initTabs();
        
        // Initialize charts
        this.initCharts();
        
        // Initialize event listeners
        this.initEventListeners();
        
        // Initialize activity feed
        this.initActivityFeed();
        
        // Initialize SLA monitor
        this.initSLAMonitor();
    }
    
    initTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Update active tab button
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Show selected tab pane
                tabPanes.forEach(pane => {
                    pane.classList.remove('active');
                    if (pane.id === `${tabName}-tab`) {
                        pane.classList.add('active');
                    }
                });
                
                // Load tab content if needed
                this.loadTabContent(tabName);
            });
        });
    }
    
    async loadTabContent(tabName) {
        switch (tabName) {
            case 'monitoring':
                await this.loadMonitoringDashboard();
                break;
            case 'api':
                await this.loadAPIConsole();
                break;
            case 'security':
                await this.loadSecurityDashboard();
                break;
            case 'infrastructure':
                await this.loadInfrastructureView();
                break;
        }
    }
    
    initCharts() {
        // Initialize performance chart
        const ctx = document.getElementById('performance-chart');
        if (ctx) {
            this.performanceChart = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: Array.from({ length: 24 }, (_, i) => `${i}:00`),
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: Array.from({ length: 24 }, () => Math.random() * 100 + 20),
                        borderColor: 'var(--accent-teal)',
                        backgroundColor: 'rgba(0, 180, 216, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'var(--primary-dark)',
                            titleColor: 'white',
                            bodyColor: 'var(--accent-teal)',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: 'var(--gray-400)' }
                        },
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: 'var(--gray-400)' },
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
    
    updatePerformanceChart() {
        if (this.performanceChart && this.metrics.historical) {
            const newData = this.metrics.historical.slice(-24); // Last 24 data points
            this.performanceChart.data.datasets[0].data = newData;
            this.performanceChart.update('none');
        }
    }
    
    initEventListeners() {
        // Quick action buttons
        document.getElementById('failover-test')?.addEventListener('click', () => this.testFailover());
        document.getElementById('scale-up')?.addEventListener('click', () => this.scaleUp());
        document.getElementById('backup-now')?.addEventListener('click', () => this.startBackup());
        document.getElementById('security-scan')?.addEventListener('click', () => this.startSecurityScan());
        
        // Navigation buttons
        document.getElementById('global-alerts-btn')?.addEventListener('click', () => this.showAlertsModal());
        document.getElementById('monitoring-btn')?.addEventListener('click', () => this.switchTab('monitoring'));
        document.getElementById('api-console-btn')?.addEventListener('click', () => this.switchTab('api'));
        document.getElementById('security-btn')?.addEventListener('click', () => this.switchTab('security'));
        
        // View all alerts
        document.getElementById('view-all-alerts')?.addEventListener('click', () => this.showAllAlerts());
    }
    
    switchTab(tabName) {
        const tabButton = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
        if (tabButton) {
            tabButton.click();
        }
    }
    
    initActivityFeed() {
        // Load recent activity
        this.loadActivityFeed();
        
        // Set up activity refresh
        setInterval(() => this.loadActivityFeed(), 30000);
    }
    
    async loadActivityFeed() {
        try {
            const response = await fetch('/api/activity');
            if (response.ok) {
                const activities = await response.json();
                this.updateActivityFeed(activities);
            }
        } catch (error) {
            console.error('Failed to load activity feed:', error);
        }
    }
    
    updateActivityFeed(activities) {
        const feed = document.getElementById('activity-feed');
        if (!feed) return;
        
        feed.innerHTML = activities.slice(0, 10).map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas ${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-details">
                    <div class="activity-action">${activity.action}</div>
                    <div class="activity-timestamp">${this.getTimeAgo(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');
    }
    
    getActivityIcon(type) {
        const icons = {
            login: 'fa-sign-in-alt',
            logout: 'fa-sign-out-alt',
            transaction: 'fa-exchange-alt',
            alert: 'fa-exclamation-circle',
            deployment: 'fa-rocket',
            backup: 'fa-database',
            security: 'fa-shield-alt',
            api: 'fa-code'
        };
        return icons[type] || 'fa-circle';
    }
    
    initSLAMonitor() {
        // Initialize SLA metrics
        this.updateSLAMetrics();
        
        // Update SLA metrics periodically
        setInterval(() => this.updateSLAMetrics(), 60000);
    }
    
    async updateSLAMetrics() {
        try {
            const response = await fetch('/api/sla-metrics');
            if (response.ok) {
                const slaMetrics = await response.json();
                this.renderSLAMetrics(slaMetrics);
            }
        } catch (error) {
            console.error('Failed to load SLA metrics:', error);
        }
    }
    
    renderSLAMetrics(metrics) {
        // Update SLA progress bars
        Object.keys(metrics).forEach(metric => {
            const bar = document.querySelector(`.sla-metric .sla-bar`);
            if (bar) {
                bar.style.width = `${metrics[metric]}%`;
            }
            
            const value = document.querySelector(`.sla-metric .sla-value`);
            if (value) {
                value.textContent = `${metrics[metric]}%`;
            }
        });
    }
    
    async initModules() {
        // Dynamically load modules as needed
        const modules = ['monitoring', 'api', 'security', 'infrastructure'];
        
        for (const module of modules) {
            try {
                const modulePath = `./js/${module}-dashboard.js`;
                const moduleExport = await import(modulePath);
                this[`${module}Module`] = new moduleExport.default(this);
            } catch (error) {
                console.warn(`Failed to load ${module} module:`, error);
            }
        }
    }
    
    startRealTimeUpdates() {
        // Request real-time updates via WebSocket
        setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({
                    type: 'subscribe',
                    channels: ['metrics', 'alerts', 'system_status']
                }));
            }
        }, 10000);
    }
    
    startBackgroundServices() {
        // Start periodic data collection
        setInterval(() => this.collectSystemMetrics(), 30000);
        
        // Start health checks
        setInterval(() => this.performHealthChecks(), 60000);
        
        // Start backup monitoring
        setInterval(() => this.checkBackupStatus(), 300000);
    }
    
    async collectSystemMetrics() {
        try {
            const response = await fetch('/api/system-metrics');
            if (response.ok) {
                const metrics = await response.json();
                this.updateMetrics(metrics);
            }
        } catch (error) {
            console.error('Failed to collect system metrics:', error);
        }
    }
    
    async performHealthChecks() {
        const services = [
            { name: 'api-gateway', url: '/api/health' },
            { name: 'database', url: '/api/db/health' },
            { name: 'cache', url: '/api/cache/health' }
        ];
        
        for (const service of services) {
            try {
                const response = await fetch(service.url);
                const health = response.ok ? 'healthy' : 'unhealthy';
                this.updateServiceHealth(service.name, health);
            } catch (error) {
                this.updateServiceHealth(service.name, 'unreachable');
            }
        }
    }
    
    updateServiceHealth(serviceName, status) {
        // Update service health in UI
        const serviceElement = document.querySelector(`[data-service="${serviceName}"]`);
        if (serviceElement) {
            serviceElement.className = `service-status ${status}`;
            serviceElement.querySelector('.status-dot').className = `status-dot ${status}`;
        }
    }
    
    async checkBackupStatus() {
        try {
            const response = await fetch('/api/backup-status');
            if (response.ok) {
                const status = await response.json();
                if (!status.lastBackup || Date.now() - new Date(status.lastBackup).getTime() > 24 * 60 * 60 * 1000) {
                    this.showWarning('Backup overdue. Last backup was more than 24 hours ago.');
                }
            }
        } catch (error) {
            console.error('Failed to check backup status:', error);
        }
    }
    
    // Enterprise Actions
    async testFailover() {
        const confirmed = await this.showConfirmation(
            'Test Failover',
            'This will test the failover to secondary region. Continue?'
        );
        
        if (confirmed) {
            try {
                const response = await fetch('/api/failover/test', { method: 'POST' });
                if (response.ok) {
                    this.showSuccess('Failover test initiated');
                }
            } catch (error) {
                this.showError('Failed to initiate failover test');
            }
        }
    }
    
    async scaleUp() {
        const confirmed = await this.showConfirmation(
            'Scale Up Resources',
            'This will increase system resources. Continue?'
        );
        
        if (confirmed) {
            try {
                const response = await fetch('/api/scale-up', { method: 'POST' });
                if (response.ok) {
                    this.showSuccess('Scale-up initiated');
                }
            } catch (error) {
                this.showError('Failed to initiate scale-up');
            }
        }
    }
    
    async startBackup() {
        try {
            const response = await fetch('/api/backup/start', { method: 'POST' });
            if (response.ok) {
                this.showSuccess('Backup initiated');
            }
        } catch (error) {
            this.showError('Failed to start backup');
        }
    }
    
    async startSecurityScan() {
        try {
            const response = await fetch('/api/security/scan', { method: 'POST' });
            if (response.ok) {
                this.showSuccess('Security scan initiated');
            }
        } catch (error) {
            this.showError('Failed to start security scan');
        }
    }
    
    // UI Helpers
    showConfirmation(title, message) {
        return new Promise(resolve => {
            const modal = document.createElement('div');
            modal.className = 'confirmation-modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <h3>${title}</h3>
                    <p>${message}</p>
                    <div class="modal-actions">
                        <button class="btn btn-secondary" id="cancel-btn">Cancel</button>
                        <button class="btn btn-primary" id="confirm-btn">Confirm</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            modal.querySelector('#cancel-btn').onclick = () => {
                modal.remove();
                resolve(false);
            };
            
            modal.querySelector('#confirm-btn').onclick = () => {
                modal.remove();
                resolve(true);
            };
        });
    }
    
    showSuccess(message) {
        // Implementation for success notification
        console.log('‚úÖ', message);
    }
    
    showError(message) {
        // Implementation for error notification
        console.error('‚ùå', message);
    }
    
    showWarning(message) {
        // Implementation for warning notification
        console.warn('‚ö†Ô∏è', message);
    }
    
    showCriticalError(message) {
        // Show critical error modal
        const modal = document.createElement('div');
        modal.className = 'critical-error-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3>Critical System Error</h3>
                <p>${message}</p>
                <div class="modal-actions">
                    <button class="btn btn-primary" id="contact-support">Contact Support</button>
                    <button class="btn btn-secondary" id="reload-page">Reload Page</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('#contact-support').onclick = () => {
            window.location.href = 'mailto:support@ainex.enterprise';
        };
        
        modal.querySelector('#reload-page').onclick = () => {
            window.location.reload();
        };
    }
    
    // Module loading methods
    async loadMonitoringDashboard() {
        if (!this.monitoringModule) {
            try {
                const { default: MonitoringDashboard } = await import('./monitoring-dashboard.js');
                this.monitoringModule = new MonitoringDashboard(this);
            } catch (error) {
                console.error('Failed to load monitoring dashboard:', error);
            }
        }
    }
    
    async loadAPIConsole() {
        if (!this.apiModule) {
            try {
                const { default: APIConsole } = await import('./api-console.js');
                this.apiModule = new APIConsole(this);
            } catch (error) {
                console.error('Failed to load API console:', error);
            }
        }
    }
    
    async loadSecurityDashboard() {
        if (!this.securityModule) {
            try {
                const { default: SecurityDashboard } = await import('./security-dashboard.js');
                this.securityModule = new SecurityDashboard(this);
            } catch (error) {
                console.error('Failed to load security dashboard:', error);
            }
        }
    }
    
    async loadInfrastructureView() {
        if (!this.infrastructureModule) {
            try {
                const { default: InfrastructureView } = await import('./infrastructure-view.js');
                this.infrastructureModule = new InfrastructureView(this);
            } catch (error) {
                console.error('Failed to load infrastructure view:', error);
            }
        }
    }
    
    showAlertDetails(alert) {
        // Show detailed alert information
        const modal = document.createElement('div');
        modal.className = 'alert-details-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-exclamation-circle"></i> Alert Details</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="alert-severity ${alert.severity}">
                        ${alert.severity.toUpperCase()}
                    </div>
                    <h4>${alert.title}</h4>
                    <p>${alert.description || 'No description available'}</p>
                    <div class="alert-metadata">
                        <div class="metadata-item">
                            <span class="label">Time:</span>
                            <span class="value">${new Date(alert.timestamp).toLocaleString()}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="label">Source:</span>
                            <span class="value">${alert.source || 'Unknown'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="label">Service:</span>
                            <span class="value">${alert.service || 'Unknown'}</span>
                        </div>
                    </div>
                    <div class="alert-actions">
                        <button class="btn btn-primary" id="acknowledge-alert">Acknowledge</button>
                        <button class="btn btn-secondary" id="resolve-alert">Mark Resolved</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listeners
        modal.querySelector('.close-btn').onclick = () => modal.remove();
        modal.querySelector('#acknowledge-alert').onclick = () => {
            this.acknowledgeAlert(alert.id);
            modal.remove();
        };
        modal.querySelector('#resolve-alert').onclick = () => {
            this.resolveAlert(alert.id);
            modal.remove();
        };
    }
    
    async acknowledgeAlert(alertId) {
        try {
            await fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
            this.showSuccess('Alert acknowledged');
        } catch (error) {
            this.showError('Failed to acknowledge alert');
        }
    }
    
    async resolveAlert(alertId) {
        try {
            await fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' });
            this.showSuccess('Alert marked as resolved');
        } catch (error) {
            this.showError('Failed to resolve alert');
        }
    }
    
    showAlertsModal() {
        // Show all alerts in a modal
        const modal = document.createElement('div');
        modal.className = 'alerts-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-bell"></i> All Alerts</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="alerts-list" id="all-alerts-list">
                        ${this.alerts.map(alert => this.createAlertHTML(alert)).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('.close-btn').onclick = () => modal.remove();
    }
    
    showAllAlerts() {
        this.showAlertsModal();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.enterpriseDashboard = new EnterpriseDashboard();
});

// Export for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EnterpriseDashboard };
}
