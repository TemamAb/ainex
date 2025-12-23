# Vercel Deployment Guide - AINEON Hybrid Dashboard

**Repository**: github.com/TemamAb/ainex  
**Platform**: Vercel (Serverless)  
**Status**: Ready for deployment

---

## What Changed for Vercel

### Files Created
1. **vercel.json** - Vercel configuration (routes, functions, headers)
2. **api/index.py** - Serverless entry point for FastAPI
3. **public/dashboard.html** - Static dashboard (served automatically)

### Files Maintained
- **main.py** - Can be removed or kept for local development
- **templates/** - Kept as fallback
- **ELITE/** - Kept as source reference

### Files Deleted
- **render.yaml** - Render-specific (not needed)

---

## Directory Structure for Vercel

```
ainex/
├── vercel.json                    ← Vercel config (NEW)
├── api/
│   └── index.py                   ← Serverless entry point (NEW)
├── public/
│   └── dashboard.html             ← Static dashboard (NEW)
├── main.py                        ← Keep for local dev (optional)
├── requirements.txt               ← Python dependencies
├── templates/                     ← Fallback (optional)
├── ELITE/                         ← Source files
└── core/                          ← Business logic
```

---

## Step 1: Set Up Vercel Account

1. Go to https://vercel.com
2. Sign up or log in
3. Click "New Project"
4. Select "Import from Git"
5. Connect GitHub account
6. Select repository: **github.com/TemamAb/ainex**

---

## Step 2: Change Git Remote to ainex Repository

### Option A: Change Existing Remote
```bash
git remote set-url origin https://github.com/TemamAb/ainex.git
git remote -v  # Verify
```

### Option B: Add New Remote
```bash
git remote add vercel https://github.com/TemamAb/ainex.git
git push vercel main
```

### Option C: Reinitialize
```bash
git remote remove origin
git remote add origin https://github.com/TemamAb/ainex.git
git push -u origin main
```

---

## Step 3: Create/Push to ainex Repository

### Create Repository on GitHub
1. Go to https://github.com/new
2. Repository name: **ainex**
3. Make it public
4. Don't initialize (we'll push existing)
5. Click "Create repository"

### Push Code to ainex
```bash
cd c:\Users\op\Desktop\aineon-enterprise

# Remove old remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/TemamAb/ainex.git

# Push to new repository
git push -u origin main
```

---

## Step 4: Configure Environment Variables in Vercel

In Vercel Dashboard:

1. Go to Project Settings
2. Click "Environment Variables"
3. Add these variables:

```
ALCHEMY_API_KEY = <your-key>
INFURA_API_KEY = <your-key>
PRIVATE_KEY = <your-key>
WITHDRAWAL_ADDRESS = <your-address>
AUTO_WITHDRAWAL_ENABLED = false
MIN_PROFIT_THRESHOLD = 0.5
ETH_PRICE_USD = 2850.0
ENVIRONMENT = production
LOG_LEVEL = INFO
```

**Important**: Set these for all environments (Production, Preview, Development)

---

## Step 5: Deploy to Vercel

### Automatic Deployment
Once GitHub is connected, every push to `main` branch triggers automatic deployment.

### Manual Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy (use existing project)
vercel --prod

# Or login first
vercel login
vercel --prod
```

### View Deployment
- Project URL: https://ainex.vercel.app
- Dashboard: https://ainex.vercel.app/dashboard
- Check status: https://vercel.com/dashboard

---

## Step 6: Test the Deployment

### Check Dashboard Loads
```
https://ainex.vercel.app/dashboard
```

### Test API Endpoints
```bash
# Health check
curl https://ainex.vercel.app/health

# Profit metrics
curl https://ainex.vercel.app/api/profit

# Status
curl https://ainex.vercel.app/status

# Metrics
curl https://ainex.vercel.app/metrics
```

### Expected Responses
All endpoints should return JSON with timestamp and data.

---

## Local Development with Vercel

### Install Vercel CLI
```bash
npm i -g vercel
# or
npm install --global vercel
```

### Clone and Setup
```bash
git clone https://github.com/TemamAb/ainex.git
cd ainex

# Install Python dependencies
pip install -r requirements.txt
```

### Test Locally
```bash
# Use Vercel CLI to test locally
vercel dev

# Access at: http://localhost:3000
# Dashboard: http://localhost:3000/dashboard
```

### Test with Python Only
```bash
python main.py
# Access at: http://localhost:10000
```

---

## Differences from Render Deployment

| Feature | Render | Vercel |
|---------|--------|--------|
| **Deployment Time** | 2-5 min | 30-60 sec |
| **Cold Start** | None | 1-2 sec |
| **WebSocket** | ✅ Native | ❌ Not supported |
| **Real-time Updates** | WebSocket | Polling (1-5 sec) |
| **File System** | ✅ Persistent | ❌ Read-only |
| **Static Assets** | In container | `/public/` directory |
| **Cost** | $7/month min | Free + pay-per-use |
| **Scaling** | Manual | Automatic |

---

## Troubleshooting

### Dashboard Not Loading
```
Problem: 404 on /dashboard
Solution: 
  1. Check public/dashboard.html exists
  2. Check vercel.json has /dashboard route
  3. Check function is deployed: vercel deployments
```

### API Returning 500
```
Problem: Internal server error on /api/profit
Solution:
  1. Check logs: vercel logs ainex
  2. Check requirements.txt is installed
  3. Check Python version (3.9+)
  4. Check environment variables set
```

### Environment Variables Not Working
```
Problem: API returns None for API keys
Solution:
  1. Verify vars in Vercel Dashboard
  2. Redeploy after setting vars: git push
  3. Clear cache: vercel cache rm
  4. Check in logs: vercel logs --follow
```

### Cold Start Too Slow
```
Problem: First request takes 2-3 seconds
Solution:
  1. Expected behavior for serverless
  2. Can't be prevented with Vercel Free
  3. Upgrade to Pro for faster response
  4. Keep function warm with cron
```

### Function Timeout
```
Problem: Timeout after 60 seconds
Solution:
  1. Split long operations into multiple requests
  2. Use Vercel Cron for scheduled tasks
  3. Move profit tracking to separate service
  4. Implement request queuing
```

---

## Performance Optimization

### For Vercel
1. **Keep functions small** - Faster startup
2. **Use polling** - No persistent connections
3. **Cache responses** - Reduce API calls
4. **Minify assets** - Smaller downloads
5. **Use CDN** - Auto-enabled by Vercel

### Polling Interval Recommendations
```javascript
// Fast updates (more API calls)
const POLL_INTERVAL = 1000;  // 1 second

// Balanced (recommended)
const POLL_INTERVAL = 3000;  // 3 seconds

// Slow updates (fewer calls)
const POLL_INTERVAL = 5000;  // 5 seconds
```

---

## Monitoring & Logs

### View Logs
```bash
# Real-time logs
vercel logs <project> --follow

# Last 100 lines
vercel logs <project>

# For specific function
vercel logs ainex api/index.py
```

### Monitor Performance
- Dashboard: https://vercel.com/dashboard
- Analytics: Project Settings → Analytics
- Monitoring: Project Settings → Monitoring

### Check Deployment Status
```bash
vercel status
vercel deployments list
vercel deployments inspect <deployment-id>
```

---

## Scaling & Limits

### Vercel Free Tier
- **Serverless Functions**: 1,000,000 invocations/month
- **Bandwidth**: 100 GB/month
- **Build time**: 6,000 build minutes/month
- **Deployments**: Unlimited
- **Concurrency**: Limited

### Recommended for AINEON
Free tier is sufficient for:
- Testing and development
- Low-traffic dashboards
- < 100k API calls/month
- Single serverless function

### Upgrade to Pro for
- Higher concurrency
- Faster cold starts
- Priority support
- Custom domains

---

## Continuous Integration

### Automatic on Push
1. Push to `main` branch
2. Vercel automatically builds
3. Runs tests (if configured)
4. Deploys to production
5. Updates dashboard URL

### Preview Deployments
- Pull requests get automatic preview URLs
- Test before merging to main
- Automatic cleanup after merge

### Rollback
```bash
# List deployments
vercel deployments

# Promote old deployment
vercel promote <deployment-id>
```

---

## Custom Domain

### Connect Domain
1. Go to Vercel Dashboard
2. Project Settings → Domains
3. Add your domain
4. Update DNS records
5. Verify connection

### Example
- Vercel: https://ainex.vercel.app
- Custom: https://dashboard.aineon.io

---

## Next Steps

### Immediate
1. ✅ Create ainex repository on GitHub
2. ✅ Change git remote to ainex
3. ✅ Commit and push to ainex
4. ✅ Connect to Vercel
5. ✅ Set environment variables
6. ✅ Deploy to Vercel

### After Deployment
1. Test dashboard loads
2. Test API endpoints
3. Monitor logs for errors
4. Verify environment variables work
5. Test on mobile device

### For Backend Integration
1. Connect profit_tracker to /api/profit
2. Implement polling in frontend
3. Add OpenAI/Gemini integration
4. Test production flow
5. Monitor costs

---

## Comparison: Which Platform?

### Use Render If
- Need persistent WebSocket
- Run long-running tasks
- Need file system
- Want simplicity

### Use Vercel If
- Want fast deployments
- API-first architecture
- Serverless preferred
- Cost-sensitive
- Prefer edge functions

### For AINEON
**Recommendation**: Vercel + Render (hybrid)
- **Vercel**: Dashboard frontend (fast, serverless)
- **Render**: Backend services (profit tracking, WebSocket)

---

## Files Checklist

- [x] vercel.json - Configuration
- [x] api/index.py - Serverless entry point
- [x] public/dashboard.html - Static dashboard
- [x] requirements.txt - Dependencies
- [x] main.py - Local development
- [x] VERCEL_DEPLOYMENT_GUIDE.md - This guide
- [x] VERCEL_DEPLOYMENT_ANALYSIS.md - Analysis
- [ ] ainex repository created
- [ ] Git remote changed
- [ ] Code pushed to ainex
- [ ] Vercel project created
- [ ] Environment variables set
- [ ] Deployment successful

---

## Support

**Vercel Documentation**: https://vercel.com/docs  
**Python Runtime**: https://vercel.com/docs/concepts/functions/serverless-functions/python  
**Environment Variables**: https://vercel.com/docs/concepts/projects/environment-variables  

---

**Status**: READY FOR VERCEL DEPLOYMENT  
**Platform**: Vercel (github.com/TemamAb/ainex)  
**Next Action**: Create ainex repo and push code
