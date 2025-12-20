/**
 * AINEON Enterprise - API Console
 * Developer & Integration Interface
 */

class APIConsole {
    constructor(enterpriseDashboard) {
        this.dashboard = enterpriseDashboard;
        this.endpoints = [];
        this.currentEndpoint = null;
        this.apiKeys = [];
        this.rateLimits = {};
        
        this.initialize();
    }
    
    async initialize() {
        console.log('í´Œ Initializing API Console...');
        
        // Load API documentation
        await this.loadAPIDocumentation();
        
        // Load API keys
        await this.loadAPIKeys();
        
        // Load rate limits
        await this.loadRateLimits();
        
        // Initialize UI
        this.initUI();
        
        // Initialize event listeners
        this.initEventListeners();
    }
    
    async loadAPIDocumentation() {
        try {
            const response = await fetch('/api/openapi.json');
            if (response.ok) {
                const openapi = await response.json();
                this.processOpenAPI(openapi);
            } else {
                // Fallback to mock data
                this.loadMockEndpoints();
            }
        } catch (error) {
            console.error('Failed to load API documentation:', error);
            this.loadMockEndpoints();
        }
    }
    
    processOpenAPI(openapi) {
        this.endpoints = [];
        
        // Process paths
        Object.entries(openapi.paths || {}).forEach(([path, methods]) => {
            Object.entries(methods).forEach(([method, details]) => {
                this.endpoints.push({
                    path,
                    method: method.toUpperCase(),
                    summary: details.summary || '',
                    description: details.description || '',
                    parameters: details.parameters || [],
                    requestBody: details.requestBody,
                    responses: details.responses
                });
            });
        });
        
        this.updateEndpointList();
    }
    
    loadMockEndpoints() {
        // Mock endpoints for demonstration
        this.endpoints = [
            {
                path: '/api/v1/transactions',
                method: 'GET',
                summary: 'Get transactions',
                description: 'Retrieve a list of transactions with filtering and pagination',
                parameters: [
                    { name: 'limit', in: 'query', description: 'Number of results to return', required: false },
                    { name: 'offset', in: 'query', description: 'Starting offset', required: false },
                    { name: 'wallet', in: 'query', description: 'Filter by wallet address', required: false }
                ]
            },
            {
                path: '/api/v1/wallets/{address}',
                method: 'GET',
                summary: 'Get wallet details',
                description: 'Retrieve detailed information about a specific wallet',
                parameters: [
                    { name: 'address', in: 'path', description: 'Wallet address', required: true }
                ]
            },
            {
                path: '/api/v1/flash-loans',
                method: 'POST',
                summary: 'Execute flash loan',
                description: 'Execute a flash loan transaction',
                requestBody: {
                    required: true,
                    content: {
                        'application/json': {
                            schema: {
                                type: 'object',
                                properties: {
                                    amount: { type: 'string' },
                                    token: { type: 'string' },
                                    protocol: { type: 'string' },
                                    strategy: { type: 'string' }
                                }
                            }
                        }
                    }
                }
            },
            {
                path: '/api/v1/compliance/screen',
                method: 'POST',
                summary: 'Screen wallet address',
                description: 'Perform compliance screening on a wallet address',
                requestBody: {
                    required: true,
                    content: {
                        'application/json': {
                            schema: {
                                type: 'object',
                                properties: {
                                    address: { type: 'string' },
                                    providers: { type: 'array', items: { type: 'string' } }
                                }
                            }
                        }
                    }
                }
            },
            {
                path: '/api/v1/reports/generate',
                method: 'POST',
                summary: 'Generate report',
                description: 'Generate institutional reports',
                requestBody: {
                    required: true,
                    content: {
                        'application/json': {
                            schema: {
                                type: 'object',
                                properties: {
                                    type: { type: 'string' },
                                    startDate: { type: 'string' },
                                    endDate: { type: 'string' },
                                    format: { type: 'string' }
                                }
                            }
                        }
                    }
                }
            }
        ];
        
        this.updateEndpointList();
    }
    
    updateEndpointList() {
        const list = document.getElementById('api-endpoint-list');
        if (!list) return;
        
        list.innerHTML = this.endpoints.map(endpoint => `
            <div class="api-endpoint" data-endpoint="${endpoint.path}">
                <div class="endpoint-method method-${endpoint.method.toLowerCase()}">
                    ${endpoint.method}
                </div>
                <div class="endpoint-path">${endpoint.path}</div>
                <div class="endpoint-description">${endpoint.summary}</div>
            </div>
        `).join('');
        
        // Add click listeners
        document.querySelectorAll('.api-endpoint').forEach(item => {
            item.addEventListener('click', (e) => {
                const path = e.currentTarget.dataset.endpoint;
                this.selectEndpoint(path);
            });
        });
    }
    
    selectEndpoint(path) {
        const endpoint = this.endpoints.find(e => e.path === path);
        if (!endpoint) return;
        
        this.currentEndpoint = endpoint;
        
        // Update active state
        document.querySelectorAll('.api-endpoint').forEach(item => {
            item.classList.toggle('active', item.dataset.endpoint === path);
        });
        
        // Update request builder
        this.updateRequestBuilder(endpoint);
    }
    
    updateRequestBuilder(endpoint) {
        // Update method selector
        const methodBtns = document.querySelectorAll('.method-btn');
        methodBtns.forEach(btn => {
            btn.classList.toggle('active', btn.textContent === endpoint.method);
        });
        
        // Update URL
        const urlInput = document.getElementById('request-url');
        if (urlInput) {
            const baseUrl = window.location.origin;
            urlInput.value = `${baseUrl}${endpoint.path}`;
        }
        
        // Update parameters
        this.updateParameters(endpoint.parameters);
        
        // Update request body
        this.updateRequestBody(endpoint.requestBody);
        
        // Update headers
        this.updateHeaders(endpoint);
    }
    
    updateParameters(parameters) {
        const paramsContainer = document.getElementById('query-params-list');
        if (!paramsContainer) return;
        
        paramsContainer.innerHTML = '';
        
        (parameters || []).forEach(param => {
            if (param.in === 'query') {
                const row = document.createElement('div');
                row.className = 'parameter-row';
                row.innerHTML = `
                    <input type="text" class="param-key" value="${param.name}" readonly>
                    <input type="text" class="param-value" placeholder="${param.description || 'Enter value'}">
                    <button class="remove-param">&times;</button>
                `;
                paramsContainer.appendChild(row);
            }
        });
    }
    
    updateRequestBody(requestBody) {
        const editor = document.getElementById('request-body-editor');
        if (!editor) return;
        
        if (requestBody) {
            const schema = requestBody.content?.['application/json']?.schema;
            if (schema) {
                const example = this.generateExampleFromSchema(schema);
                editor.value = JSON.stringify(example, null, 2);
            } else {
                editor.value = '{}';
            }
        } else {
            editor.value = '';
        }
    }
    
    generateExampleFromSchema(schema) {
        const example = {};
        
        if (schema.properties) {
            Object.entries(schema.properties).forEach(([key, prop]) => {
                if (prop.type === 'string') {
                    example[key] = 'example_value';
                } else if (prop.type === 'number') {
                    example[key] = 123.45;
                } else if (prop.type === 'integer') {
                    example[key] = 100;
                } else if (prop.type === 'boolean') {
                    example[key] = true;
                } else if (prop.type === 'array') {
                    example[key] = [];
                } else if (prop.type === 'object') {
                    example[key] = {};
                }
            });
        }
        
        return example;
    }
    
    updateHeaders(endpoint) {
        const headersContainer = document.getElementById('headers-list');
        if (!headersContainer) return;
        
        headersContainer.innerHTML = '';
        
        // Default headers
        const defaultHeaders = [
            { key: 'Content-Type', value: 'application/json' },
            { key: 'Accept', value: 'application/json' }
        ];
        
        // Add API key header if available
        const activeKey = this.apiKeys.find(key => key.active);
        if (activeKey) {
            defaultHeaders.push({ key: 'X-API-Key', value: activeKey.key });
        }
        
        defaultHeaders.forEach(header => {
            const row = document.createElement('div');
            row.className = 'header-row';
            row.innerHTML = `
                <input type="text" class="param-key" value="${header.key}" readonly>
                <input type="text" class="param-value" value="${header.value}">
                <button class="remove-param">&times;</button>
            `;
            headersContainer.appendChild(row);
        });
    }
    
    async loadAPIKeys() {
        try {
            const response = await fetch('/api/keys');
            if (response.ok) {
                this.apiKeys = await response.json();
                this.updateAPIKeysDisplay();
            }
        } catch (error) {
            console.error('Failed to load API keys:', error);
        }
    }
    
    updateAPIKeysDisplay() {
        const keysList = document.getElementById('api-keys-list');
        if (!keysList) return;
        
        keysList.innerHTML = this.apiKeys.map(key => `
            <div class="api-key-item ${key.active ? 'active' : ''}">
                <div class="key-info">
                    <span class="key-name">${key.name}</span>
                    <span class="key-prefix">${key.key.substring(0, 8)}...${key.key.substring(key.key.length - 4)}</span>
                </div>
                <div class="key-actions">
                    <button class="btn btn-sm ${key.active ? 'btn-secondary' : 'btn-primary'}" 
                            data-action="${key.active ? 'deactivate' : 'activate'}" 
                            data-key="${key.id}">
                        ${key.active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button class="btn btn-sm btn-error" data-action="delete" data-key="${key.id}">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    async loadRateLimits() {
        try {
            const response = await fetch('/api/rate-limits');
            if (response.ok) {
                this.rateLimits = await response.json();
                this.updateRateLimitsDisplay();
            }
        } catch (error) {
            console.error('Failed to load rate limits:', error);
        }
    }
    
    updateRateLimitsDisplay() {
        const limitsContainer = document.getElementById('rate-limits-display');
        if (!limitsContainer) return;
        
        limitsContainer.innerHTML = Object.entries(this.rateLimits).map(([endpoint, limit]) => `
            <div class="rate-limit-item">
                <span class="endpoint">${endpoint}</span>
                <span class="limit">${limit.limit} requests per ${limit.period}</span>
                <span class="remaining">${limit.remaining} remaining</span>
            </div>
        `).join('');
    }
    
    initUI() {
        // Initialize code editor
        this.initCodeEditor();
        
        // Initialize response viewer
        this.initResponseViewer();
    }
    
    initCodeEditor() {
        const editor = document.getElementById('request-body-editor');
        if (editor) {
            editor.addEventListener('input', () => {
                this.formatJSONEditor(editor);
            });
        }
    }
    
    formatJSONEditor(editor) {
        try {
            const json = JSON.parse(editor.value);
            editor.value = JSON.stringify(json, null, 2);
            editor.classList.remove('error');
        } catch (error) {
            editor.classList.add('error');
        }
    }
    
    initResponseViewer() {
        // Response viewer is initialized with default state
    }
    
    initEventListeners() {
        // Send request button
        const sendBtn = document.getElementById('send-request');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendRequest());
        }
        
        // Format JSON button
        const formatBtn = document.getElementById('format-json');
        if (formatBtn) {
            formatBtn.addEventListener('click', () => {
                const editor = document.getElementById('request-body-editor');
                this.formatJSONEditor(editor);
            });
        }
        
        // Add parameter button
        const addParamBtn = document.getElementById('add-param');
        if (addParamBtn) {
            addParamBtn.addEventListener('click', () => this.addParameter());
        }
        
        // Add header button
        const addHeaderBtn = document.getElementById('add-header');
        if (addHeaderBtn) {
            addHeaderBtn.addEventListener('click', () => this.addHeader());
        }
        
        // Remove parameter/header buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-param')) {
                e.target.closest('.parameter-row, .header-row').remove();
            }
        });
        
        // API key management
        document.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            const keyId = e.target.dataset.key;
            
            if (action && keyId) {
                if (action === 'activate') this.activateAPIKey(keyId);
                if (action === 'deactivate') this.deactivateAPIKey(keyId);
                if (action === 'delete') this.deleteAPIKey(keyId);
            }
        });
        
        // Create new API key
        const createKeyBtn = document.getElementById('create-api-key');
        if (createKeyBtn) {
            createKeyBtn.addEventListener('click', () => this.createAPIKey());
        }
        
        // SDK download buttons
        document.querySelectorAll('.sdk-download-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sdk = e.target.dataset.sdk;
                this.downloadSDK(sdk);
            });
        });
    }
    
    async sendRequest() {
        if (!this.currentEndpoint) {
            this.dashboard.showError('Please select an endpoint first');
            return;
        }
        
        const urlInput = document.getElementById('request-url');
        const method = this.currentEndpoint.method;
        const url = urlInput.value;
        
        // Collect headers
        const headers = {};
        document.querySelectorAll('#headers-list .header-row').forEach(row => {
            const key = row.querySelector('.param-key').value;
            const value = row.querySelector('.param-value').value;
            if (key && value) {
                headers[key] = value;
            }
        });
        
        // Collect query parameters
        const queryParams = new URLSearchParams();
        document.querySelectorAll('#query-params-list .parameter-row').forEach(row => {
            const key = row.querySelector('.param-key').value;
            const value = row.querySelector('.param-value').value;
            if (key && value) {
                queryParams.append(key, value);
            }
        });
        
        // Get request body
        let body = null;
        const editor = document.getElementById('request-body-editor');
        if (editor && editor.value.trim()) {
            try {
                body = JSON.parse(editor.value);
            } catch (error) {
                this.dashboard.showError('Invalid JSON in request body');
                return;
            }
        }
        
        // Construct final URL with query parameters
        const finalUrl = queryParams.toString() ? `${url}?${queryParams.toString()}` : url;
        
        // Show loading state
        this.showLoadingState(true);
        
        try {
            const startTime = Date.now();
            const response = await fetch(finalUrl, {
                method,
                headers,
                body: body ? JSON.stringify(body) : null
            });
            const endTime = Date.now();
            
            const responseTime = endTime - startTime;
            const responseData = await response.text();
            
            // Update response display
            this.updateResponseDisplay(response, responseData, responseTime);
            
            // Track API usage
            this.trackAPIUsage(method, url, response.status, responseTime);
            
        } catch (error) {
            this.updateResponseDisplay(null, error.message, 0);
        } finally {
            this.showLoadingState(false);
        }
    }
    
    updateResponseDisplay(response, data, responseTime) {
        const statusElement = document.getElementById('response-status');
        const timeElement = document.getElementById('response-time');
        const bodyElement = document.getElementById('response-body');
        
        if (response) {
            // Update status
            const statusClass = response.status >= 400 ? 'error' : response.status >= 300 ? 'warning' : 'success';
            statusElement.textContent = response.status;
            statusElement.className = `status-code ${statusClass}`;
            
            // Update response time
            timeElement.textContent = `${responseTime}ms`;
            
            // Update response body
            try {
                const json = JSON.parse(data);
                bodyElement.textContent = JSON.stringify(json, null, 2);
                bodyElement.className = 'response-content json';
            } catch {
                bodyElement.textContent = data;
                bodyElement.className = 'response-content';
            }
        } else {
            // Error case
            statusElement.textContent = 'Error';
            statusElement.className = 'status-code error';
            timeElement.textContent = '0ms';
            bodyElement.textContent = data;
            bodyElement.className = 'response-content error';
        }
    }
    
    showLoadingState(loading) {
        const sendBtn = document.getElementById('send-request');
        if (sendBtn) {
            if (loading) {
                sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
                sendBtn.disabled = true;
            } else {
                sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Request';
                sendBtn.disabled = false;
            }
        }
    }
    
    trackAPIUsage(method, endpoint, status, responseTime) {
        // Track API usage for analytics
        const usage = {
            method,
            endpoint,
            status,
            responseTime,
            timestamp: Date.now()
        };
        
        // Store locally
        const usageLog = JSON.parse(localStorage.getItem('api-usage-log') || '[]');
        usageLog.push(usage);
        
        // Keep only last 1000 requests
        if (usageLog.length > 1000) {
            usageLog.splice(0, usageLog.length - 1000);
        }
        
        localStorage.setItem('api-usage-log', JSON.stringify(usageLog));
    }
    
    addParameter() {
        const container = document.getElementById('query-params-list');
        const row = document.createElement('div');
        row.className = 'parameter-row';
        row.innerHTML = `
            <input type="text" class="param-key" placeholder="Parameter name">
            <input type="text" class="param-value" placeholder="Value">
            <button class="remove-param">&times;</button>
        `;
        container.appendChild(row);
    }
    
    addHeader() {
        const container = document.getElementById('headers-list');
        const row = document.createElement('div');
        row.className = 'header-row';
        row.innerHTML = `
            <input type="text" class="param-key" placeholder="Header name">
            <input type="text" class="param-value" placeholder="Value">
            <button class="remove-param">&times;</button>
        `;
        container.appendChild(row);
    }
    
    async activateAPIKey(keyId) {
        try {
            const response = await fetch(`/api/keys/${keyId}/activate`, { method: 'POST' });
            if (response.ok) {
                await this.loadAPIKeys();
                this.dashboard.showSuccess('API key activated');
            }
        } catch (error) {
            this.dashboard.showError('Failed to activate API key');
        }
    }
    
    async deactivateAPIKey(keyId) {
        try {
            const response = await fetch(`/api/keys/${keyId}/deactivate`, { method: 'POST' });
            if (response.ok) {
                await this.loadAPIKeys();
                this.dashboard.showSuccess('API key deactivated');
            }
        } catch (error) {
            this.dashboard.showError('Failed to deactivate API key');
        }
    }
    
    async deleteAPIKey(keyId) {
        const confirmed = await this.dashboard.showConfirmation(
            'Delete API Key',
            'Are you sure you want to delete this API key? This action cannot be undone.'
        );
        
        if (confirmed) {
            try {
                const response = await fetch(`/api/keys/${keyId}`, { method: 'DELETE' });
                if (response.ok) {
                    await this.loadAPIKeys();
                    this.dashboard.showSuccess('API key deleted');
                }
            } catch (error) {
                this.dashboard.showError('Failed to delete API key');
            }
        }
    }
    
    async createAPIKey() {
        const name = prompt('Enter a name for the new API key:');
        if (!name) return;
        
        try {
            const response = await fetch('/api/keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            
            if (response.ok) {
                const key = await response.json();
                await this.loadAPIKeys();
                
                // Show the key to the user (only once!)
                this.showNewAPIKey(key);
            }
        } catch (error) {
            this.dashboard.showError('Failed to create API key');
        }
    }
    
    showNewAPIKey(key) {
        const modal = document.createElement('div');
        modal.className = 'api-key-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-key"></i> New API Key Created</h3>
                </div>
                <div class="modal-body">
                    <p><strong>Warning:</strong> This is the only time the API key will be shown. Copy it now and store it securely.</p>
                    <div class="api-key-display">
                        <code>${key.key}</code>
                        <button class="btn btn-sm" id="copy-api-key">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-primary" id="close-key-modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Copy button
        modal.querySelector('#copy-api-key').addEventListener('click', () => {
            navigator.clipboard.writeText(key.key);
            this.dashboard.showSuccess('API key copied to clipboard');
        });
        
        // Close button
        modal.querySelector('#close-key-modal').addEventListener('click', () => {
            modal.remove();
        });
    }
    
    async downloadSDK(sdk) {
        try {
            const response = await fetch(`/api/sdk/${sdk}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `aineon-sdk-${sdk}.zip`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.dashboard.showSuccess(`SDK for ${sdk} downloaded`);
            }
        } catch (error) {
            this.dashboard.showError('Failed to download SDK');
        }
    }
}

export default APIConsole;
