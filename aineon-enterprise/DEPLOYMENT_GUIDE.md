# AINEON Enterprise - Production Deployment Guide

## 🎯 Overview

This guide provides step-by-step instructions for deploying the AINEON Enterprise Flash Loan Arbitrage Engine to production with real profit generation capabilities.

## 📋 Pre-Deployment Checklist

### Required Accounts & APIs

- [ ] **Ethereum RPC Provider**: Alchemy, Infura, or QuickNode account
- [ ] **Etherscan API Key**: Free from [etherscan.io/apis](https://etherscan.io/apis)
- [ ] **Ethereum Wallet**: With sufficient ETH for gas fees
- [ ] **Optional**: Pimlico account for gasless transactions

### Security Prerequisites

- [ ] Hardware wallet or secure key management
- [ ] Server with firewall configured
- [ ] SSL certificate for HTTPS (recommended)
- [ ] Backup and recovery procedures

## 🚀 Quick Production Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8+
sudo apt install python3 python3-pip python3-venv nginx -y

# Create application user
sudo useradd -m -s /bin/bash aineon
sudo usermod -aG sudo aineon

# Switch to application user
sudo su - aineon
```

### 2. Application Deployment

```bash
# Clone repository
git clone https://github.com/your-username/aineon-enterprise.git
cd aineon-enterprise

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install application
pip install -e .
```

### 3. Environment Configuration

```bash
# Create production environment file
cat > .env << EOF
# REQUIRED: Ethereum Configuration
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
WALLET_ADDRESS=0xYourWalletAddress
PRIVATE_KEY=0xYourPrivateKey

# REQUIRED: Etherscan Verification
ETHERSCAN_API_KEY=YourEtherscanAPIKey

# OPTIONAL: Enhanced Features
PAYMASTER_URL=https://api.pimlico.io/v1/mainnet/rpc?apikey=YourPimlicoKey
PROFIT_WALLET=0xYourProfitWalletAddress
PORT=8081
ENVIRONMENT=production
LOG_LEVEL=INFO

# OPTIONAL: Risk Management
RISK_TIER=balanced
MAX_DAILY_LOSS_USD=100000
MIN_PROFIT_THRESHOLD_ETH=0.01
EOF
```

### 4. Systemd Service Setup

```bash
# Create systemd service
sudo tee /etc/systemd/system/aineon.service > /dev/null <<EOF
[Unit]
Description=AINEON Enterprise Flash Loan Engine
After=network.target

[Service]
Type=simple
User=aineon
Group=aineon
WorkingDirectory=/home/aineon/aineon-enterprise
Environment=PATH=/home/aineon/aineon-enterprise/venv/bin
ExecStart=/home/aineon/aineon-enterprise/venv/bin/python core/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aineon

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/aineon/aineon-enterprise

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable aineon
sudo systemctl start aineon

# Check status
sudo systemctl status aineon
```

### 5. Nginx Reverse Proxy (Optional)

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/aineon > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/aineon /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🐳 Docker Deployment

### 1. Build Production Image

```bash
# Build optimized image
docker build -f Dockerfile.production -t aineon-enterprise:latest .

# Tag for registry
docker tag aineon-enterprise:latest your-registry/aineon-enterprise:latest
```

### 2. Docker Compose Setup

```bash
# Create docker-compose.prod.yml
cat > docker-compose.prod.yml <<EOF
version: '3.8'

services:
  aineon-engine:
    image: aineon-enterprise:latest
    container_name: aineon-engine
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      - ETH_RPC_URL=\${ETH_RPC_URL}
      - WALLET_ADDRESS=\${WALLET_ADDRESS}
      - PRIVATE_KEY=\${PRIVATE_KEY}
      - ETHERSCAN_API_KEY=\${ETHERSCAN_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - aineon-network
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp

  nginx:
    image: nginx:alpine
    container_name: aineon-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - aineon-engine
    networks:
      - aineon-network

networks:
  aineon-network:
    driver: bridge

volumes:
  logs:
  data:
EOF

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Configuration Management

### Risk Profiles

Choose appropriate risk profile based on your capital and risk tolerance:

#### Conservative Profile
```bash
export RISK_TIER=conservative
export MAX_PER_TRADE_USD=10000
export MAX_DAILY_LOSS_USD=100000
export MIN_CONFIDENCE_THRESHOLD=0.80
```

#### Balanced Profile (Recommended)
```bash
export RISK_TIER=balanced
export MAX_PER_TRADE_USD=100000
export MAX_DAILY_LOSS_USD=1500000
export MIN_CONFIDENCE_THRESHOLD=0.75
```

#### Aggressive Profile
```bash
export RISK_TIER=aggressive
export MAX_PER_TRADE_USD=1000000
export MAX_DAILY_LOSS_USD=15000000
export MIN_CONFIDENCE_THRESHOLD=0.70
```

### Monitoring Configuration

```bash
# Enable monitoring
export MONITORING_ENABLED=true
export PROMETHEUS_ENABLED=true
export GRAFANA_ENABLED=true

# Alert thresholds
export PROFIT_ALERT_THRESHOLD_ETH=50
export LOSS_ALERT_THRESHOLD_ETH=10
export ERROR_RATE_ALERT_THRESHOLD=0.05
```

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Check service status
sudo systemctl status aineon

# Check logs
sudo journalctl -u aineon -f

# Check API health
curl http://localhost:8081/health

# Check detailed status
curl http://localhost:8081/status
```

### Performance Monitoring

```bash
# Monitor resource usage
htop
iotop
netstat -tulpn

# Monitor logs in real-time
tail -f /var/log/aineon/engine.log
```

### Maintenance Tasks

```bash
# Daily maintenance script
cat > /home/aineon/maintenance.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# Backup logs
tar -czf /backup/logs_$DATE.tar.gz /var/log/aineon/

# Check disk space
df -h | awk '$5 > 80 {print "WARNING: Disk space low on " $1}'

# Restart service if needed
if ! systemctl is-active --quiet aineon; then
    echo "Service down, restarting..."
    sudo systemctl restart aineon
fi

# Clean old log files
find /var/log/aineon/ -name "*.log" -mtime +7 -delete

echo "Maintenance completed: $DATE"
EOF

chmod +x /home/aineon/maintenance.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /home/aineon/maintenance.sh >> /var/log/aineon/maintenance.log 2>&1") | crontab -
```

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
sudo journalctl -u aineon -n 50

# Verify environment
python3 -c "import os; print([k for k in os.environ if 'ETH' in k or 'WALLET' in k])"

# Test RPC connection
python3 -c "from web3 import Web3; w3 = Web3(Web3.HTTPProvider('$ETH_RPC_URL')); print('RPC OK:', w3.is_connected())"
```

#### No Arbitrage Opportunities
- Check market volatility (low volatility = fewer opportunities)
- Verify DEX API endpoints
- Adjust minimum profit thresholds
- Check gas price settings

#### High Failure Rate
- Review error logs for patterns
- Check RPC provider reliability
- Verify wallet has sufficient ETH for gas
- Consider switching to more reliable RPC

### Emergency Procedures

#### Stop Trading Immediately
```bash
# Emergency stop
sudo systemctl stop aineon

# Or send HTTP request
curl -X POST http://localhost:8081/emergency-stop
```

#### Emergency Fund Transfer
```bash
# Manual fund transfer
python3 -c "
from core.profit_manager import ProfitManager
from web3 import Web3
import os

w3 = Web3(Web3.HTTPProvider(os.getenv('ETH_RPC_URL')))
pm = ProfitManager(w3, os.getenv('WALLET_ADDRESS'), os.getenv('PRIVATE_KEY'))
result = asyncio.run(pm.manual_transfer_profits(pm.accumulated_eth, os.getenv('PROFIT_WALLET')))
print('Transfer result:', result)
"
```

## 🔒 Security Best Practices

### Server Security

```bash
# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8081  # Block direct access to engine port

# Update system regularly
sudo apt update && sudo apt upgrade -y

# Install fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Application Security

```bash
# Set proper file permissions
chmod 600 .env
chown aineon:aineon .env

# Use secrets management (recommended)
# AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
```

## 📈 Scaling Considerations

### Horizontal Scaling

For high-volume trading, consider:

- Load balancer with multiple engine instances
- Redis for shared state management
- Database for persistent profit tracking
- Message queue for async operations

### Performance Optimization

```bash
# Use premium RPC endpoints
# Enable connection pooling
# Optimize database queries
# Implement caching strategies
```

## 📞 Support

For production support:

- 📧 Emergency: emergency@aineon.io
- 📊 Status: status.aineon.io
- 📖 Docs: docs.aineon.io
- 💬 Discord: [Production Support](https://discord.gg/aineon-prod)

---

**🎯 Ready for Production**: Follow this guide to deploy a production-ready AINEON Enterprise engine capable of generating real profits through automated DeFi arbitrage.