# 🚀 AINEON Production Deployment - ETH Mainnet

## Overview

This deployment sets up AINEON's elite-tier arbitrage dashboards on Ethereum mainnet with real-time profit monitoring and automated trading capabilities.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Profit        │    │   API Backend    │    │   ETH Mainnet   │
│   Dashboard     │◄──►│   (FastAPI)      │◄──►│   RPC Nodes     │
│   (Streamlit)   │    │                  │    │   • Infura      │
└─────────────────┘    └──────────────────┘    │   • Alchemy     │
                                               │   • QuickNode   │
┌─────────────────┐    ┌──────────────────┐    └─────────────────┘
│   Monitoring    │    │   Redis Cache    │
│   Dashboard     │◄──►│   (Optional)     │
│   (Streamlit)   │    └──────────────────┘
└─────────────────┘
```

## Prerequisites

### Required API Keys

1. **Etherscan API Key** - For transaction verification
   - Get from: https://etherscan.io/apis
   - Set as: `ETHERSCAN_API_KEY`

2. **Infura Project ID** - For ETH mainnet RPC
   - Get from: https://infura.io/
   - Set as: `INFURA_PROJECT_ID`

3. **Alchemy API Key** (Optional) - Additional RPC redundancy
   - Get from: https://alchemy.com/
   - Set as: `ALCHEMY_API_KEY`

### System Requirements

- Docker & Docker Compose
- 4GB RAM minimum
- 2 CPU cores minimum
- Linux/Windows/MacOS

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.production .env

# Edit with your API keys
nano .env
```

### 2. Local Testing

```bash
# Test locally with Docker Compose
./deploy-production.sh local

# Check services are running
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### 3. Production Deployment

#### Option A: Render (Recommended)

```bash
# Deploy to Render
./deploy-production.sh render
```

#### Option B: Vercel

```bash
# Deploy dashboards to Vercel
./deploy-production.sh vercel
```

#### Option C: AWS

```bash
# Deploy to AWS ECS
./deploy-production.sh aws
```

## Services

### 1. API Backend (`aineon-api`)
- **Port**: 8000
- **Health Check**: `GET /api/profit`
- **Features**:
  - Real-time profit tracking
  - Withdrawal management
  - DEX arbitrage monitoring
  - Gas price optimization

### 2. Profit Dashboard (`aineon-profit-dashboard`)
- **Port**: 8501
- **Features**:
  - Live profit charts
  - DEX arbitrage opportunities
  - Gas price monitoring
  - Transaction history

### 3. Monitoring Dashboard (`aineon-monitoring-dashboard`)
- **Port**: 8502
- **Features**:
  - System health monitoring
  - Risk management
  - Performance analytics
  - Alert configuration

## Configuration

### Environment Variables

```bash
# Required
ETHERSCAN_API_KEY=your_etherscan_key
INFURA_PROJECT_ID=your_infura_project_id
ETH_MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID

# Optional
ALCHEMY_API_KEY=your_alchemy_key
QUICKNODE_ENDPOINT=your_quicknode_url
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis:6379/0

# Risk Management
MAX_SLIPPAGE_PERCENT=2.0
MAX_POSITION_SIZE_USD=10000
MIN_PROFIT_THRESHOLD_ETH=0.001

# Monitoring
DISCORD_WEBHOOK_URL=your_discord_webhook
TELEGRAM_BOT_TOKEN=your_telegram_token
```

### Risk Parameters

```bash
# Gas Management
MAX_GAS_PRICE_GWEI=100
GAS_MULTIPLIER=1.2

# Position Limits
MAX_SLIPPAGE_PERCENT=2.0
MAX_POSITION_SIZE_USD=10000

# Profit Thresholds
MIN_PROFIT_THRESHOLD_ETH=0.001
AUTO_WITHDRAWAL_THRESHOLD=0.1
```

## API Endpoints

### Profit Data
- `GET /api/profit` - Current profit metrics
- `GET /api/profit/history` - Historical profit data

### DEX Monitoring
- `GET /api/dex/opportunities` - Live arbitrage opportunities
- `GET /api/dex/prices` - Current DEX prices

### Gas Monitoring
- `GET /api/gas/prices` - Current gas prices
- `GET /api/gas/history` - Gas price history

### Transaction Monitoring
- `GET /api/transactions/recent` - Recent transactions
- `GET /api/transactions/pending` - Pending transactions

## Monitoring & Alerts

### Health Checks

```bash
# API Health
curl http://your-domain:8000/api/profit

# Dashboard Health
curl http://your-domain:8501
curl http://your-domain:8502
```

### Alert Configuration

Alerts are triggered for:
- Profit threshold breaches
- Gas price spikes
- Network congestion
- System failures
- Large position changes

### Logging

Logs are available at:
- `/app/logs/aineon.log` (API)
- Docker container logs
- Cloud provider logging services

## Security

### API Security
- Rate limiting (60 requests/minute)
- CORS protection
- Input validation
- JWT authentication (optional)

### Network Security
- HTTPS encryption
- Firewall rules
- API key protection
- Private networking (cloud)

### Wallet Security
- Encrypted private keys
- Multi-signature requirements
- Withdrawal limits
- Audit trails

## Scaling

### Horizontal Scaling

```bash
# Scale API instances
docker-compose up -d --scale aineon-api=3

# Load balancer configuration required
```

### Database Scaling

For high-frequency trading:
- PostgreSQL for transaction history
- Redis for caching
- Time-series database for metrics

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```bash
   # Check API logs
   docker logs aineon-api-prod

   # Test connectivity
   curl http://localhost:8000/api/profit
   ```

2. **Dashboard Not Loading**
   ```bash
   # Check dashboard logs
   docker logs aineon-profit-dashboard-prod

   # Restart service
   docker restart aineon-profit-dashboard-prod
   ```

3. **High Gas Prices**
   - Adjust `MAX_GAS_PRICE_GWEI`
   - Enable gas optimization
   - Monitor network congestion

### Performance Optimization

```bash
# Enable Redis caching
docker-compose -f docker-compose.production.yml up redis

# Adjust worker counts
export WEB_CONCURRENCY=4
export GUNICORN_WORKERS=4
```

## Backup & Recovery

### Automated Backups

```bash
# Database backup (if using PostgreSQL)
pg_dump aineon_prod > backup_$(date +%Y%m%d).sql

# Configuration backup
cp .env.production .env.production.backup
```

### Recovery Procedures

1. **Service Restart**
   ```bash
   docker-compose restart
   ```

2. **Full Redeploy**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **Data Recovery**
   - Restore from database backups
   - Re-sync blockchain data
   - Recalculate profit metrics

## Support

### Documentation
- API Documentation: `http://your-domain:8000/docs`
- Dashboard Help: Built-in help sections

### Monitoring
- Real-time dashboards
- Alert notifications
- Performance metrics
- Error tracking

### Community
- GitHub Issues
- Discord Community
- Telegram Support

---

## 🚀 Deployment Checklist

- [ ] Environment variables configured
- [ ] API keys obtained and tested
- [ ] Docker images built
- [ ] Services deployed
- [ ] Health checks passing
- [ ] Dashboards accessible
- [ ] Real-time data flowing
- [ ] Alerts configured
- [ ] Backup procedures tested

**Your AINEON production system is now live on Ethereum mainnet! 🎉**