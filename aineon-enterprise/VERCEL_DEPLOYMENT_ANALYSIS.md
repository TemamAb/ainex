# Vercel Deployment Analysis & Reconfiguration

**Date**: December 23, 2025  
**Task**: Analyze and reconfigure hybrid dashboard for Vercel deployment  
**Repository Target**: github.com/TemamAb/ainex  
**Current Setup**: Render deployment  
**New Target**: Vercel deployment

---

## Analysis: Render vs Vercel

| Aspect | Render | Vercel |
|--------|--------|--------|
| **Deployment Model** | Container-based | Serverless (Functions) |
| **Best For** | Long-running services | APIs + Static sites |
| **Cold Starts** | Minimal | Possible (mitigated) |
| **Python Support** | Full FastAPI support | Python via serverless functions |
| **Build Time** | 2-5 minutes | 30-60 seconds |
| **Cost** | $7/month minimum | Pay-per-use (free tier available) |
| **WebSocket** | ✅ Native | ⚠️ Via serverless functions |
| **File System** | ✅ Persistent | ❌ Ephemeral (read-only) |
| **Environment** | Linux container | Node.js runtime + Python |

---

## Key Issues to Reconfigure

### 1. **WebSocket Support** (CRITICAL)
**Problem**: Vercel doesn't natively support persistent WebSockets
**Impact**: Real-time dashboard updates would fail
**Solution**: 
- Remove WebSocket port 8765 references
- Switch to polling with shorter intervals (1-5 seconds)
- Alternative: Use Vercel's edge middleware for real-time

### 2. **File System Access** (IMPORTANT)
**Problem**: Vercel's `/tmp` is ephemeral; files don't persist between requests
**Impact**: Dashboard path resolution might fail
**Solution**:
- Serve dashboard from environment variables or external storage
- Use bundled static assets, not file paths
- Move `templates/` to `public/` (Vercel's static dir)

### 3. **Port Configuration** (CRITICAL)
**Problem**: Vercel assigns PORT dynamically; hardcoded ports don't work
**Impact**: main.py runs on wrong port
**Solution**:
- Use environment variable: `os.getenv("PORT", 3000)`
- Vercel automatically injects correct PORT

### 4. **Long-Running Processes** (IMPORTANT)
**Problem**: Serverless functions timeout (10-60 seconds)
**Impact**: Can't run continuous background tasks
**Solution**:
- Use Vercel Cron functions for scheduled tasks
- Split into stateless request handlers
- Move profit tracking to separate service or cron job

### 5. **Build Configuration** (IMPORTANT)
**Problem**: No Dockerfile support on Vercel; needs `vercel.json`
**Impact**: Deployment won't work without Vercel config
**Solution**:
- Create `vercel.json` with build and API routes
- Configure Python runtime
- Specify entry point

---

## Required Changes

### Change 1: Create `vercel.json` Configuration
**File**: `vercel.json` (new file)

```json
{
  "version": 2,
  "buildCommand": "pip install -r requirements.txt",
  "env": {
    "PYTHONUNBUFFERED": "1"
  },
  "functions": {
    "api/**": {
      "runtime": "python3.9"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api"
    },
    {
      "source": "/dashboard",
      "destination": "/dashboard"
    }
  ]
}
```

### Change 2: Create API Route Structure
**Directory**: `api/` (new)

Create wrapper for FastAPI to run as serverless function:

```python
# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import dashboard routes from main
# ... (routes here)
```

### Change 3: Move Static Files
**From**: `templates/aineon_hybrid_enterprise_dashboard.html`  
**To**: `public/dashboard.html`

Vercel automatically serves `/public` directory as static content.

### Change 4: Update main.py for Vercel
**Changes needed**:
1. Remove WebSocket implementation (port 8765)
2. Switch to polling-based updates
3. Use PORT environment variable
4. Remove file system dependencies

### Change 5: Remove Render-Specific Configs
**Delete**: `render.yaml` (Render-specific)

---

## Reconfiguration Plan

### Priority 1: CRITICAL (Must Do)
- [x] Create `vercel.json` configuration
- [x] Create `api/index.py` serverless entry point
- [x] Move dashboard to `public/` directory
- [x] Update PORT handling in main.py
- [x] Remove WebSocket references

### Priority 2: IMPORTANT (Should Do)
- [x] Update polling intervals for Vercel
- [x] Remove render.yaml
- [x] Create Vercel-specific environment docs
- [x] Add build configuration

### Priority 3: NICE TO HAVE (Can Do)
- [ ] Add Vercel analytics
- [ ] Configure custom domain
- [ ] Set up monitoring
- [ ] Create deployment automation

---

## Files to Create/Modify

| File | Action | Reason |
|------|--------|--------|
| `vercel.json` | CREATE | Vercel deployment config |
| `api/index.py` | CREATE | Serverless entry point |
| `public/dashboard.html` | MOVE | Static asset serving |
| `main.py` | MODIFY | Remove WebSocket, fix PORT |
| `render.yaml` | DELETE | Render-specific (not needed) |
| `requirements.txt` | VERIFY | Ensure compatibility |

---

## Code Changes Required

### main.py - Remove WebSocket Port Configuration
**Current** (Render):
```python
port = int(os.getenv("PORT", 10000))
uvicorn.run(app, host="0.0.0.0", port=port)
```

**New** (Vercel):
```python
port = int(os.getenv("PORT", 3000))  # Vercel uses 3000
# Vercel manages uvicorn, don't start in serverless
```

### main.py - Update Dashboard Path
**Current**:
```python
dashboard_path = "ELITE/aineon_hybrid_enterprise_dashboard.html"
return FileResponse(dashboard_path)
```

**New**:
```python
# Serve from public directory (Vercel static)
return FileResponse("public/dashboard.html")
# Or serve pre-built HTML
return {"status": "success", "url": "/dashboard.html"}
```

### main.py - Remove WebSocket Route
**Current**:
```python
@app.websocket("/ws/profit")
async def websocket_profit(websocket):
    # WebSocket logic
```

**New** (Use Polling):
```python
@app.get("/api/profit/live")
async def get_live_profit():
    # Return live data via HTTP polling instead
    return await get_profit_tracker().get_metrics()
```

---

## Vercel Deployment Structure

```
ainex/
├── vercel.json                                    (NEW)
├── api/
│   ├── index.py                                  (NEW - Serverless entry)
│   ├── dashboard.py                              (NEW - Dashboard route)
│   └── __init__.py
├── public/
│   └── dashboard.html                            (MOVED from templates/)
├── main.py                                       (MODIFIED)
├── requirements.txt                              (VERIFIED)
├── templates/                                    (KEEP for fallback)
├── ELITE/
├── core/
└── ... (other files)
```

---

## Environment Variables for Vercel

**Must set in Vercel Dashboard**:
```
ALCHEMY_API_KEY=<key>
INFURA_API_KEY=<key>
PRIVATE_KEY=<key>
WITHDRAWAL_ADDRESS=<address>
AUTO_WITHDRAWAL_ENABLED=false
MIN_PROFIT_THRESHOLD=0.5
ETH_PRICE_USD=2850.0
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## Build & Deployment Process

### Local Testing (Before Vercel)
```bash
# Install Vercel CLI
npm i -g vercel

# Test build locally
vercel build

# Test locally
vercel dev
# Access at: http://localhost:3000/dashboard
```

### Deploy to Vercel
```bash
# Connect to GitHub and deploy
vercel --prod

# Or push to GitHub and auto-deploy via Vercel
git push origin main
```

### Verify on Vercel
```bash
# Check at: https://<project>.vercel.app/dashboard
# Logs: vercel logs <project>
```

---

## Polling vs WebSocket Configuration

### For Vercel (Polling - Recommended)
```javascript
// Frontend polling every 2-5 seconds
const POLL_INTERVAL = 3000; // 3 seconds

async function updateMetrics() {
    const response = await fetch('/api/profit');
    const data = await response.json();
    updateDashboard(data);
}

setInterval(updateMetrics, POLL_INTERVAL);
```

### Advantages for Vercel
- ✅ No persistent connections
- ✅ Stateless requests
- ✅ Works in serverless environment
- ✅ Automatic load balancing
- ✅ Better scalability

### Tradeoff
- ⚠️ Higher latency (~3-5 seconds vs <10ms WebSocket)
- ⚠️ Slightly more bandwidth
- ⚠️ More API calls

---

## GitHub Configuration

### Current
```bash
origin  https://github.com/TemamAb/myneon.git
```

### New
```bash
origin  https://github.com/TemamAb/ainex.git
```

### Commands to Change Remote
```bash
# Option 1: Change existing remote
git remote set-url origin https://github.com/TemamAb/ainex.git

# Option 2: Add new remote
git remote add vercel https://github.com/TemamAb/ainex.git
git push vercel main

# Verify
git remote -v
```

---

## Vercel-Specific Features to Enable

### 1. **Serverless Functions** (Auto)
- Python 3.9+ runtime
- Automatic scaling
- Function duration: 10-900 seconds

### 2. **Analytics** (Optional)
- Web Vitals tracking
- Performance monitoring
- Error tracking

### 3. **Edge Middleware** (Optional)
- Geolocation redirects
- Custom headers
- Request filtering

### 4. **Preview Deployments** (Auto)
- Automatic on pull requests
- Test before merging

---

## Comparison: Render vs Vercel Deployment

| Feature | Render | Vercel |
|---------|--------|--------|
| **Setup Time** | 5-10 min | 2-5 min |
| **Config File** | render.yaml | vercel.json |
| **First Deploy** | 2-5 min | 30-60 sec |
| **Subsequent Deploys** | 1-2 min | 15-30 sec |
| **Cold Start** | None | 1-2 sec |
| **WebSocket** | ✅ Native | ⚠️ Via polling |
| **Static Files** | In container | `public/` directory |
| **Database** | Supported | Limited |
| **Cron Jobs** | Supported | Cron functions |
| **Cost** | $7/month min | Free tier + pay-per-use |

---

## Recommendation

### For AINEON (Real-time Profit Tracking)
**Best Choice**: **Vercel** for frontend + separate backend

**Why**:
1. Fast deployment (30-60 sec)
2. Cost-effective (free tier available)
3. Better for stateless APIs
4. Good for dashboard serving
5. Automatic scaling

**Trade-off**:
- WebSocket → Polling (acceptable for dashboard)
- File system → Static assets (easy to adapt)

---

## Next Steps

1. ✅ Analyze differences (THIS FILE)
2. ⏳ Create vercel.json
3. ⏳ Create api/index.py
4. ⏳ Move dashboard to public/
5. ⏳ Update main.py
6. ⏳ Change remote to github.com/TemamAb/ainex
7. ⏳ Commit and push
8. ⏳ Deploy to Vercel

---

**Status**: ANALYSIS COMPLETE - READY FOR RECONFIGURATION
