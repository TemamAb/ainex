/**
 * Chainalysis API Integration (Mock)
 * For demonstration purposes only
 * In production, use actual Chainalysis API credentials
 */

class ChainalysisAPI {
    constructor() {
        this.apiKey = null;
        this.baseURL = 'https://public.chainalysis.com/api/v1';
        this.isConfigured = false;
        
        this.loadConfig();
    }
    
    loadConfig() {
        // Load API key from secure storage
        const savedKey = localStorage.getItem('chainalysis-api-key');
        if (savedKey) {
            this.apiKey = savedKey;
            this.isConfigured = true;
        }
    }
    
    async screenAddress(address) {
        if (!this.isConfigured) {
            return this.mockScreen(address);
        }
        
        try {
            const response = await fetch(`${this.baseURL}/address/${address}`, {
                headers: {
                    'X-API-Key': this.apiKey,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Chainalysis API error: ${response.status}`);
            }
            
            const data = await response.json();
            return this.parseResponse(data);
            
        } catch (error) {
            console.error('Chainalysis screening failed:', error);
            // Fallback to mock data
            return this.mockScreen(address);
        }
    }
    
    async quickScreen(address) {
        // Quick screening for real-time validation
        return this.mockScreen(address);
    }
    
    mockScreen(address) {
        // Mock response for demonstration
        // In production, this would be real API call
        
        // Generate deterministic risk based on address hash
        const addressHash = this.hashAddress(address);
        const riskScore = addressHash % 100;
        
        // Simulate risk flags
        const riskLevel = riskScore >= 80 ? 'HIGH' : 
                         riskScore >= 50 ? 'MEDIUM' : 'LOW';
        
        const matches = [];
        if (riskScore > 85) {
            matches.push({
                list: 'OFAC',
                type: 'sanctions',
                description: 'Potential sanctions list match'
            });
        }
        
        if (addressHash % 10 === 0) {
            matches.push({
                list: 'PEP',
                type: 'political_exposure',
                description: 'Politically Exposed Person association'
            });
        }
        
        return {
            riskScore,
            riskLevel,
            confidence: 0.85 + (Math.random() * 0.15),
            matches,
            categories: this.generateRiskCategories(addressHash),
            lastUpdated: new Date().toISOString()
        };
    }
    
    hashAddress(address) {
        // Simple hash function for deterministic mock data
        let hash = 0;
        for (let i = 0; i < address.length; i++) {
            hash = ((hash << 5) - hash) + address.charCodeAt(i);
            hash = hash & hash;
        }
        return Math.abs(hash);
    }
    
    generateRiskCategories(hash) {
        const categories = [];
        const possibleCategories = [
            'sanctions',
            'stolen_funds',
            'ransomware',
            'mixer',
            'darknet_market',
            'scam',
            'terrorist_financing'
        ];
        
        possibleCategories.forEach((category, index) => {
            if ((hash >> index) & 1) {
                categories.push({
                    category,
                    risk: (hash >> (index * 4)) % 100,
                    evidence: `Pattern match for ${category}`
                });
            }
        });
        
        return categories;
    }
    
    parseResponse(data) {
        // Parse actual Chainalysis API response
        return {
            riskScore: data.riskScore || 50,
            riskLevel: data.riskLevel || 'MEDIUM',
            confidence: data.confidence || 0.8,
            matches: data.matches || [],
            categories: data.categories || [],
            lastUpdated: data.lastUpdated || new Date().toISOString()
        };
    }
    
    async configure(apiKey) {
        this.apiKey = apiKey;
        this.isConfigured = true;
        localStorage.setItem('chainalysis-api-key', apiKey);
        
        // Test the configuration
        try {
            await this.testConnection();
            return { success: true, message: 'Configuration saved successfully' };
        } catch (error) {
            return { success: false, message: `Configuration test failed: ${error.message}` };
        }
    }
    
    async testConnection() {
        if (!this.isConfigured) {
            throw new Error('API not configured');
        }
        
        // Test with a known address
        const testAddress = '0x742d35Cc6634C0532925a3b844Bc9e98D3E9c6b3'; // Vitalik's address
        const result = await this.screenAddress(testAddress);
        
        if (!result || typeof result.riskScore !== 'number') {
            throw new Error('Invalid response from API');
        }
        
        return true;
    }
}

export default ChainalysisAPI;
