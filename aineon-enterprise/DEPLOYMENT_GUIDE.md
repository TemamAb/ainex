# AINEON Flash Loan Engine - Production Deployment Guide

## 🚀 Quick Deploy to Render & GitHub

### Prerequisites
- GitHub account
- Render.com account (free tier available)
- Ethereum wallet with funds (for mainnet deployment)

## Step 1: GitHub Setup

### Create GitHub Repository
1. Go to [github.com](https://github.com) and create a new repository
2. Name it `myneon` (as requested)
3. Make it public or private as preferred

### Prepare Local Repository
```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Create .gitignore if needed
echo "*.pyc
__pycache__/
.env
logs/
data/
models/
*.log" > .gitignore

# Commit files
git commit -m "Initial commit: AINEON Flash Loan Engine"

# Add GitHub remote (replace with your username)
git remote add origin https://github.com/TemamAb/myneon.git

# Push to GitHub
git push -u origin main
```

## Step 2: Render Deployment

### Connect GitHub to Render
1. Go to [render.com](https://render.com)
2. Sign up/login with your GitHub account
3. Click "New +" → "Web Service"
4. Connect your `myneon` repository

### Deploy Engine API Service
1. **Service Name**: `aineon-engine-api`
2. **Environment**: Python 3
3. **Build Command**: 
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   pip install -r core/requirements.txt
   pip install fastapi uvicorn[standard] requests
   ```
4. **Start Command**:
   ```bash
   cd backend && python production_api.py
   ```
5. **Environment Variables** (add these in Render dashboard):
   ```bash
   ENVIRONMENT=production
   ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
   WALLET_ADDRESS=0xYourWalletAddress
   PRIVATE_KEY=your_private_key
   ETHERSCAN_API_KEY=your_etherscan_api_key
   DEBUG=false
   PROFIT_MODE=ENTERPRISE_TIER
   ```

### Deploy Dashboard Service
1. **Service Name**: `aineon-dashboard`
2. **Environment**: Python 3
3. **Build Command**: 
   ```bash
   pip install --upgrade pip
   pip install streamlit plotly pandas numpy requests
   ```
4. **Start Command**:
   ```bash
   streamlit run production_dashboard.py --server.port=$PORT --server.address=0.0.0.0
   ```
5. **Environment Variables**:
   ```bash
   API_BASE_URL=https://aineon-engine-api.onrender.com
   ENVIRONMENT=production
   ```

## Step 3: Configuration

### Environment Variables Setup
In Render dashboard, set these environment variables:

**For Engine API:**
- `ETH_RPC_URL`: Your Ethereum RPC endpoint
- `WALLET_ADDRESS`: Your wallet address
- `PRIVATE_KEY`: Your private key (keep secure!)
- `ETHERSCAN_API_KEY`: Your Etherscan API key
- `PROFIT_THRESHOLD_ETH`: `1.0`
- `MIN_PROFIT_PER_TRADE`: `0.1`
- `MAX_POSITION_SIZE`: `1000.0`

**For Dashboard:**
- `API_BASE_URL`: Auto-populated by Render (leave empty)
- `ENVIRONMENT`: `production`

## Step 4: Monitoring & Access

### Service URLs
After deployment, Render will provide URLs:
- **Engine API**: `https://aineon-engine-api.onrender.com`
- **Dashboard**: `https://aineon-dashboard.onrender.com`

### Health Checks
- API Health: `https://aineon-engine-api.onrender.com/api/health`
- Engine Status: `https://aineon-engine-api.onrender.com/api/status`
- Dashboard: `https://aineon-dashboard.onrender.com`

## Step 5: Production Considerations

### Security
- **NEVER** commit private keys to GitHub
- Use Render's environment variables for sensitive data
- Consider using Render's encrypted environment variables
- Set up proper CORS policies for production

### Performance
- Upgrade to Render's paid tier for better performance
- Configure auto-scaling if needed
- Monitor resource usage in Render dashboard

### Cost Management
- **Free Tier Limitations**: 
  - Services spin down after 15 minutes of inactivity
  - Limited CPU/memory
  - No persistent connections
- **Starter Plan** ($7/month): 
  - Always-on instances
  - Better performance
  - Custom domains

## Local Development (Preserve Current State)

To run locally without affecting your current engine:

```bash
# Run API locally (different port)
cd backend
python production_api.py  # Uses port 8000

# Run dashboard locally
streamlit run production_dashboard.py  # Uses port 8501

# Your original engine continues running on current ports
```

## Troubleshooting

### Common Issues
1. **Service won't start**: Check build logs in Render dashboard
2. **API not responding**: Verify environment variables
3. **Dashboard can't connect**: Check API_BASE_URL setting
4. **Private key issues**: Ensure it's properly formatted (0x...)

### Logs
- View logs in Render dashboard for each service
- Check both build logs and runtime logs
- Monitor for any error messages

## Next Steps

1. **Test the deployment** with small amounts first
2. **Monitor performance** and adjust as needed
3. **Scale up** when ready for production volumes
4. **Set up monitoring** and alerting
5. **Configure backup** strategies

## Support

- Render Documentation: https://render.com/docs
- GitHub Actions: Can be set up for CI/CD
- Streamlit Documentation: https://docs.streamlit.io

---

**⚡ Your AINEON Flash Loan Engine is now ready for cloud deployment! ⚡**