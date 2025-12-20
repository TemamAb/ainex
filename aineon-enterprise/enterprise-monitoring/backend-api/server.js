/**
 * AINEON Enterprise - Backend API Server
 * Enterprise Grade API Infrastructure
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const WebSocket = require('ws');
const morgan = require('morgan');

class EnterpriseAPIServer {
    constructor() {
        this.app = express();
        this.wss = null;
        this.clients = new Set();
        
        this.setupMiddleware();
        this.setupRoutes();
        this.setupWebSocket();
        this.startMetricsCollection();
    }
    
    setupMiddleware() {
        // Security middleware
        this.app.use(helmet({
            contentSecurityPolicy: {
                directives: {
                    defaultSrc: ["'self'"],
                    styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdnjs.cloudflare.com"],
                    fontSrc: ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"],
                    scriptSrc: ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdn.socket.io"],
                    connectSrc: ["'self'", "wss://*", "https://*"]
                }
            }
        }));
        
        this.app.use(cors({
            origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:8080'],
            credentials: true
        }));
        
        // Rate limiting
        const apiLimiter = rateLimit({
            windowMs: 15 * 60 * 1000, // 15 minutes
            max: 100, // Limit each IP to 100 requests per windowMs
            message: 'Too many requests from this IP, please try again later.'
        });
        
        this.app.use('/api/', apiLimiter);
        
        // Logging
        this.app.use(morgan('combined'));
        
        // Body parsing
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));
    }
    
    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({ 
                status: 'healthy',
                timestamp: new Date().toISOString(),
                uptime: process.uptime()
            });
        });
        
        // System metrics
        this.app.get('/api/system-metrics', this.getSystemMetrics.bind(this));
        
        // Infrastructure routes
        this.app.get('/api/infrastructure/regions', this.getRegions.bind(this));
        this.app.get('/api/infrastructure/resources', this.getResources.bind(this));
        this.app.get('/api/infrastructure/summary', this.getInfrastructureSummary.bind(this));
        this.app.post('/api/infrastructure/scale', this.scaleResources.bind(this));
        
        // Security routes
        this.app.get('/api/security/score', this.getSecurityScore.bind(this));
        this.app.get('/api/security/threats', this.getThreats.bind(this));
        this.app.get('/api/security/incidents', this.getIncidents.bind(this));
        this.app.get('/api/security/controls', this.getSecurityControls.bind(this));
        this.app.post('/api/security/scan', this.startSecurityScan.bind(this));
        
        // API management routes
        this.app.get('/api/keys', this.getAPIKeys.bind(this));
        this.app.post('/api/keys', this.createAPIKey.bind(this));
        this.app.post('/api/keys/:id/activate', this.activateAPIKey.bind(this));
        this.app.delete('/api/keys/:id', this.deleteAPIKey.bind(this));
        
        // Monitoring routes
        this.app.get('/api/metrics', this.getMetrics.bind(this));
        this.app.get('/api/metrics/export', this.exportMetrics.bind(this));
        this.app.get('/api/activity', this.getActivity.bind(this));
        this.app.get('/api/sla-metrics', this.getSLAMetrics.bind(this));
        
        // Fallback for SPA
        this.app.get('*', (req, res) => {
            res.sendFile(require('path').join(__dirname, '../frontend/index.html'));
        });
    }
    
    setupWebSocket() {
        this.wss = new WebSocket.Server({ 
            port: process.env.WS_PORT || 8081,
            path: '/ws'
        });
        
        this.wss.on('connection', (ws, req) => {
            this.clients.add(ws);
            console.log('New WebSocket connection');
            
            // Send initial data
            this.sendInitialData(ws);
            
            ws.on('message', (message) => {
                this.handleWebSocketMessage(ws, message);
            });
            
            ws.on('close', () => {
                this.clients.delete(ws);
                console.log('WebSocket connection closed');
            });
            
            ws.on('error', (error) => {
                console.error('WebSocket error:', error);
            });
        });
    }
    
    sendInitialData(ws) {
        // Send initial system status
        ws.send(JSON.stringify({
            type: 'system_status',
            payload: this.getCurrentSystemStatus()
        }));
        
        // Send recent alerts
        ws.send(JSON.stringify({
            type: 'alert',
            payload: this.getRecentAlerts()
        }));
    }
    
    handleWebSocketMessage(ws, message) {
        try {
            const data = JSON.parse(message);
            
            switch (data.type) {
                case 'subscribe':
                    this.handleSubscription(ws, data.channels);
                    break;
                case 'unsubscribe':
                    this.handleUnsubscription(ws, data.channels);
                    break;
                case 'ping':
                    ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
                    break;
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }
    
    handleSubscription(ws, channels) {
        // Store subscription info (simplified)
        ws.subscriptions = ws.subscriptions || [];
        ws.subscriptions.push(...channels);
        
        console.log(`Client subscribed to: ${channels.join(', ')}`);
    }
    
    startMetricsCollection() {
        // Simulate metrics collection
        setInterval(() => {
            const metrics = this.generateMockMetrics();
            this.broadcastToClients({
                type: 'metrics_update',
                payload: metrics
            });
        }, 5000);
        
        // Simulate occasional alerts
        setInterval(() => {
            if (Math.random() < 0.1) { // 10% chance
                const alert = this.generateMockAlert();
                this.broadcastToClients({
                    type: 'alert',
                    payload: alert
                });
            }
        }, 30000);
        
        // Simulate security events
        setInterval(() => {
            if (Math.random() < 0.05) { // 5% chance
                const event = this.generateSecurityEvent();
                this.broadcastToClients({
                    type: 'security_event',
                    payload: event
                });
            }
        }, 60000);
    }
    
    broadcastToClients(message) {
        const messageStr = JSON.stringify(message);
        this.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(messageStr);
            }
        });
    }
    
    // Mock data generators
    generateMockMetrics() {
        return {
            cpu: Math.floor(Math.random() * 30) + 40, // 40-70%
            memory: Math.floor(Math.random() * 40) + 30, // 30-70%
            disk: Math.floor(Math.random() * 20) + 60, // 60-80%
            network_in: Math.floor(Math.random() * 500) + 100, // 100-600 KB/s
            network_out: Math.floor(Math.random() * 300) + 50, // 50-350 KB/s
            requests: Math.floor(Math.random() * 2000) + 500, // 500-2500 req/s
            error_rate: Math.random() * 2, // 0-2%
            timestamp: Date.now()
        };
    }
    
    generateMockAlert() {
        const alerts = [
            {
                title: 'High CPU Usage',
                description: 'CPU usage above 80% for more than 5 minutes',
                severity: 'warning',
                service: 'compute'
            },
            {
                title: 'Database Connection Spike',
                description: 'Unusual number of database connections detected',
                severity: 'warning',
                service: 'database'
            },
            {
                title: 'Cache Memory High',
                description: 'Cache memory usage approaching limit',
                severity: 'info',
                service: 'cache'
            }
        ];
        
        return {
            id: `alert-${Date.now()}`,
            ...alerts[Math.floor(Math.random() * alerts.length)],
            timestamp: Date.now()
        };
    }
    
    generateSecurityEvent() {
        const events = [
            {
                title: 'Failed Login Attempt',
                description: 'Multiple failed login attempts from unknown IP',
                severity: 'medium',
                type: 'authentication'
            },
            {
                title: 'API Rate Limit Exceeded',
                description: 'API rate limit exceeded for user account',
                severity: 'low',
                type: 'api'
            },
            {
                title: 'Suspicious File Access',
                description: 'Unusual file access pattern detected',
                severity: 'high',
                type: 'data'
            }
        ];
        
        return {
            id: `sec-event-${Date.now()}`,
            ...events[Math.floor(Math.random() * events.length)],
            timestamp: Date.now(),
            source: 'security_monitor'
        };
    }
    
    // Route handlers
    getSystemMetrics(req, res) {
        res.json(this.generateMockMetrics());
    }
    
    getRegions(req, res) {
        // Mock regions data
        res.json([
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
            }
        ]);
    }
    
    getResources(req, res) {
        // Mock resources data
        res.json({
            compute: {
                total: 26,
                used: 18,
                available: 8,
                instances: [
                    { id: 'api-1', type: 'c5.xlarge', status: 'running', cpu: 65, memory: 72 },
                    { id: 'api-2', type: 'c5.xlarge', status: 'running', cpu: 58, memory: 68 }
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
        });
    }
    
    getInfrastructureSummary(req, res) {
        res.json({
            totalCost: 12500,
            monthlyTrend: -8,
            carbonFootprint: 2450,
            efficiencyScore: 87
        });
    }
    
    scaleResources(req, res) {
        // In a real implementation, this would interact with cloud provider APIs
        res.json({ 
            success: true, 
            message: 'Scaling operation initiated',
            operationId: `scale-${Date.now()}`
        });
    }
    
    getSecurityScore(req, res) {
        res.json({ score: 87 });
    }
    
    getThreats(req, res) {
        res.json([
            {
                id: 'threat-1',
                title: 'Brute Force Attempt',
                description: 'Multiple failed login attempts detected from IP 192.168.1.100',
                severity: 'high',
                timestamp: Date.now() - 3600000,
                status: 'active'
            }
        ]);
    }
    
    getIncidents(req, res) {
        res.json([
            {
                id: 'incident-1',
                title: 'Unauthorized Access Attempt',
                severity: 'critical',
                timestamp: Date.now() - 86400000,
                description: 'Multiple failed attempts to access admin panel',
                status: 'investigating',
                assignedTo: 'Security Team'
            }
        ]);
    }
    
    getSecurityControls(req, res) {
        res.json([
            {
                id: 'mfa',
                name: 'Multi-Factor Authentication',
                type: 'authentication',
                description: 'Require MFA for all user accounts',
                status: 'enabled',
                enabled: true
            }
        ]);
    }
    
    startSecurityScan(req, res) {
        res.json({ 
            success: true, 
            scanId: `scan-${Date.now()}`,
            estimatedCompletion: Date.now() + 300000 // 5 minutes
        });
    }
    
    getAPIKeys(req, res) {
        res.json([
            {
                id: 'key-1',
                name: 'Production API Key',
                key: 'sk_live_************1234',
                active: true,
                created: Date.now() - 86400000,
                lastUsed: Date.now() - 3600000
            }
        ]);
    }
    
    createAPIKey(req, res) {
        const { name } = req.body;
        const newKey = {
            id: `key-${Date.now()}`,
            name,
            key: `sk_live_${this.generateRandomString(32)}`,
            active: true,
            created: Date.now(),
            lastUsed: null
        };
        
        res.status(201).json(newKey);
    }
    
    activateAPIKey(req, res) {
        const { id } = req.params;
        res.json({ success: true, message: `API key ${id} activated` });
    }
    
    deleteAPIKey(req, res) {
        const { id } = req.params;
        res.json({ success: true, message: `API key ${id} deleted` });
    }
    
    getMetrics(req, res) {
        const { range } = req.query;
        
        // Generate historical data based on range
        const historical = this.generateHistoricalMetrics(range);
        
        res.json({
            current: this.generateMockMetrics(),
            historical: historical,
            range: range
        });
    }
    
    generateHistoricalMetrics(range) {
        const points = range === '1h' ? 60 : range === '24h' ? 144 : 168; // 7 days default
        return Array.from({ length: points }, (_, i) => ({
            timestamp: Date.now() - (i * (range === '1h' ? 60000 : range === '24h' ? 600000 : 3600000)),
            cpu: Math.floor(Math.random() * 30) + 40,
            memory: Math.floor(Math.random() * 40) + 30,
            network_in: Math.floor(Math.random() * 500) + 100,
            network_out: Math.floor(Math.random() * 300) + 50,
            error_rate: Math.random() * 2
        })).reverse();
    }
    
    exportMetrics(req, res) {
        const metrics = this.generateHistoricalMetrics('7d');
        
        // Convert to CSV
        const csv = this.convertToCSV(metrics);
        
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', 'attachment; filename=metrics-export.csv');
        res.send(csv);
    }
    
    convertToCSV(data) {
        const headers = Object.keys(data[0]).join(',');
        const rows = data.map(row => Object.values(row).join(','));
        return [headers, ...rows].join('\n');
    }
    
    getActivity(req, res) {
        // Mock activity data
        const activities = [
            {
                type: 'login',
                action: 'User logged in',
                timestamp: Date.now() - 300000
            },
            {
                type: 'transaction',
                action: 'Flash loan executed',
                timestamp: Date.now() - 600000
            },
            {
                type: 'deployment',
                action: 'New version deployed',
                timestamp: Date.now() - 900000
            }
        ];
        
        res.json(activities);
    }
    
    getSLAMetrics(req, res) {
        res.json({
            uptime: 99.99,
            responseTime: 100,
            supportResponse: 98
        });
    }
    
    getCurrentSystemStatus() {
        return {
            'api-gateway': { health: 'healthy', message: 'All systems operational' },
            'database': { health: 'healthy', message: 'Replication active' },
            'cache': { health: 'warning', message: 'High memory usage' },
            'cdn': { health: 'healthy', message: 'Global distribution' }
        };
    }
    
    getRecentAlerts() {
        return [this.generateMockAlert()];
    }
    
    generateRandomString(length) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }
    
    start(port = process.env.PORT || 3000) {
        this.app.listen(port, () => {
            console.log(`íº€ Enterprise API Server running on port ${port}`);
            console.log(`í´— WebSocket Server running on port ${process.env.WS_PORT || 8081}`);
            console.log(`í³Š Metrics collection active`);
        });
    }
}

// Start server if run directly
if (require.main === module) {
    const server = new EnterpriseAPIServer();
    server.start();
}

module.exports = EnterpriseAPIServer;
