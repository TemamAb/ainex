# AINEON Flash Loan Engine - Render Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Enterprise-Grade Flash Loan Engine to Render via GitHub.

## Prerequisites
- GitHub repository: `github.com/TemamAb/myneon`
- Render account with access to create new services
- Required environment variables (see Environment Variables section)

## Deployment Architecture
- **Service Name**: flash-loan-engine
- **Runtime**: Python 3.11.10
- **Plan**: Starter (high-performance CPU/RAM)
- **Region**: Ohio
- **Web Server**: Gunicorn with UvicornWorker
- **Port**: 10000 (Render assigns dynamically)

## Files Required for Deployment

### 1. render.yaml
```yaml
services:
  - type: web
    name: flash-loan-engine
    runtime: python
    plan: starter
    region: ohio
    buildCommand: "pip install --upgrade pip && pip install -r requirements.txt"
    startCommand: "gunicorn main:app --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker"
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.12
      - key: PORT
        value: 10000
    autoDeploy: true
```

### 2. requirements.txt
Contains all Python dependencies with Python 3.10+ compatible versions:
- FastAPI for web framework
- Uvicorn for ASGI server
- Gunicorn for production WSGI server
- Web3 and blockchain libraries
- Data processing libraries (pandas, numpy)
- All dependencies are compatible with Python 3.10+

### 3. runtime.txt
```
python-3.11.10
```

### 4. main.py
FastAPI application with:
- Health check endpoint (`/health`)
- System status endpoint (`/status`)
- Engine control endpoints (`/start`, `/stop`)
- Metrics endpoint (`/metrics`)
- Configuration endpoint (`/config`)

## Environment Variables to Set in Render

### Required Secrets (Set as Environment Variables in Render Dashboard)
```
ETH_RPC_URL=your_ethereum_rpc_url
WALLET_ADDRESS=your_wallet_address
PROFIT_WALLET=your_profit_wallet_address
ALCHEMY_API_KEY=your_alchemy_api_key
INFURA_API_KEY=your_infura_api_key
```

*Note: PRIVATE_KEY is optional and only required for live trading operations*

### Optional Configuration Variables
```
ENVIRONMENT=production
LOG_LEVEL=INFO
MIN_PROFIT_THRESHOLD=0.5
MAX_GAS_PRICE=50
CONFIDENCE_THRESHOLD=0.7
MAX_POSITION_SIZE=1000
INITIAL_ETH_BALANCE=0.0
ETH_PRICE_USD=2850.0
MIN_WITHDRAWAL_ETH=0.1
MAX_WITHDRAWAL_ETH=100.0
AUTO_WITHDRAWAL_ENABLED=false
```

## Deployment Steps

### Step 1: Prepare GitHub Repository
1. Ensure all required files are in the root directory:
   - `render.yaml`
   - `requirements.txt`
   - `runtime.txt`
   - `main.py`

2. Push changes to GitHub:
```bash
git add .
git commit -m "Configure for Render deployment"
git push origin main
```

### Step 2: Deploy to Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Web Service"
3. Connect your GitHub account and select the `myneon` repository
4. Configure the service:
   - **Name**: flash-loan-engine
   - **Region**: Ohio (US Central)
   - **Branch**: main
   - **Root Directory**: (leave empty)
   - **Runtime**: Python 3
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker`

5. Click "Create Web Service"

### Step 3: Configure Environment Variables
1. In the Render service dashboard, go to "Environment" tab
2. Add all required environment variables as secrets
3. Set `PYTHON_VERSION` to `3.10.12`
4. Set `PORT` to `10000`

### Step 4: Deploy and Monitor
1. Trigger deployment by pushing to GitHub or manual deploy
2. Monitor build logs for any errors
3. Once deployed, test the endpoints:
   - `GET /` - Root endpoint
   - `GET /health` - Health check
   - `GET /status` - System status

## API Endpoints

### Core Endpoints
- `GET /` - Service information
- `GET /health` - Health check (for Render monitoring)
- `GET /status` - Comprehensive system status
- `POST /start` - Start the arbitrage engine
- `POST /stop` - Stop the arbitrage engine

### Monitoring Endpoints
- `GET /metrics` - Performance metrics
- `GET /config` - Current configuration (non-sensitive)

## Troubleshooting

### Build Issues
1. **Python Version Errors**: Ensure `runtime.txt` specifies `python-3.11.10`
2. **Dependency Conflicts**: Check that all versions in `requirements.txt` are Python 3.10+ compatible
3. **Memory Issues**: The starter plan has limited memory; consider upgrading if needed

### Runtime Issues
1. **Port Binding**: Ensure the app binds to `$PORT` environment variable
2. **Health Check**: The `/health` endpoint must return HTTP 200 for Render to consider the service healthy
3. **Logging**: Check Render logs for any runtime errors

### Performance Optimization
1. **Worker Count**: Currently set to 4 workers; adjust based on workload
2. **Memory Usage**: Monitor memory consumption and adjust plan if needed
3. **Cold Start**: Free tier instances spin down with inactivity; upgrade to avoid delays

## Security Considerations
1. **Private Keys**: Never commit private keys to repository
2. **API Keys**: Use Render's environment variable secrets
3. **CORS**: Currently allows all origins; restrict in production
4. **Rate Limiting**: Consider implementing rate limiting for API endpoints

## Next Steps
1. **Monitoring**: Set up additional monitoring and alerting
2. **Scaling**: Consider upgrading to paid plan for better performance
3. **Backup**: Implement data backup and recovery procedures
4. **Security**: Add authentication and authorization for API endpoints

## Support
For deployment issues:
1. Check Render documentation: https://render.com/docs
2. Review application logs in Render dashboard
3. Verify environment variables are correctly set
4. Test endpoints locally before deploying

## Deployment Checklist
- [ ] All required files present in repository
- [ ] render.yaml configured correctly
- [ ] requirements.txt uses Python 3.10+ compatible versions
- [ ] runtime.txt specifies Python 3.11.10
- [ ] main.py serves FastAPI application
- [ ] Environment variables set in Render
- [ ] Health check endpoint returns 200
- [ ] Service deploys successfully
- [ ] All endpoints tested and working