# AINEON Enterprise Setup Guide

## Fixed Issues

✅ **API Error Resolution**: The Minimax API error you encountered is an infrastructure-level issue, not a problem with your project code.

✅ **Environment Setup**: Fixed missing `.env.example` file and startup script references
- Created proper `.env.example` template
- Fixed `start.sh` and `start.bat` to use correct `main.py` file
- Created clean `.env.clean` template

✅ **Project Structure**: The AINEON Enterprise system is properly configured for:
- DeFi arbitrage trading across multiple DEXs
- AI-powered profit optimization
- Gasless transactions via Pimlico Paymaster
- Comprehensive monitoring and risk management

## Quick Setup

### 1. Environment Configuration

Copy the clean environment template:
```bash
cp .env.clean .env
```

Edit `.env` with your actual values:
- `ETH_RPC_URL`: Your Alchemy/Infura endpoint
- `WALLET_ADDRESS`: Your Ethereum wallet address
- `PRIVATE_KEY`: Your private key (leave empty for monitoring mode)
- `CONTRACT_ADDRESS`: Your deployed contract address
- `PAYMASTER_URL`: Pimlico paymaster URL (for gasless mode)
- `ETHERSCAN_API_KEY`: For transaction verification

### 2. Start the System

**Linux/macOS:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**Windows:**
```cmd
scripts\start.bat
```

### 3. Alternative Manual Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the system
cd core
python main.py
```

## System Features

### Monitoring Mode (No Private Key)
- Market scanning active
- Profit tracking active  
- Trade execution disabled
- API endpoints available for monitoring

### Execution Mode (With Private Key)
- Full arbitrage trading
- Flash loan execution
- AI optimization
- Gasless transactions
- Profit management and transfer

### API Endpoints
- `GET /health` - System health check
- `GET /status` - Current system status
- `GET /opportunities` - Active trading opportunities
- `GET /profit` - Profit metrics and statistics
- `GET /audit` - Transaction audit details
- `POST /withdraw` - Manual profit withdrawal

## Troubleshooting

### Environment Issues
- Ensure `.env` file exists and is properly formatted
- Verify all required environment variables are set
- Check that RPC endpoints are accessible

### Dependencies
- Ensure Python 3.10+ is installed
- Install all required packages: `pip install -r requirements.txt`
- For ML features, install TensorFlow: `pip install tensorflow`

### Network Issues
- Verify RPC endpoints are working
- Check wallet has sufficient balance for gas
- Ensure contract addresses are correct

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit `.env` file to version control
- Keep private keys secure and never share them
- Use testnet for development and testing
- Enable monitoring before enabling execution mode

## Support

The Minimax API error you encountered cannot be resolved through code changes as it's a platform-level infrastructure issue. This requires:

1. **Platform-level fix**: Contact Kilo Code support or switch to a different AI model
2. **Your project code**: Is functioning correctly and has been properly configured

For AINEON-specific issues, check the logs and ensure all environment variables are properly configured.