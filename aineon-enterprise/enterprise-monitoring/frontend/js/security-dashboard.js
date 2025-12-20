/**
 * AINEON Enterprise - Security Dashboard
 * Enterprise Security Monitoring and Management
 */

class SecurityDashboard {
    constructor(enterpriseDashboard) {
        this.dashboard = enterpriseDashboard;
        this.securityScore = 0;
        this.threats = [];
        this.incidents = [];
        this.compliance = {};
        
        this.initialize();
    }
    
    async initialize() {
        console.log('���️ Initializing Security Dashboard...');
        
        // Load security data
        await this.loadSecurityData();
        
        // Initialize UI
        this.initUI();
        
        // Initialize event listeners
        this.initEventListeners();
        
        // Start security monitoring
        this.startSecurityMonitoring();
    }
    
    async loadSecurityData() {
        try {
            // Load security score
            const scoreResponse = await fetch('/api/security/score');
            if (scoreResponse.ok) {
                const scoreData = await scoreResponse.json();
                this.securityScore = scoreData.score;
                this.updateSecurityScore();
            }
            
            // Load threats
            const threatsResponse = await fetch('/api/security/threats');
            if (threatsResponse.ok) {
                this.threats = await threatsResponse.json();
                this.updateThreatsDisplay();
            }
            
            // Load incidents
            const incidentsResponse = await fetch('/api/security/incidents');
            if (incidentsResponse.ok) {
                this.incidents = await incidentsResponse.json();
                this.updateIncidentsDisplay();
            }
            
            // Load compliance status
            const complianceResponse = await fetch('/api/compliance/status');
            if (complianceResponse.ok) {
                this.compliance = await complianceResponse.json();
                this.updateComplianceDisplay();
            }
            
        } catch (error) {
            console.error('Failed to load security data:', error);
            // Load mock data for demonstration
            this.loadMockData();
        }
    }
    
    loadMockData() {
        // Mock security data for demonstration
        this.securityScore = 87;
        
        this.threats = [
            {
                id: 'threat-1',
                title: 'Brute Force Attempt',
                description: 'Multiple failed login attempts detected from IP 192.168.1.100',
                severity: 'high',
                timestamp: Date.now() - 3600000,
                status: 'active'
            },
            {
                id: 'threat-2',
                title: 'Suspicious API Activity',
                description: 'Unusual API call patterns detected from user account',
                severity: 'medium',
                timestamp: Date.now() - 7200000,
                status: 'investigating'
            },
            {
                id: 'threat-3',
                title: 'Data Access Anomaly',
                description: 'User accessed sensitive data outside normal hours',
                severity: 'low',
                timestamp: Date.now() - 10800000,
                status: 'resolved'
            }
        ];
        
        this.incidents = [
            {
                id: 'incident-1',
                title: 'Unauthorized Access Attempt',
                severity: 'critical',
                timestamp: Date.now() - 86400000,
                description: 'Multiple failed attempts to access admin panel',
                status: 'investigating',
                assignedTo: 'Security Team'
            }
        ];
        
        this.compliance = {
            gdpr: { status: 'compliant', score: 95 },
            mica: { status: 'partial', score: 85 },
            soc2: { status: 'compliant', score: 92 },
            pci: { status: 'non-compliant', score: 65 }
        };
        
        this.updateSecurityScore();
        this.updateThreatsDisplay();
        this.updateIncidentsDisplay();
        this.updateComplianceDisplay();
    }
    
    updateSecurityScore() {
        const scoreElement = document.getElementById('security-score-value');
        if (scoreElement) {
            scoreElement.textContent = this.securityScore;
            scoreElement.className = `score-value ${
                this.securityScore >= 90 ? 'success' :
                this.securityScore >= 75 ? 'warning' : 'error'
            }`;
        }
        
        const scoreLabel = document.getElementById('security-score-label');
        if (scoreLabel) {
            if (this.securityScore >= 90) {
                scoreLabel.textContent = 'Excellent - All systems secure';
            } else if (this.securityScore >= 75) {
                scoreLabel.textContent = 'Good - Minor issues detected';
            } else {
                scoreLabel.textContent = 'Needs Attention - Security concerns';
            }
        }
    }
    
    updateThreatsDisplay() {
        const threatsList = document.getElementById('threats-list');
        if (!threatsList) return;
        
        threatsList.innerHTML = this.threats.map(threat => `
            <div class="threat-item ${threat.severity}">
                <div class="threat-title">${threat.title}</div>
                <div class="threat-description">${threat.description}</div>
                <div class="threat-meta">
                    <span class="threat-time">${this.formatTimeAgo(threat.timestamp)}</span>
                    <span class="threat-status ${threat.status}">${threat.status}</span>
                </div>
            </div>
        `).join('');
    }
    
    updateIncidentsDisplay() {
        const incidentsList = document.getElementById('incidents-list');
        if (!incidentsList) return;
        
        incidentsList.innerHTML = this.incidents.map(incident => `
            <div class="incident-item">
                <div class="incident-severity ${incident.severity}">
                    ${incident.severity.toUpperCase()}
                </div>
                <div class="incident-content">
                    <div class="incident-title">${incident.title}</div>
                    <div class="incident-description">${incident.description}</div>
                    <div class="incident-meta">
                        <span>${this.formatTimeAgo(incident.timestamp)}</span>
                        <span>Assigned to: ${incident.assignedTo}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    updateComplianceDisplay() {
        const complianceList = document.getElementById('compliance-list');
        if (!complianceList) return;
        
        complianceList.innerHTML = Object.entries(this.compliance).map(([standard, data]) => `
            <div class="compliance-item ${data.status}">
                <div class="compliance-name">
                    ${standard.toUpperCase()}
                </div>
                <div class="compliance-progress">
                    <div class="compliance-bar">
                        <div class="compliance-fill ${data.status}" 
                             style="width: ${data.score}%"></div>
                    </div>
                    <div class="compliance-percentage">${data.score}%</div>
                </div>
            </div>
        `).join('');
    }
    
    initUI() {
        // Initialize attack map
        this.initAttackMap();
        
        // Initialize security controls
        this.initSecurityControls();
        
        // Initialize compliance charts
        this.initComplianceCharts();
    }
    
    initAttackMap() {
        // Create mock attack map visualization
        const mapContainer = document.getElementById('attack-map');
        if (!mapContainer) return;
        
        // This would be replaced with a real visualization library
        mapContainer.innerHTML = `
            <div class="map-visualization">
                <div class="attack-source" style="top: 20%; left: 10%;">
                    <i class="fas fa-skull-crossbones"></i>
                </div>
                <div class="attack-source" style="top: 60%; left: 15%;">
                    <i class="fas fa-skull-crossbones"></i>
                </div>
                <div class="defense-point" style="top: 40%; left: 50%;">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <div class="critical-asset" style="top: 80%; left: 80%;">
                    <i class="fas fa-database"></i>
                </div>
            </div>
        `;
    }
    
    initSecurityControls() {
        // Load security controls configuration
        this.loadSecurityControls();
    }
    
    async loadSecurityControls() {
        try {
            const response = await fetch('/api/security/controls');
            if (response.ok) {
                const controls = await response.json();
                this.renderSecurityControls(controls);
            }
        } catch (error) {
            console.error('Failed to load security controls:', error);
            this.renderMockSecurityControls();
        }
    }
    
    renderSecurityControls(controls) {
        const controlsGrid = document.getElementById('security-controls-grid');
        if (!controlsGrid) return;
        
        controlsGrid.innerHTML = controls.map(control => `
            <div class="control-card">
                <div class="control-header">
                    <div class="control-name">
                        <i class="fas ${this.getControlIcon(control.type)}"></i>
                        ${control.name}
                    </div>
                    <div class="control-status ${control.status}">
                        ${control.status}
                    </div>
                </div>
                <div class="control-description">
                    ${control.description}
                </div>
                <div class="control-actions">
                    <button class="control-btn ${control.enabled ? 'btn-secondary' : 'btn-primary'}"
                            data-control="${control.id}"
                            data-action="${control.enabled ? 'disable' : 'enable'}">
                        ${control.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button class="control-btn" data-control="${control.id}" data-action="configure">
                        Configure
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    renderMockSecurityControls() {
        const controls = [
            {
                id: 'mfa',
                name: 'Multi-Factor Authentication',
                type: 'authentication',
                description: 'Require MFA for all user accounts',
                status: 'enabled',
                enabled: true
            },
            {
                id: 'waf',
                name: 'Web Application Firewall',
                type: 'network',
                description: 'Protect against web application attacks',
                status: 'enabled',
                enabled: true
            },
            {
                id: 'ids',
                name: 'Intrusion Detection System',
                type: 'monitoring',
                description: 'Monitor for suspicious network activity',
                status: 'warning',
                enabled: true
            },
            {
                id: 'encryption',
                name: 'Data Encryption',
                type: 'data',
                description: 'Encrypt all sensitive data at rest',
                status: 'enabled',
                enabled: true
            },
            {
                id: 'backup',
                name: 'Automated Backups',
                type: 'recovery',
                description: 'Automatic daily backups with encryption',
                status: 'enabled',
                enabled: true
            },
            {
                id: 'audit',
                name: 'Audit Logging',
                type: 'compliance',
                description: 'Comprehensive audit trail for all actions',
                status: 'enabled',
                enabled: true
            }
        ];
        
        this.renderSecurityControls(controls);
    }
    
    getControlIcon(type) {
        const icons = {
            authentication: 'fa-user-lock',
            network: 'fa-network-wired',
            monitoring: 'fa-eye',
            data: 'fa-database',
            recovery: 'fa-save',
            compliance: 'fa-clipboard-check'
        };
        return icons[type] || 'fa-cog';
    }
    
    initComplianceCharts() {
        // Initialize compliance trend chart
        this.initComplianceTrendChart();
        
        // Initialize security events chart
        this.initSecurityEventsChart();
    }
    
    initComplianceTrendChart() {
        const ctx = document.getElementById('compliance-trend-chart');
        if (!ctx) return;
        
        // Mock data for demonstration
        new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [
                    {
                        label: 'GDPR Compliance',
                        data: [85, 88, 90, 92, 95, 96],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 2,
                        fill: true
                    },
                    {
                        label: 'MiCA Compliance',
                        data: [70, 75, 78, 82, 85, 87],
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        borderWidth: 2,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: 'var(--gray-400)' } },
                    title: {
                        display: true,
                        text: 'Compliance Trend',
                        color: 'white'
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
                        min: 60,
                        max: 100
                    }
                }
            }
        });
    }
    
    initSecurityEventsChart() {
        const ctx = document.getElementById('security-events-chart');
        if (!ctx) return;
        
        // Mock data for demonstration
        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Login Attempts', 'API Calls', 'Data Access', 'Admin Actions'],
                datasets: [{
                    label: 'Security Events',
                    data: [1200, 8500, 320, 45],
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(155, 89, 182, 0.7)',
                        'rgba(241, 196, 15, 0.7)',
                        'rgba(231, 76, 60, 0.7)'
                    ],
                    borderColor: [
                        '#3498db',
                        '#9b59b6',
                        '#f1c40f',
                        '#e74c3c'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Security Events by Type',
                        color: 'white'
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
    
    initEventListeners() {
        // Security control buttons
        document.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            const controlId = e.target.dataset.control;
            
            if (action && controlId) {
                if (action === 'enable' || action === 'disable') {
                    this.toggleSecurityControl(controlId, action === 'enable');
                } else if (action === 'configure') {
                    this.configureSecurityControl(controlId);
                }
            }
        });
        
        // Run security scan button
        const scanBtn = document.getElementById('run-security-scan');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => this.runSecurityScan());
        }
        
        // View all threats button
        const viewThreatsBtn = document.getElementById('view-all-threats');
        if (viewThreatsBtn) {
            viewThreatsBtn.addEventListener('click', () => this.showAllThreats());
        }
        
        // View all incidents button
        const viewIncidentsBtn = document.getElementById('view-all-incidents');
        if (viewIncidentsBtn) {
            viewIncidentsBtn.addEventListener('click', () => this.showAllIncidents());
        }
        
        // Emergency lockdown button
        const lockdownBtn = document.getElementById('emergency-lockdown');
        if (lockdownBtn) {
            lockdownBtn.addEventListener('click', () => this.initiateEmergencyLockdown());
        }
    }
    
    async toggleSecurityControl(controlId, enable) {
        try {
            const response = await fetch(`/api/security/controls/${controlId}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enable })
            });
            
            if (response.ok) {
                await this.loadSecurityControls();
                this.dashboard.showSuccess(`Security control ${enable ? 'enabled' : 'disabled'}`);
            }
        } catch (error) {
            this.dashboard.showError(`Failed to ${enable ? 'enable' : 'disable'} security control`);
        }
    }
    
    configureSecurityControl(controlId) {
        // Show configuration modal for security control
        this.dashboard.showWarning('Configuration interface would open here');
    }
    
    async runSecurityScan() {
        const confirmed = await this.dashboard.showConfirmation(
            'Run Security Scan',
            'This will perform a comprehensive security scan. Continue?'
        );
        
        if (confirmed) {
            try {
                const response = await fetch('/api/security/scan', { method: 'POST' });
                if (response.ok) {
                    this.dashboard.showSuccess('Security scan initiated');
                    
                    // Monitor scan progress
                    this.monitorSecurityScan();
                }
            } catch (error) {
                this.dashboard.showError('Failed to start security scan');
            }
        }
    }
    
    async monitorSecurityScan() {
        // Poll for scan results
        const interval = setInterval(async () => {
            try {
                const response = await fetch('/api/security/scan/status');
                if (response.ok) {
                    const status = await response.json();
                    
                    if (status.completed) {
                        clearInterval(interval);
                        
                        if (status.findings && status.findings.length > 0) {
                            this.showScanResults(status.findings);
                        } else {
                            this.dashboard.showSuccess('Security scan completed - No issues found');
                        }
                    }
                }
            } catch (error) {
                clearInterval(interval);
                this.dashboard.showError('Failed to monitor security scan');
            }
        }, 5000);
    }
    
    showScanResults(findings) {
        const modal = document.createElement('div');
        modal.className = 'scan-results-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-search"></i> Security Scan Results</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="scan-summary">
                        <p>Found ${findings.length} security finding(s)</p>
                    </div>
                    <div class="findings-list">
                        ${findings.map(finding => `
                            <div class="finding-item ${finding.severity}">
                                <div class="finding-severity">${finding.severity.toUpperCase()}</div>
                                <div class="finding-content">
                                    <div class="finding-title">${finding.title}</div>
                                    <div class="finding-description">${finding.description}</div>
                                    <div class="finding-recommendation">
                                        <strong>Recommendation:</strong> ${finding.recommendation}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-primary" id="export-scan-results">
                            <i class="fas fa-download"></i> Export Results
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('.close-btn').onclick = () => modal.remove();
        modal.querySelector('#export-scan-results').onclick = () => this.exportScanResults(findings);
    }
    
    exportScanResults(findings) {
        const data = {
            scanDate: new Date().toISOString(),
            findings: findings
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security-scan-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.dashboard.showSuccess('Scan results exported');
    }
    
    showAllThreats() {
        const modal = document.createElement('div');
        modal.className = 'threats-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-exclamation-triangle"></i> All Security Threats</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="threats-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Threat</th>
                                    <th>Severity</th>
                                    <th>Time</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.threats.map(threat => `
                                    <tr>
                                        <td>${threat.title}</td>
                                        <td><span class="severity-${threat.severity}">${threat.severity}</span></td>
                                        <td>${this.formatTimeAgo(threat.timestamp)}</td>
                                        <td><span class="status-${threat.status}">${threat.status}</span></td>
                                        <td>
                                            <button class="btn btn-sm" data-threat="${threat.id}" data-action="investigate">
                                                Investigate
                                            </button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('.close-btn').onclick = () => modal.remove();
    }
    
    showAllIncidents() {
        const modal = document.createElement('div');
        modal.className = 'incidents-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-fire"></i> Security Incidents</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="incidents-list">
                        ${this.incidents.map(incident => `
                            <div class="incident-detail">
                                <div class="incident-header">
                                    <span class="incident-id">#${incident.id}</span>
                                    <span class="incident-severity ${incident.severity}">
                                        ${incident.severity.toUpperCase()}
                                    </span>
                                </div>
                                <div class="incident-title">${incident.title}</div>
                                <div class="incident-description">${incident.description}</div>
                                <div class="incident-timeline">
                                    <div class="timeline-item">
                                        <span class="timeline-label">Detected:</span>
                                        <span class="timeline-value">${new Date(incident.timestamp).toLocaleString()}</span>
                                    </div>
                                    <div class="timeline-item">
                                        <span class="timeline-label">Status:</span>
                                        <span class="timeline-value">${incident.status}</span>
                                    </div>
                                    <div class="timeline-item">
                                        <span class="timeline-label">Assigned to:</span>
                                        <span class="timeline-value">${incident.assignedTo}</span>
                                    </div>
                                </div>
                                <div class="incident-actions">
                                    <button class="btn btn-sm" data-incident="${incident.id}" data-action="update">
                                        Update Status
                                    </button>
                                    <button class="btn btn-sm btn-primary" data-incident="${incident.id}" data-action="resolve">
                                        Mark Resolved
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('.close-btn').onclick = () => modal.remove();
    }
    
    async initiateEmergencyLockdown() {
        const confirmed = await this.dashboard.showConfirmation(
            'Emergency Lockdown',
            '⚠️ CRITICAL: This will lock down all systems and restrict access. Only use in case of confirmed security breach. Continue?'
        );
        
        if (confirmed) {
            try {
                const response = await fetch('/api/security/lockdown', { method: 'POST' });
                if (response.ok) {
                    this.dashboard.showSuccess('Emergency lockdown initiated');
                    this.startLockdownCountdown();
                }
            } catch (error) {
                this.dashboard.showError('Failed to initiate lockdown');
            }
        }
    }
    
    startLockdownCountdown() {
        let countdown = 60;
        
        const modal = document.createElement('div');
        modal.className = 'lockdown-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header critical">
                    <h3><i class="fas fa-skull-crossbones"></i> EMERGENCY LOCKDOWN</h3>
                </div>
                <div class="modal-body">
                    <div class="lockdown-message">
                        <p>System lockdown in progress. All non-essential services will be shut down.</p>
                        <div class="countdown" id="lockdown-countdown">${countdown}</div>
                        <p>Time until complete lockdown:</p>
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-primary" id="cancel-lockdown">Cancel Lockdown</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const countdownElement = modal.querySelector('#lockdown-countdown');
        const interval = setInterval(() => {
            countdown--;
            countdownElement.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(interval);
                modal.remove();
                this.showLockdownComplete();
            }
        }, 1000);
        
        modal.querySelector('#cancel-lockdown').onclick = () => {
            clearInterval(interval);
            modal.remove();
            this.cancelLockdown();
        };
    }
    
    showLockdownComplete() {
        const modal = document.createElement('div');
        modal.className = 'lockdown-complete-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header critical">
                    <h3><i class="fas fa-shield-alt"></i> LOCKDOWN COMPLETE</h3>
                </div>
                <div class="modal-body">
                    <div class="lockdown-status">
                        <p>All systems are now in lockdown mode.</p>
                        <ul>
                            <li>✅ External access blocked</li>
                            <li>✅ Admin access restricted</li>
                            <li>✅ All services secured</li>
                            <li>✅ Audit logging active</li>
                        </ul>
                        <p>Security team has been notified.</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    async cancelLockdown() {
        try {
            await fetch('/api/security/lockdown/cancel', { method: 'POST' });
            this.dashboard.showSuccess('Lockdown cancelled');
        } catch (error) {
            this.dashboard.showError('Failed to cancel lockdown');
        }
    }
    
    startSecurityMonitoring() {
        // Subscribe to security events
        if (this.dashboard.socket) {
            this.dashboard.socket.send(JSON.stringify({
                type: 'subscribe',
                channels: ['security_events', 'threat_intelligence']
            }));
        }
        
        // Handle incoming security events
        this.dashboard.socket.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'security_event') {
                this.handleSecurityEvent(data.payload);
            } else if (data.type === 'threat_intelligence') {
                this.handleThreatIntelligence(data.payload);
            }
        });
        
        // Periodic security score update
        setInterval(() => this.updateSecurityScoreFromAPI(), 300000);
    }
    
    async updateSecurityScoreFromAPI() {
        try {
            const response = await fetch('/api/security/score');
            if (response.ok) {
                const data = await response.json();
                this.securityScore = data.score;
                this.updateSecurityScore();
            }
        } catch (error) {
            console.error('Failed to update security score:', error);
        }
    }
    
    handleSecurityEvent(event) {
        // Add to recent events
        this.addSecurityEvent(event);
        
        // Update security score if needed
        if (event.impactScore) {
            this.securityScore = Math.max(0, this.securityScore - event.impactScore);
            this.updateSecurityScore();
        }
        
        // Show notification for critical events
        if (event.severity === 'critical') {
            this.dashboard.handleNewAlert({
                id: `security-event-${Date.now()}`,
                title: 'Critical Security Event',
                description: event.description,
                severity: 'critical',
                timestamp: Date.now(),
                service: 'security'
            });
        }
    }
    
    addSecurityEvent(event) {
        // Add to security events list
        const eventsList = document.getElementById('security-events-list');
        if (!eventsList) return;
        
        const eventElement = document.createElement('div');
        eventElement.className = `event-item ${event.severity}`;
        eventElement.innerHTML = `
            <div class="event-type ${event.type}">${event.type}</div>
            <div class="event-description">${event.description}</div>
            <div class="event-details">
                <span>${this.formatTimeAgo(event.timestamp)}</span>
                <span>Source: ${event.source}</span>
            </div>
        `;
        
        eventsList.insertBefore(eventElement, eventsList.firstChild);
        
        // Limit to 50 events
        if (eventsList.children.length > 50) {
            eventsList.removeChild(eventsList.lastChild);
        }
    }
    
    handleThreatIntelligence(threat) {
        // Add to threats list
        this.threats.unshift(threat);
        this.updateThreatsDisplay();
        
        // Show notification for high severity threats
        if (threat.severity === 'high' || threat.severity === 'critical') {
            this.dashboard.showWarning(`New threat detected: ${threat.title}`);
        }
    }
    
    formatTimeAgo(timestamp) {
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
}

export default SecurityDashboard;
