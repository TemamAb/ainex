# AINEON Enterprise Engine - Render Deployment Guide

## Overview
This guide will help you deploy the AINEON Enterprise Engine to Render using Docker containerization.

## Prerequisites
1. A Render account (sign up at https://render.com)
2. Ethereum wallet with some ETH for gas fees
3. RPC endpoint (Alchemy, Infura, or similar)
4. Smart contract deployed (for flash loan functionality)

## Quick Deploy to Render

### Step 1: Fork/Clone the Repository
1. Fork this repository to your GitHub account
2. Or clone and push to your own repository

### Step 2: Connect to Render
1. Log into your Render dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the repository containing this code

### Step 3: Configure Web Service
1. **Name**: `aineon-enterprise-engine` (or your preferred name)
2. **Region**: Choose closest to your target users
3. **Branch**: `main`
4. **Root Directory**: Leave empty (root level)
5. **Runtime**: `Docker`
6. **Dockerfile Path**: `./infrastructure/docker/Dockerfile`
7. **Docker Build Context**: `./`

### Step 4: Set Environment Variables
In the Render dashboard, go to Environment tab and add:

#### Required Variables:
- `ETH_RPC_URL`: Your Ethereum RPC endpoint
- `WALLET_ADDRESS`: Your Ethereum wallet address

#### Optional Variables (for live trading):
- `PRIVATE_KEY`: Your wallet private key (⚠️ **WARNING**: Keep this secret!)
- `CONTRACT_ADDRESS`: Your deployed smart contract address
- `PAYMASTER_URL`: Pimlico paymaster URL for gasless transactions
- `BUNDLER_URL`: Bundler URL for transaction bundling
- `PROFIT_WALLET`: Address to receive profits
- `ETHERSCAN_API_KEY`: For transaction verification

#### Server Configuration:
- `PORT`: `8081` (default)

### Step 5: Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy using Docker
3. Monitor the logs for deployment status

## Architecture

### Container Structure
- **Base Image**: `python:3.11-slim`
- **Application Port**: `8081`
- **Health Check**: `/health` endpoint
- **Entry Point**: `core/main.py`

### API Endpoints
- `GET /health` - Health check
- `GET /status` - System status
- `GET /opportunities` - Current arbitrage opportunities
- `GET /profit` - Profit statistics
- `GET /audit` - Audit information
- `POST /withdraw` - Manual profit withdrawal

## Environment Modes

### Monitoring Mode
When `PRIVATE_KEY` is not set, the system runs in monitoring mode:
- ✅ Market scanning active
- ✅ Profit tracking active
- ✅ API endpoints functional
- ❌ Trade execution disabled

### Execution Mode
When `PRIVATE_KEY` and `CONTRACT_ADDRESS` are set:
- ✅ Full system active
- ✅ Trade execution enabled
- ✅ Flash loan arbitrage
- ✅ Profit generation

## Local Development

### Using Docker
```bash
# Build the Docker image
docker build -f infrastructure/docker/Dockerfile -t aineon-engine .

# Run the container
docker run -p 8081:8081 \
  -e ETH_RPC_URL=your_rpc_url \
  -e WALLET_ADDRESS=your_wallet \
  -e PRIVATE_KEY=your_key \
  aineon-engine
```

### Using Python Directly
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ETH_RPC_URL=your_rpc_url
export WALLET_ADDRESS=your_wallet
export PRIVATE_KEY=your_key

# Run the engine
python core/main.py
```

## Security Best Practices

1. **Never commit private keys** to version control
2. **Use environment variables** for all sensitive data
3. **Enable Render's private environment variables**
4. **Monitor your wallet** for unauthorized transactions
5. **Use testnet first** before mainnet deployment
6. **Set up alerts** for unusual activity

## Troubleshooting

### Common Issues

1. **Port not accessible**
   - Ensure `PORT=8081` is set in environment variables
   - Check Render service logs

2. **RPC connection failed**
   - Verify your `ETH_RPC_URL` is correct and accessible
   - Check your API key limits

3. **Private key errors**
   - Ensure private key format is correct (with or without 0x prefix)
   - Verify wallet has sufficient ETH for gas fees

4. **Contract interaction fails**
   - Confirm `CONTRACT_ADDRESS` is correct
   - Verify contract is deployed on the same network as your RPC

### Logs
Monitor Render service logs for:
- Startup messages
- RPC connection status
- API endpoint responses
- Any error messages

## Scaling

### Horizontal Scaling
- Render supports auto-scaling (configure in dashboard)
- Each instance runs independently
- Consider database for shared state if needed

### Resource Optimization
- Monitor memory usage in Render dashboard
- Adjust instance type based on load
- Consider using Render's persistent disks for data

## Support

For issues and questions:
1. Check the logs first
2. Review environment variables
3. Test locally with Docker
4. Create an issue in the repository

## License

This project is proprietary software. All rights reserved.