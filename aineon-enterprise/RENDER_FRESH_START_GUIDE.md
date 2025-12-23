# AINEON Render Deployment - Fresh Start Guide
## Step-by-Step from GitHub to Live

---

## PHASE 1: GitHub Repository Check

### Step 1.1: Verify Latest Commit
Run this locally:
```bash
git log --oneline -1
```
Should show: `341b0dbc Set manual withdrawal as default`

### Step 1.2: Verify Files in Repository Root
These 3 files MUST exist in root directory:
- `main.py` ✓ (FastAPI app)
- `requirements.txt` ✓ (dependencies)
- `render.yaml` ✓ (deployment config)

If yes, proceed. If no, STOP and fix first.

---

## PHASE 2: Create Render Account & Login

1. Go to https://render.com
2. Sign up or login
3. Go to Dashboard: https://dashboard.render.com
4. Click profile → GitHub → Authorize Render to access GitHub

---

## PHASE 3: Create NEW Web Service (Fresh Start)

### Step 3.1: Delete Any Existing Service (if any)
If you have a previous AINEON service on Render:
1. Dashboard → Find service
2. Settings → Delete Service
3. Confirm deletion

### Step 3.2: Click "New +"
1. Dashboard → Click **"New +"** (top-left button)
2. Select **"Web Service"**

### Step 3.3: Connect GitHub Repository
1. **GitHub Account**: (Should be pre-connected)
2. **Select Repository**: `TemamAb/myneon`
3. If not listed, click "Configure Account" → authorize Render

### Step 3.4: Configure Service Settings

Fill in these fields:

| Field | Value | Notes |
|-------|-------|-------|
| **Name** | `aineon-profit-engine` | Service identifier |
| **Runtime** | `Python 3` | Select from dropdown |
| **Region** | `Ohio` | Or your region |
| **Branch** | `main` | Default branch |
| **Root Directory** | (leave empty) | App is in root |

Click **"Advanced"** (if available)

### Step 3.5: Build Settings

**Build Command:**
```
pip install --upgrade pip && pip install -r requirements.txt
```

Copy exactly as shown.

### Step 3.6: Start Command

**Start Command:**
```
gunicorn main:app --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

Copy exactly.

### Step 3.7: Environment Variables

**Option A - Set Now (Basic):**

Click "Add Environment Variable" and add ONLY:
```
ENVIRONMENT = production
LOG_LEVEL = INFO
AUTO_WITHDRAWAL_ENABLED = false
```

**Option B - Add Later (After Deploy)**

You'll add blockchain/wallet keys after service is running (more secure).

### Step 3.8: Auto-Deploy

Check: **"Auto-deploy new commits"** = ON (checked)

### Step 3.9: Create Service

Click **"Create Web Service"**

Render will:
1. Connect to GitHub
2. Clone repository
3. Build dependencies (watch logs)
4. Start service

---

## PHASE 4: Monitor Build Process

### Step 4.1: Watch Build Logs
1. Service page opens automatically
2. Click **"Logs"** tab (top)
3. Watch for messages:
   - `Building...` → Building dependencies
   - `Deployed` → Success
   - `Failed` → Error (read logs)

### Step 4.2: Build Should Take 2-3 Minutes

Expected log sequence:
```
Building...
Installing dependencies from requirements.txt...
Installing web3==6.11.2...
Installing fastapi==0.104.1...
...
Successfully installed all packages
Starting gunicorn...
Application started on port 10000
```

### Step 4.3: If Build Fails

Common errors:
- **"pandas error"** → Already fixed (pandas 2.0.3)
- **"Port already in use"** → Render assigns port, click redeploy
- **"ImportError"** → Missing dependency in requirements.txt

If fails, STOP and share error message.

---

## PHASE 5: Add Environment Variables (Secrets)

Once service is "Live":

### Step 5.1: Go to Environment Tab

Service page → **"Environment"** tab

### Step 5.2: Add Required Variables

Click **"Add Environment Variable"** for each:

**Blockchain:**
```
ETH_RPC_URL = https://mainnet.infura.io/v3/YOUR_INFURA_KEY
ALCHEMY_API_KEY = your_alchemy_key
INFURA_API_KEY = your_infura_key
```

**Wallet (CRITICAL):**
```
WALLET_ADDRESS = 0x... (your main wallet)
WITHDRAWAL_ADDRESS = 0x... (where profits go)
PRIVATE_KEY = your_private_key (HANDLE WITH CARE)
```

**Profit Tracking:**
```
MIN_PROFIT_THRESHOLD = 0.5
AUTO_WITHDRAWAL_ENABLED = false
AUTO_WITHDRAWAL_THRESHOLD = 5.0
TRACKING_INTERVAL = 60
```

### Step 5.3: Save & Deploy

After adding each variable:
- Click "Save Changes"
- Render auto-redeploys with new variables

---

## PHASE 6: Verify Deployment

### Step 6.1: Check Service Status

Dashboard → Your service:
- Status should show **"Live"** (green)
- If "Building" → Wait for completion
- If "Failed" → Check logs

### Step 6.2: Get Service URL

Service page shows URL at top:
```
https://aineon-profit-engine.onrender.com
```

Copy this URL.

### Step 6.3: Test Health Endpoint

Open browser and go to:
```
https://aineon-profit-engine.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-23T...",
  "engine_running": false,
  "uptime_seconds": 0
}
```

If error → Check service logs

### Step 6.4: Test Root Endpoint

Go to:
```
https://aineon-profit-engine.onrender.com/
```

Expected response:
```json
{
  "message": "AINEON Flash Loan Engine - Enterprise Blockchain Arbitrage",
  "version": "1.0.0",
  "status": "stopped",
  "start_time": null,
  "environment": "production"
}
```

---

## PHASE 7: Start Engine

### Step 7.1: Trigger Engine Start

In terminal or Postman, run:
```bash
curl -X POST https://aineon-profit-engine.onrender.com/start
```

Or in browser go to:
```
https://aineon-profit-engine.onrender.com/start
```
(Changes GET to POST in advanced tools)

### Step 7.2: Check Status

```bash
curl https://aineon-profit-engine.onrender.com/status
```

Should show `"engine_running": true`

### Step 7.3: Monitor Logs

Service → **"Logs"** tab

Watch for:
- Engine initialization
- Blockchain connection
- Profit tracking starting
- Any errors

---

## PHASE 8: Monitor Real-Time Profits

### Step 8.1: Check Metrics

Every 60 seconds, profits are tracked:
```bash
curl https://aineon-profit-engine.onrender.com/metrics
```

Response should show:
```json
{
  "status": "demo_mode",
  "metrics": {
    "total_profit_eth": 0.0,
    "successful_trades": 0,
    "failed_trades": 0
  }
}
```

### Step 8.2: Manual Withdrawal (When Ready)

Once profit threshold reached (5 ETH default):

```bash
curl -X POST https://aineon-profit-engine.onrender.com/withdrawal/manual \
  -H "Content-Type: application/json" \
  -d '{
    "amount_eth": 2.5,
    "destination_address": "YOUR_WITHDRAWAL_ADDRESS",
    "confirm": true
  }'
```

### Step 8.3: Verify on Etherscan

Check your withdrawal address:
```
https://etherscan.io/address/YOUR_WITHDRAWAL_ADDRESS
```

Look for incoming ETH transactions.

---

## PHASE 9: Monitor & Maintain

### Step 9.1: Service Logs (Daily Check)

Dashboard → Service → **"Logs"** tab

Check for:
- Errors
- Connection issues
- Profit accumulation
- Transaction confirmations

### Step 9.2: Metrics Monitoring

Every hour check:
```bash
curl https://aineon-profit-engine.onrender.com/metrics
```

Track total_profit_eth growth.

### Step 9.3: Service Health

Dashboard shows:
- **Status**: Should be "Live"
- **CPU/Memory**: Monitor usage
- **Uptime**: Should be continuous

---

## TROUBLESHOOTING

### Build Fails
**Problem**: "Failed to build"
**Solution**: 
1. Check logs for specific error
2. If pandas error → Already fixed
3. Click "Manual Deploy" to retry

### Service Won't Start
**Problem**: Status stays "Building"
**Solution**:
1. Wait 5 minutes
2. If still building → Click "Cancel Deploy"
3. Click "Manual Deploy" again

### /health Returns Error
**Problem**: `{"error": "Connection refused"}`
**Solution**:
1. Service still starting → Wait 2 minutes
2. Check environment variables set correctly
3. Check logs for startup errors

### No Profit Data
**Problem**: `/metrics` returns 0 profit
**Solution**:
1. Confirm blockchain APIs working (ETH_RPC_URL valid)
2. Check WALLET_ADDRESS format (start with 0x)
3. Engine may be in demo mode waiting for live data

### Withdrawal Fails
**Problem**: Withdrawal API returns error
**Solution**:
1. Confirm WITHDRAWAL_ADDRESS is valid (0x...)
2. Confirm PRIVATE_KEY is correct
3. Check wallet has ETH for gas fees (0.01 ETH minimum)

---

## SUCCESS CRITERIA

✓ **Mission Complete When:**
1. Service shows "Live" on Render
2. `/health` returns HTTP 200
3. `/metrics` shows profit data
4. Etherscan shows ETH received at WITHDRAWAL_ADDRESS
5. Logs show no critical errors

**BOOM BONUS:** Screenshot of Etherscan with your profit transfer!

---

## Quick Reference URLs

| Endpoint | Purpose |
|----------|---------|
| `https://aineon-profit-engine.onrender.com/` | Root status |
| `https://aineon-profit-engine.onrender.com/health` | Health check |
| `https://aineon-profit-engine.onrender.com/status` | Full system status |
| `https://aineon-profit-engine.onrender.com/metrics` | Profit metrics |
| `https://dashboard.render.com/` | Render dashboard |
| `https://etherscan.io/address/YOUR_ADDR` | Verify profits |

---

## Ready? Start from Phase 1 Step 3.1

Delete old service (if any) and create fresh one!
