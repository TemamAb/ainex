/**
 * AINEON Enterprise - Infrastructure Manager
 * Cloud Infrastructure Management and Monitoring
 */

class InfrastructureManager {
    constructor(enterpriseDashboard) {
        this.dashboard = enterpriseDashboard;
        this.infrastructure = {};
        this.regions = [];
        this.resources = {};
        
        this.initialize();
    }
    
    async initialize() {
        console.log('í¿¢ Initializing Infrastructure Manager...');
        
        // Load infrastructure data
        await this.loadInfrastructureData();
        
        // Initialize UI
        this.initUI();
        
        // Initialize event listeners
        this.initEventListeners();
        
        // Start infrastructure monitoring
        this.startInfrastructureMonitoring();
    }
    
    async loadInfrastructureData() {
        try {
            // Load regions
            const regionsResponse = await fetch('/api/infrastructure/regions');
            if (regionsResponse.ok) {
                this.regions = await regionsResponse.json();
                this.updateRegionsDisplay();
            }
            
            // Load resources
            const resourcesResponse = await fetch('/api/infrastructure/resources');
            if (resourcesResponse.ok) {
                this.resources = await resourcesResponse.json();
                this.updateResourcesDisplay();
            }
            
            // Load infrastructure summary
            const summaryResponse = await fetch('/api/infrastructure/summary');
            if (summaryResponse.ok) {
                this.infrastructure = await summaryResponse.json();
                this.updateInfrastructureSummary();
            }
            
        } catch (error) {
            console.error('Failed to load infrastructure data:', error);
            this.loadMockInfrastructureData();
        }
    }
    
    loadMockInfrastructureData() {
        // Mock infrastructure data for demonstration
        this.regions = [
            {
                id: 'us-east-1',
                name: 'US East (N. Virginia)',
                status: 'active',
                resources: {
                    instances: 12,
                    databases: 3,
                    loadBalancers: 2,
                    storage: '1.2TB'
                },
                latency: 24,
                health: 'healthy'
            },
            {
                id: 'eu-west-1',
                name: 'EU West (Ireland)',
                status: 'standby',
                resources: {
                    instances: 8,
                    databases: 2,
                    loadBalancers: 1,
                    storage: '850GB'
                },
                latency: 42,
                health: 'healthy'
            },
            {
                id: 'asia-northeast1',
                name: 'Asia Northeast (Tokyo)',
                status: 'active',
                resources: {
                    instances: 6,
                    databases: 1,
                    loadBalancers: 1,
                    storage: '520GB'
                },
                latency: 89,
                health: 'degraded'
            }
        ];
        
        this.resources = {
            compute: {
                total: 26,
                used: 18,
                available: 8,
                instances: [
                    { id: 'api-1', type: 'c5.xlarge', status: 'running', cpu: 65, memory: 72 },
                    { id: 'api-2', type: 'c5.xlarge', status: 'running', cpu: 58, memory: 68 },
                    { id: 'db-1', type: 'r5.large', status: 'running', cpu: 42, memory: 85 },
                    { id: 'cache-1', type: 'cache.r5.large', status: 'running', cpu: 38, memory: 92 }
                ]
            },
            storage: {
                total: '2.5TB',
                used: '1.8TB',
                available: '700GB',
                volumes: [
                    { id: 'vol-1', type: 'gp3', size: '500GB', used: '420GB' },
                    { id: 'vol-2', type: 'io1', size: '1TB', used: '850GB' }
                ]
            },
            network: {
                throughput: '1.2Gbps',
                activeConnections: 1247,
                loadBalancers: 4,
                vpcs: 3
            }
        };
        
        this.infrastructure = {
            totalCost: 12500,
            monthlyTrend: -8,
            carbonFootprint: 2450,
            efficiencyScore: 87
        };
        
        this.updateRegionsDisplay();
        this.updateResourcesDisplay();
        this.updateInfrastructureSummary();
    }
    
    updateRegionsDisplay() {
        const regionsGrid = document.getElementById('regions-grid');
        if (!regionsGrid) return;
        
        regionsGrid.innerHTML = this.regions.map(region => `
            <div class="region-card ${region.status}">
                <div class="region-header">
                    <div class="region-name">${region.name}</div>
                    <div class="region-status ${region.health}">
                        <span class="status-dot ${region.health}"></span>
                        ${region.status.toUpperCase()}
                    </div>
                </div>
                <div class="region-metrics">
                    <div class="metric">
                        <span class="metric-label">Instances</span>
                        <span class="metric-value">${region.resources.instances}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Databases</span>
                        <span class="metric-value">${region.resources.databases}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Storage</span>
                        <span class="metric-value">${region.resources.storage}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Latency</span>
                        <span class="metric-value">${region.latency}ms</span>
                    </div>
                </div>
                <div class="region-actions">
                    <button class="btn btn-sm" data-region="${region.id}" data-action="details">
                        Details
                    </button>
                    <button class="btn btn-sm ${region.status === 'active' ? 'btn-secondary' : 'btn-primary'}" 
                            data-region="${region.id}" 
                            data-action="${region.status === 'active' ? 'deactivate' : 'activate'}">
                        ${region.status === 'active' ? 'Deactivate' : 'Activate'}
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    updateResourcesDisplay() {
        // Update compute resources
        this.updateComputeResources();
        
        // Update storage resources
        this.updateStorageResources();
        
        // Update network resources
        this.updateNetworkResources();
    }
    
    updateComputeResources() {
        const computeElement = document.getElementById('compute-resources');
        if (!computeElement || !this.resources.compute) return;
        
        const { total, used, available, instances } = this.resources.compute;
        const usagePercent = Math.round((used / total) * 100);
        
        computeElement.innerHTML = `
            <div class="resource-summary">
                <div class="resource-stats">
                    <div class="stat">
                        <span class="stat-label">Total Instances</span>
                        <span class="stat-value">${total}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">In Use</span>
                        <span class="stat-value">${used}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Available</span>
                        <span class="stat-value">${available}</span>
                    </div>
                </div>
                <div class="resource-usage">
                    <div class="usage-bar">
                        <div class="usage-fill" style="width: ${usagePercent}%"></div>
                    </div>
                    <div class="usage-label">${usagePercent}% utilized</div>
                </div>
            </div>
            <div class="instances-list">
                ${instances.map(instance => `
                    <div class="instance-item">
                        <div class="instance-id">${instance.id}</div>
                        <div class="instance-type">${instance.type}</div>
                        <div class="instance-status ${instance.status}">
                            <span class="status-dot ${instance.status}"></span>
                            ${instance.status}
                        </div>
                        <div class="instance-metrics">
                            <span class="metric cpu">CPU: ${instance.cpu}%</span>
                            <span class="metric memory">Memory: ${instance.memory}%</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    updateStorageResources() {
        const storageElement = document.getElementById('storage-resources');
        if (!storageElement || !this.resources.storage) return;
        
        const { total, used, available, volumes } = this.resources.storage;
        
        // Calculate usage percentage
        const totalGB = this.parseStorageSize(total);
        const usedGB = this.parseStorageSize(used);
        const usagePercent = Math.round((usedGB / totalGB) * 100);
        
        storageElement.innerHTML = `
            <div class="resource-summary">
                <div class="resource-stats">
                    <div class="stat">
                        <span class="stat-label">Total Storage</span>
                        <span class="stat-value">${total}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Used</span>
                        <span class="stat-value">${used}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Available</span>
                        <span class="stat-value">${available}</span>
                    </div>
                </div>
                <div class="resource-usage">
                    <div class="usage-bar">
                        <div class="usage-fill" style="width: ${usagePercent}%"></div>
                    </div>
                    <div class="usage-label">${usagePercent}% utilized</div>
                </div>
            </div>
            <div class="volumes-list">
                ${volumes.map(volume => `
                    <div class="volume-item">
                        <div class="volume-id">${volume.id}</div>
                        <div class="volume-type">${volume.type}</div>
                        <div class="volume-size">${volume.size}</div>
                        <div class="volume-usage">
                            <div class="usage-bar">
                                <div class="usage-fill" style="width: ${Math.round((this.parseStorageSize(volume.used) / this.parseStorageSize(volume.size)) * 100)}%"></div>
                            </div>
                            <span class="usage-label">${volume.used}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    parseStorageSize(size) {
        // Parse storage size string like "500GB" or "1TB"
        const match = size.match(/^(\d+(?:\.\d+)?)\s*(GB|TB)$/i);
        if (!match) return 0;
        
        const value = parseFloat(match[1]);
        const unit = match[2].toUpperCase();
        
        if (unit === 'TB') {
            return value * 1024; // Convert TB to GB
        }
        return value;
    }
    
    updateNetworkResources() {
        const networkElement = document.getElementById('network-resources');
        if (!networkElement || !this.resources.network) return;
        
        const { throughput, activeConnections, loadBalancers, vpcs } = this.resources.network;
        
        networkElement.innerHTML = `
            <div class="network-stats">
                <div class="network-stat">
                    <div class="stat-icon">
                        <i class="fas fa-exchange-alt"></i>
                    </div>
                    <div class="stat-data">
                        <div class="stat-value">${throughput}</div>
                        <div class="stat-label">Throughput</div>
                    </div>
                </div>
                <div class="network-stat">
                    <div class="stat-icon">
                        <i class="fas fa-link"></i>
                    </div>
                    <div class="stat-data">
                        <div class="stat-value">${activeConnections.toLocaleString()}</div>
                        <div class="stat-label">Active Connections</div>
                    </div>
                </div>
                <div class="network-stat">
                    <div class="stat-icon">
                        <i class="fas fa-balance-scale"></i>
                    </div>
                    <div class="stat-data">
                        <div class="stat-value">${loadBalancers}</div>
                        <div class="stat-label">Load Balancers</div>
                    </div>
                </div>
                <div class="network-stat">
                    <div class="stat-icon">
                        <i class="fas fa-network-wired"></i>
                    </div>
                    <div class="stat-data">
                        <div class="stat-value">${vpcs}</div>
                        <div class="stat-label">VPCs</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    updateInfrastructureSummary() {
        const summaryElement = document.getElementById('infrastructure-summary');
        if (!summaryElement || !this.infrastructure) return;
        
        const { totalCost, monthlyTrend, carbonFootprint, efficiencyScore } = this.infrastructure;
        
        summaryElement.innerHTML = `
            <div class="summary-metrics">
                <div class="summary-metric">
                    <div class="metric-icon">
                        <i class="fas fa-dollar-sign"></i>
                    </div>
                    <div class="metric-data">
                        <div class="metric-value">$${totalCost.toLocaleString()}</div>
                        <div class="metric-label">Monthly Cost</div>
                        <div class="metric-trend ${monthlyTrend < 0 ? 'down' : 'up'}">
                            ${monthlyTrend < 0 ? 'â†“' : 'â†‘'} ${Math.abs(monthlyTrend)}%
                        </div>
                    </div>
                </div>
                <div class="summary-metric">
                    <div class="metric-icon">
                        <i class="fas fa-leaf"></i>
                    </div>
                    <div class="metric-data">
                        <div class="metric-value">${carbonFootprint}kg</div>
                        <div class="metric-label">CO2 / Month</div>
                    </div>
                </div>
                <div class="summary-metric">
                    <div class="metric-icon">
                        <i class="fas fa-tachometer-alt"></i>
                    </div>
                    <div class="metric-data">
                        <div class="metric-value">${efficiencyScore}%</div>
                        <div class="metric-label">Efficiency Score</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    initUI() {
        // Initialize infrastructure charts
        this.initInfrastructureCharts();
        
        // Initialize topology viewer
        this.initTopologyViewer();
    }
    
    initInfrastructureCharts() {
        // Initialize cost trend chart
        this.initCostTrendChart();
        
        // Initialize resource utilization chart
        this.initResourceUtilizationChart();
    }
    
    initCostTrendChart() {
        const ctx = document.getElementById('cost-trend-chart');
        if (!ctx) return;
        
        // Mock data for demonstration
        new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                datasets: [{
                    label: 'Infrastructure Cost',
                    data: [11000, 11500, 12000, 12500, 12200, 11800, 11500],
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
                    title: {
                        display: true,
                        text: 'Monthly Infrastructure Cost',
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
                        ticks: { 
                            color: 'var(--gray-400)',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    initResourceUtilizationChart() {
        const ctx = document.getElementById('resource-utilization-chart');
        if (!ctx) return;
        
        // Mock data for demonstration
        new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Compute', 'Storage', 'Database', 'Network'],
                datasets: [{
                    data: [45, 25, 20, 10],
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(155, 89, 182, 0.8)',
                        'rgba(241, 196, 15, 0.8)'
                    ],
                    borderColor: [
                        '#3498db',
                        '#2ecc71',
                        '#9b59b6',
                        '#f1c40f'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: 'var(--gray-400)' }
                    },
                    title: {
                        display: true,
                        text: 'Resource Utilization',
                        color: 'white'
                    }
                }
            }
        });
    }
    
    initTopologyViewer() {
        const viewer = document.getElementById('topology-viewer');
        if (!viewer) return;
        
        // Simple topology visualization
        viewer.innerHTML = `
            <div class="topology-diagram">
                <div class="network-layer">
                    <div class="node load-balancer">
                        <i class="fas fa-balance-scale"></i>
                        <span>Load Balancer</span>
                    </div>
                    <div class="connections">
                        <div class="connection"></div>
                        <div class="connection"></div>
                    </div>
                    <div class="server-group">
                        <div class="node api-server">
                            <i class="fas fa-server"></i>
                            <span>API Server</span>
                        </div>
                        <div class="node api-server">
                            <i class="fas fa-server"></i>
                            <span>API Server</span>
                        </div>
                    </div>
                    <div class="connections">
                        <div class="connection"></div>
                    </div>
                    <div class="data-layer">
                        <div class="node database">
                            <i class="fas fa-database"></i>
                            <span>Database</span>
                        </div>
                        <div class="node cache">
                            <i class="fas fa-bolt"></i>
                            <span>Cache</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    initEventListeners() {
        // Region actions
        document.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            const regionId = e.target.dataset.region;
            
            if (action && regionId) {
                if (action === 'details') {
                    this.showRegionDetails(regionId);
                } else if (action === 'activate' || action === 'deactivate') {
                    this.toggleRegion(regionId, action === 'activate');
                }
            }
        });
        
        // Scale resources buttons
        const scaleUpBtn = document.getElementById('scale-up-resources');
        const scaleDownBtn = document.getElementById('scale-down-resources');
        
        if (scaleUpBtn) {
            scaleUpBtn.addEventListener('click', () => this.scaleResources('up'));
        }
        
        if (scaleDownBtn) {
            scaleDownBtn.addEventListener('click', () => this.scaleResources('down'));
        }
        
        // Deploy new instance
        const deployBtn = document.getElementById('deploy-instance');
        if (deployBtn) {
            deployBtn.addEventListener('click', () => this.deployNewInstance());
        }
        
        // Backup infrastructure
        const backupBtn = document.getElementById('backup-infrastructure');
        if (backupBtn) {
            backupBtn.addEventListener('click', () => this.backupInfrastructure());
        }
        
        // Optimize costs
        const optimizeBtn = document.getElementById('optimize-costs');
        if (optimizeBtn) {
            optimizeBtn.addEventListener('click', () => this.optimizeCosts());
        }
    }
    
    async showRegionDetails(regionId) {
        const region = this.regions.find(r => r.id === regionId);
        if (!region) return;
        
        try {
            const response = await fetch(`/api/infrastructure/regions/${regionId}/details`);
            const details = response.ok ? await response.json() : {};
            
            this.showRegionModal(region, details);
        } catch (error) {
            console.error('Failed to load region details:', error);
            this.showRegionModal(region, {});
        }
    }
    
    showRegionModal(region, details) {
        const modal = document.createElement('div');
        modal.className = 'region-details-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-globe-americas"></i> ${region.name}</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="region-info">
                        <div class="info-item">
                            <span class="info-label">Region ID:</span>
                            <span class="info-value">${region.id}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Status:</span>
                            <span class="info-value ${region.status}">${region.status.toUpperCase()}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Health:</span>
                            <span class="info-value ${region.health}">${region.health}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Latency:</span>
                            <span class="info-value">${region.latency}ms</span>
                        </div>
                    </div>
                    
                    <div class="region-resources">
                        <h4>Resources</h4>
                        <div class="resources-grid">
                            <div class="resource-card">
                                <div class="resource-icon">
                                    <i class="fas fa-server"></i>
                                </div>
                                <div class="resource-data">
                                    <div class="resource-value">${region.resources.instances}</div>
                                    <div class="resource-label">Instances</div>
                                </div>
                            </div>
                            <div class="resource-card">
                                <div class="resource-icon">
                                    <i class="fas fa-database"></i>
                                </div>
                                <div class="resource-data">
                                    <div class="resource-value">${region.resources.databases}</div>
                                    <div class="resource-label">Databases</div>
                                </div>
                            </div>
                            <div class="resource-card">
                                <div class="resource-icon">
                                    <i class="fas fa-hdd"></i>
                                </div>
                                <div class="resource-data">
                                    <div class="resource-value">${region.resources.storage}</div>
                                    <div class="resource-label">Storage</div>
                                </div>
                            </div>
                            <div class="resource-card">
                                <div class="resource-icon">
                                    <i class="fas fa-network-wired"></i>
                                </div>
                                <div class="resource-data">
                                    <div class="resource-value">${region.resources.loadBalancers || 0}</div>
                                    <div class="resource-label">Load Balancers</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    ${details.metrics ? `
                    <div class="region-metrics">
                        <h4>Performance Metrics</h4>
                        <div class="metrics-grid">
                            ${Object.entries(details.metrics).map(([key, value]) => `
                                <div class="metric-item">
                                    <span class="metric-label">${key}</span>
                                    <span class="metric-value">${value}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="modal-actions">
                        <button class="btn btn-primary" data-region="${region.id}" data-action="monitor">
                            <i class="fas fa-chart-line"></i> Monitor
                        </button>
                        <button class="btn btn-secondary" data-region="${region.id}" data-action="configure">
                            <i class="fas fa-cog"></i> Configure
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.querySelector('.close-btn').onclick = () => modal.remove();
        
        // Add action listeners
        modal.querySelector('[data-action="monitor"]').addEventListener('click', () => {
            this.monitorRegion(region.id);
            modal.remove();
        });
        
        modal.querySelector('[data-action="configure"]').addEventListener('click', () => {
            this.configureRegion(region.id);
            modal.remove();
        });
    }
    
    async toggleRegion(regionId, activate) {
        const action = activate ? 'activate' : 'deactivate';
        const confirmed = await this.dashboard.showConfirmation(
            `${activate ? 'Activate' : 'Deactivate'} Region`,
            `Are you sure you want to ${action} this region?`
        );
        
        if (confirmed) {
            try {
                const response = await fetch(`/api/infrastructure/regions/${regionId}/${action}`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    await this.loadInfrastructureData();
                    this.dashboard.showSuccess(`Region ${action}d successfully`);
                }
            } catch (error) {
                this.dashboard.showError(`Failed to ${action} region`);
            }
        }
    }
    
    async scaleResources(direction) {
        const type = prompt(`Enter resource type to scale ${direction} (instances, storage, database):`);
        if (!type) return;
        
        const amount = prompt(`Enter amount to scale ${direction} (e.g., 2, 100GB):`);
        if (!amount) return;
        
        try {
            const response = await fetch('/api/infrastructure/scale', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    direction,
                    type,
                    amount
                })
            });
            
            if (response.ok) {
                await this.loadInfrastructureData();
                this.dashboard.showSuccess(`Resources scaled ${direction} successfully`);
            }
        } catch (error) {
            this.dashboard.showError(`Failed to scale resources ${direction}`);
        }
    }
    
    async deployNewInstance() {
        const instanceType = prompt('Enter instance type (e.g., c5.xlarge, r5.large):');
        if (!instanceType) return;
        
        const region = prompt('Enter region (us-east-1, eu-west-1, asia-northeast1):');
        if (!region) return;
        
        try {
            const response = await fetch('/api/infrastructure/instances', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: instanceType,
                    region: region
                })
            });
            
            if (response.ok) {
                await this.loadInfrastructureData();
                this.dashboard.showSuccess('New instance deployed successfully');
            }
        } catch (error) {
            this.dashboard.showError('Failed to deploy new instance');
        }
    }
    
    async backupInfrastructure() {
        const confirmed = await this.dashboard.showConfirmation(
            'Backup Infrastructure',
            'This will create a backup of all infrastructure configuration. Continue?'
        );
        
        if (confirmed) {
            try {
                const response = await fetch('/api/infrastructure/backup', { method: 'POST' });
                if (response.ok) {
                    const backup = await response.json();
                    this.downloadBackup(backup);
                    this.dashboard.showSuccess('Infrastructure backup created');
                }
            } catch (error) {
                this.dashboard.showError('Failed to create backup');
            }
        }
    }
    
    downloadBackup(backup) {
        const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `infrastructure-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
    
    async optimizeCosts() {
        try {
            const response = await fetch('/api/infrastructure/optimize');
            if (response.ok) {
                const recommendations = await response.json();
                this.showOptimizationRecommendations(recommendations);
            }
        } catch (error) {
            this.dashboard.showError('Failed to get optimization recommendations');
        }
    }
    
    showOptimizationRecommendations(recommendations) {
        const modal = document.createElement('div');
        modal.className = 'optimization-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-chart-line"></i> Cost Optimization Recommendations</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="recommendations-list">
                        ${recommendations.map(rec => `
                            <div class="recommendation-item">
                                <div class="recommendation-header">
                                    <div class="rec-title">${rec.title}</div>
                                    <div class="rec-savings">Save $${rec.estimatedSavings}/month</div>
                                </div>
                                <div class="rec-description">${rec.description}</div>
                                <div class="rec-actions">
                                    <button class="btn btn-sm btn-primary" data-action="apply" data-rec="${rec.id}">
                                        Apply
                                    </button>
                                    <button class="btn btn-sm" data-action="details" data-rec="${rec.id}">
                                        Details
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
        
        // Add recommendation action listeners
        modal.querySelectorAll('[data-action="apply"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const recId = e.target.dataset.rec;
                this.applyOptimization(recId);
            });
        });
    }
    
    async applyOptimization(recommendationId) {
        try {
            const response = await fetch(`/api/infrastructure/optimize/${recommendationId}/apply`, {
                method: 'POST'
            });
            
            if (response.ok) {
                await this.loadInfrastructureData();
                this.dashboard.showSuccess('Optimization applied successfully');
            }
        } catch (error) {
            this.dashboard.showError('Failed to apply optimization');
        }
    }
    
    monitorRegion(regionId) {
        // Navigate to monitoring with region filter
        this.dashboard.switchTab('monitoring');
        // Additional region-specific monitoring setup would go here
    }
    
    configureRegion(regionId) {
        // Show region configuration interface
        this.dashboard.showWarning(`Configuration interface for ${regionId} would open here`);
    }
    
    startInfrastructureMonitoring() {
        // Subscribe to infrastructure events
        if (this.dashboard.socket) {
            this.dashboard.socket.send(JSON.stringify({
                type: 'subscribe',
                channels: ['infrastructure_events', 'resource_updates']
            }));
        }
        
        // Handle infrastructure updates
        this.dashboard.socket.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'resource_updates') {
                this.handleResourceUpdates(data.payload);
            } else if (data.type === 'infrastructure_events') {
                this.handleInfrastructureEvents(data.payload);
            }
        });
        
        // Periodic infrastructure updates
        setInterval(() => this.refreshInfrastructureData(), 60000);
    }
    
    async refreshInfrastructureData() {
        try {
            await this.loadInfrastructureData();
        } catch (error) {
            console.error('Failed to refresh infrastructure data:', error);
        }
    }
    
    handleResourceUpdates(updates) {
        // Update specific resources
        Object.keys(updates).forEach(resourceType => {
            if (this.resources[resourceType]) {
                this.resources[resourceType] = {
                    ...this.resources[resourceType],
                    ...updates[resourceType]
                };
            }
        });
        
        // Update displays
        this.updateResourcesDisplay();
    }
    
    handleInfrastructureEvents(events) {
        events.forEach(event => {
            // Show notification for critical events
            if (event.severity === 'critical') {
                this.dashboard.handleNewAlert({
                    id: `infra-event-${Date.now()}`,
                    title: event.title,
                    description: event.description,
                    severity: 'critical',
                    timestamp: Date.now(),
                    service: 'infrastructure'
                });
            }
            
            // Add to activity feed
            this.dashboard.updateActivityFeed([{
                type: 'infrastructure',
                action: event.title,
                timestamp: Date.now()
            }]);
        });
    }
}

export default InfrastructureManager;
