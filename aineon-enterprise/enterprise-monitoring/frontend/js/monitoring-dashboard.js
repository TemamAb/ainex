/**
 * AINEON Enterprise - Monitoring Dashboard
 * Real-time System Monitoring and Metrics
 */

class MonitoringDashboard {
    constructor(enterpriseDashboard) {
        this.dashboard = enterpriseDashboard;
        this.charts = {};
        this.metrics = {};
        this.timeRange = '7d';
        
        this.initialize();
    }
    
    async initialize() {
        console.log('í³Š Initializing Monitoring Dashboard...');
        
        // Load initial metrics
        await this.loadMetrics();
        
        // Initialize charts
        this.initCharts();
        
        // Set up real-time updates
        this.setupRealTimeUpdates();
        
        // Initialize event listeners
        this.initEventListeners();
    }
    
    async loadMetrics() {
        try {
            const response = await fetch(`/api/metrics?range=${this.timeRange}`);
            if (response.ok) {
                this.metrics = await response.json();
                this.updateCharts();
                this.updateMetricsDisplay();
            }
        } catch (error) {
            console.error('Failed to load metrics:', error);
            this.dashboard.showError('Failed to load monitoring data');
        }
    }
    
    initCharts() {
        // Initialize CPU usage chart
        this.initCPUChart();
        
        // Initialize memory usage chart
        this.initMemoryChart();
        
        // Initialize network traffic chart
        this.initNetworkChart();
        
        // Initialize error rate chart
        this.initErrorChart();
    }
    
    initCPUChart() {
        const ctx = document.getElementById('cpu-usage-chart');
        if (!ctx) return;
        
        this.charts.cpu = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage',
                    data: [],
                    borderColor: 'var(--accent-teal)',
                    backgroundColor: 'rgba(0, 180, 216, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: this.getChartOptions('CPU Usage (%)')
        });
    }
    
    initMemoryChart() {
        const ctx = document.getElementById('memory-usage-chart');
        if (!ctx) return;
        
        this.charts.memory = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Memory Usage',
                    data: [],
                    borderColor: '#9b59b6',
                    backgroundColor: 'rgba(155, 89, 182, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: this.getChartOptions('Memory Usage (%)')
        });
    }
    
    initNetworkChart() {
        const ctx = document.getElementById('network-traffic-chart');
        if (!ctx) return;
        
        this.charts.network = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Inbound',
                        data: [],
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Outbound',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: this.getChartOptions('Network Traffic (MB/s)')
        });
    }
    
    initErrorChart() {
        const ctx = document.getElementById('error-rate-chart');
        if (!ctx) return;
        
        this.charts.errors = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Error Rate',
                    data: [],
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: 'var(--error-red)',
                    borderWidth: 1
                }]
            },
            options: this.getChartOptions('Error Rate (%)', true)
        });
    }
    
    getChartOptions(title, isBar = false) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: !isBar,
                    labels: { color: 'var(--gray-400)' }
                },
                title: {
                    display: true,
                    text: title,
                    color: 'white',
                    font: { size: 14 }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'var(--primary-dark)',
                    titleColor: 'white',
                    bodyColor: 'var(--gray-300)',
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
        };
    }
    
    updateCharts() {
        if (!this.metrics.historical) return;
        
        const labels = this.metrics.historical.map(point => 
            new Date(point.timestamp).toLocaleTimeString()
        );
        
        // Update CPU chart
        if (this.charts.cpu) {
            this.charts.cpu.data.labels = labels;
            this.charts.cpu.data.datasets[0].data = this.metrics.historical.map(p => p.cpu);
            this.charts.cpu.update();
        }
        
        // Update memory chart
        if (this.charts.memory) {
            this.charts.memory.data.labels = labels;
            this.charts.memory.data.datasets[0].data = this.metrics.historical.map(p => p.memory);
            this.charts.memory.update();
        }
        
        // Update network chart
        if (this.charts.network) {
            this.charts.network.data.labels = labels;
            this.charts.network.data.datasets[0].data = this.metrics.historical.map(p => p.network_in);
            this.charts.network.data.datasets[1].data = this.metrics.historical.map(p => p.network_out);
            this.charts.network.update();
        }
        
        // Update error chart
        if (this.charts.errors) {
            this.charts.errors.data.labels = labels;
            this.charts.errors.data.datasets[0].data = this.metrics.historical.map(p => p.error_rate);
            this.charts.errors.update();
        }
    }
    
    updateMetricsDisplay() {
        // Update real-time metrics display
        this.updateMetric('cpu-usage', this.metrics.current?.cpu);
        this.updateMetric('memory-usage', this.metrics.current?.memory);
        this.updateMetric('disk-usage', this.metrics.current?.disk);
        this.updateMetric('network-usage', this.metrics.current?.network_total);
        this.updateMetric('request-rate', this.metrics.current?.requests);
        this.updateMetric('error-rate-current', this.metrics.current?.error_rate);
    }
    
    updateMetric(elementId, value) {
        const element = document.getElementById(elementId);
        if (element && value !== undefined) {
            const formattedValue = this.formatMetricValue(value, elementId);
            element.textContent = formattedValue;
            
            // Add trend indicator
            this.updateTrendIndicator(elementId, value);
        }
    }
    
    formatMetricValue(value, metricType) {
        switch (metricType) {
            case 'cpu-usage':
            case 'memory-usage':
            case 'disk-usage':
            case 'error-rate-current':
                return `${value.toFixed(1)}%`;
            case 'network-usage':
                return `${(value / 1024 / 1024).toFixed(1)} MB/s`;
            case 'request-rate':
                return `${Math.round(value).toLocaleString()}/s`;
            default:
                return value.toLocaleString();
        }
    }
    
    updateTrendIndicator(metricId, currentValue) {
        const previousValue = this.metrics.previous?.[metricId];
        if (previousValue === undefined) return;
        
        const element = document.getElementById(`${metricId}-trend`);
        if (!element) return;
        
        const change = ((currentValue - previousValue) / previousValue) * 100;
        
        if (Math.abs(change) < 1) {
            element.textContent = 'â†’';
            element.className = 'trend stable';
        } else if (change > 0) {
            element.textContent = `â†‘ ${change.toFixed(1)}%`;
            element.className = 'trend up';
        } else {
            element.textContent = `â†“ ${Math.abs(change).toFixed(1)}%`;
            element.className = 'trend down';
        }
    }
    
    setupRealTimeUpdates() {
        // Subscribe to real-time metrics updates
        if (this.dashboard.socket) {
            this.dashboard.socket.send(JSON.stringify({
                type: 'subscribe',
                channels: ['metrics_realtime']
            }));
        }
        
        // Handle incoming real-time updates
        this.dashboard.socket.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics_realtime') {
                this.handleRealTimeUpdate(data.payload);
            }
        });
    }
    
    handleRealTimeUpdate(metrics) {
        // Update current metrics
        this.metrics.current = { ...this.metrics.current, ...metrics };
        
        // Add to historical data
        if (!this.metrics.historical) {
            this.metrics.historical = [];
        }
        
        this.metrics.historical.push({
            timestamp: Date.now(),
            ...metrics
        });
        
        // Keep only last 100 data points
        if (this.metrics.historical.length > 100) {
            this.metrics.historical.shift();
        }
        
        // Update displays
        this.updateMetricsDisplay();
        this.updateCharts();
        
        // Check thresholds
        this.checkThresholds(metrics);
    }
    
    checkThresholds(metrics) {
        const thresholds = this.dashboard.config.system.alertThresholds;
        
        if (metrics.cpu > thresholds.cpu) {
            this.dashboard.handleNewAlert({
                id: `cpu-high-${Date.now()}`,
                title: 'High CPU Usage',
                description: `CPU usage is at ${metrics.cpu}% (threshold: ${thresholds.cpu}%)`,
                severity: 'warning',
                timestamp: Date.now(),
                service: 'system'
            });
        }
        
        if (metrics.memory > thresholds.memory) {
            this.dashboard.handleNewAlert({
                id: `memory-high-${Date.now()}`,
                title: 'High Memory Usage',
                description: `Memory usage is at ${metrics.memory}% (threshold: ${thresholds.memory}%)`,
                severity: 'warning',
                timestamp: Date.now(),
                service: 'system'
            });
        }
        
        if (metrics.error_rate > thresholds.errorRate) {
            this.dashboard.handleNewAlert({
                id: `error-rate-high-${Date.now()}`,
                title: 'High Error Rate',
                description: `Error rate is at ${metrics.error_rate}% (threshold: ${thresholds.errorRate}%)`,
                severity: 'critical',
                timestamp: Date.now(),
                service: 'api'
            });
        }
    }
    
    initEventListeners() {
        // Time range selector
        const rangePresets = document.querySelectorAll('.range-preset');
        rangePresets.forEach(preset => {
            preset.addEventListener('click', () => {
                rangePresets.forEach(p => p.classList.remove('active'));
                preset.classList.add('active');
                this.timeRange = preset.dataset.range;
                this.loadMetrics();
            });
        });
        
        // Custom date range
        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');
        const applyRangeBtn = document.getElementById('apply-range');
        
        if (applyRangeBtn) {
            applyRangeBtn.addEventListener('click', () => {
                const startDate = startDateInput.value;
                const endDate = endDateInput.value;
                
                if (startDate && endDate) {
                    this.loadCustomRange(startDate, endDate);
                }
            });
        }
        
        // Chart type toggles
        const chartTypeSelectors = document.querySelectorAll('.chart-type-selector');
        chartTypeSelectors.forEach(selector => {
            selector.addEventListener('change', (e) => {
                const chartId = e.target.dataset.chart;
                const chartType = e.target.value;
                this.changeChartType(chartId, chartType);
            });
        });
        
        // Export data button
        const exportBtn = document.getElementById('export-metrics');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportMetrics());
        }
    }
    
    async loadCustomRange(startDate, endDate) {
        try {
            const response = await fetch(`/api/metrics?start=${startDate}&end=${endDate}`);
            if (response.ok) {
                this.metrics = await response.json();
                this.updateCharts();
                this.updateMetricsDisplay();
                this.dashboard.showSuccess(`Loaded data from ${startDate} to ${endDate}`);
            }
        } catch (error) {
            console.error('Failed to load custom range:', error);
            this.dashboard.showError('Failed to load data for selected range');
        }
    }
    
    changeChartType(chartId, chartType) {
        const chart = this.charts[chartId];
        if (chart) {
            chart.config.type = chartType;
            chart.update();
        }
    }
    
    async exportMetrics() {
        try {
            const response = await fetch(`/api/metrics/export?range=${this.timeRange}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `metrics-${this.timeRange}-${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.dashboard.showSuccess('Metrics exported successfully');
            }
        } catch (error) {
            console.error('Failed to export metrics:', error);
            this.dashboard.showError('Failed to export metrics');
        }
    }
    
    // Service health monitoring
    updateServiceHealth(service, health) {
        const serviceElement = document.querySelector(`[data-service="${service}"]`);
        if (serviceElement) {
            const statusElement = serviceElement.querySelector('.service-status');
            if (statusElement) {
                statusElement.textContent = health;
                statusElement.className = `service-status ${health}`;
            }
        }
    }
    
    // Resource usage updates
    updateResourceUsage(resource, usage) {
        const bar = document.querySelector(`[data-resource="${resource}"] .resource-fill`);
        if (bar) {
            bar.style.width = `${usage}%`;
            
            // Update color based on usage
            if (usage > 90) {
                bar.style.background = 'linear-gradient(90deg, var(--error-red), #c0392b)';
            } else if (usage > 75) {
                bar.style.background = 'linear-gradient(90deg, var(--warning-orange), #d35400)';
            } else {
                bar.style.background = 'linear-gradient(90deg, var(--success-green), var(--accent-teal))';
            }
        }
        
        const value = document.querySelector(`[data-resource="${resource}"] .resource-value`);
        if (value) {
            value.textContent = `${usage}%`;
        }
    }
    
    // Alert timeline updates
    addToTimeline(event) {
        const timeline = document.getElementById('alert-timeline');
        if (!timeline) return;
        
        const eventElement = document.createElement('div');
        eventElement.className = `timeline-event ${event.severity || 'info'}`;
        eventElement.innerHTML = `
            <div class="event-time">${new Date(event.timestamp).toLocaleTimeString()}</div>
            <div class="event-content">
                <div class="event-title">${event.title}</div>
                <div class="event-description">${event.description || ''}</div>
            </div>
            <div class="event-service">${event.service || 'system'}</div>
        `;
        
        timeline.insertBefore(eventElement, timeline.firstChild);
        
        // Limit to 50 events
        if (timeline.children.length > 50) {
            timeline.removeChild(timeline.lastChild);
        }
    }
}

export default MonitoringDashboard;
