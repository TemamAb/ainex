# AINEON Enterprise - Render Quick Start Guide

## 1. Initial Setup (5 minutes)

### Prerequisites
- Render account (https://render.com)
- GitHub account with access to github.com/TemamAb/myneon
- Ethereum RPC URL (get free from Alchemy or Infura)

### Step 1: Log into Render Dashboard
Visit https://dashboard.render.com and sign in with your GitHub account.

### Step 2: Create New Web Service
1. Click "New +" button (top right)
2. Select "Web Service"
3. Connect GitHub repository when prompted
4. Choose "TemamAb/myneon" repository

## 2. Configure Service (5 minutes)

### Basic Settings
| Setting | Value |
|---------|-------|
| **Name** | aineon-enterprise |
| **Region** | Choose closest to your location |
| **Branch** | main |
| **Root Directory** | (leave empty) |
| **Runtime** | Docker |

### Docker Configuration
| Setting | Value |
|---------|-------|
| **Dockerfile Path** | ./Dockerfile |
| **Docker Build Context** | ./ |

## 3. Environment Variables (2 minutes)

Add these in the Render dashboard under "Environment":

### Required (minimum)
```
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
WALLET_ADDRESS=0xyourwalletaddress
PORT=8081
```

### Optional (for live trading)
```
PRIVATE_KEY=0xyourprivatekey
ETHERSCAN_API_KEY=yourapikey
PROFIT_WALLET=0xprofitaddress
```

## 4. Deploy (2 minutes)

1. Click "Create Web Service" button
2. Render automatically:
   - Clones repository
   - Builds Docker image
   - Starts container
   - Runs health checks

3. Monitor logs in dashboard (should see green checkmark when ready)

## 5. Verify Deployment (2 minutes)

Once "Running" status shows:

```bash
# Test health endpoint
curl https://your-service.onrender.com/health

# Check status
curl https://your-service.onrender.com/status

# View profit data
curl https://your-service.onrender.com/profit
```

## 6. Enable Auto-Deploy (Optional)

Render automatically redeploys when you push to `main` branch:

```bash
git push origin main  # Trigger auto-deploy
```

---

## Architecture

```
GitHub (TemamAb/myneon)
  ↓ (on push)
Render.com
  ├─ Docker Build
  ├─ Service Deployment
  ├─ Auto Health Checks
  ├─ Auto Restart on Failure
  └─ HTTPS Enabled
```

---

## Common Operations

### View Logs
```
Dashboard → Select Service → Logs tab (live streaming)
```

### Restart Service
```
Dashboard → Select Service → Restart button
```

### Update Configuration
```
Dashboard → Select Service → Environment tab → Edit variables → Save
```

### View Service Status
```
Dashboard → Select Service → Overview tab
```

---

## Estimated Costs

- **Free Tier**: ✅ Limited to 750 free instance hours/month (≈ 1 instance)
- **Pro Tier**: $12/month for continuous running

---

## Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Verify requirements.txt is valid
- Check build logs in Render dashboard

### Service Won't Start
- Check Environment variables (especially ETH_RPC_URL)
- Verify Dockerfile entry point
- Review logs for error messages

### RPC Connection Error
- Verify ETH_RPC_URL format is correct
- Check Alchemy/Infura API key is valid
- Ensure API key has not hit rate limits

### Port Issues
- Must use PORT 8081 or Render's assigned port
- Never hardcode ports in code

---

## Next Steps

1. Set up wallet with some ETH for gas fees
2. Monitor first 24 hours of operation
3. Set up alerts in Render dashboard
4. Review profit reports
5. Withdraw profits as needed

---

## Support

- Render Docs: https://render.com/docs
- AINEON Docs: See RENDER_READY_DEPLOYMENT.md
- Repository: https://github.com/TemamAb/myneon

---

**Status**: Ready for deployment  
**Last Updated**: 2025-12-16
