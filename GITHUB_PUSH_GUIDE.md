# GitHub Push & Render Deployment Guide

## Step 1: Verify Git Status
```bash
cd c:\Users\op\Desktop\ainex
git status
```

Expected output should show modified/untracked files:
- `app/types.ts` (NEW)
- `app/page.tsx` (MODIFIED)
- `app/engine/EngineContext.tsx` (MODIFIED)
- `.env.local` (NEW)
- `render-build.sh` (NEW)
- `DEPLOYMENT_CHECKLIST.md` (NEW)
- `GITHUB_PUSH_GUIDE.md` (NEW)

---

## Step 2: Stage All Changes
```bash
git add -A
```

---

## Step 3: Commit Changes
```bash
git commit -m "fix: resolve type definitions and hook violations for Render deployment

- Create app/types.ts with WalletState, UserProfile, FileNode interfaces
- Fix hook violation in page.tsx (startSimulation call outside of component)
- Update EngineContext to properly export startSimulation as Promise
- Add deployment checklist and build scripts
- Create .env.local template for development

This resolves all critical issues blocking deployment to Render."
```

---

## Step 4: Push to GitHub
```bash
git push origin main
```

**Or if main doesn't exist:**
```bash
git push -u origin main
```

---

## Step 5: Verify on GitHub
1. Go to: https://github.com/TemamAb/ainex
2. Confirm all files appear in main branch
3. Check commit message and files changed

---

## Step 6: Connect to Render

### Option A: Using Render Dashboard (Recommended)
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Select `TemamAb/ainex`
5. Configure:
   - **Name:** `quantumnex-dashboard`
   - **Environment:** Node
   - **Build Command:** `npm run build`
   - **Start Command:** `npm start`
   - **Auto-deploy:** Enable

### Option B: Using Infrastructure as Code
Create `render-deploy.json`:
```json
{
  "services": [
    {
      "type": "web",
      "name": "quantumnex-dashboard",
      "env": "node",
      "buildCommand": "npm run build",
      "startCommand": "npm start",
      "envVars": [
        {
          "key": "NODE_ENV",
          "value": "production"
        }
      ]
    }
  ]
}
```

---

## Step 7: Set Environment Variables on Render

In Render Dashboard → Your Service → Settings → Environment:

```
NODE_ENV=production
VITE_WALLET_ADDRESS=
VITE_GEMINI_API_KEY=your-key-here
VITE_LICENSE_KEY=production-license-key
VITE_ENABLE_LIVE_MODE=false
```

---

## Step 8: Monitor Deployment

1. Go to Render Dashboard
2. Click on `quantumnex-dashboard` service
3. Watch "Build" tab for compilation
4. Check "Logs" for runtime errors
5. Once "Build Succeeded", service URL is live

Expected URL: `https://quantumnex-dashboard.onrender.com`

---

## Troubleshooting

### Build Fails: "npm: not found"
**Solution:** Render environment is missing Node.js
- Go to Service → Settings → Environment
- Ensure `Environment` is set to `Node`
- Trigger rebuild

### Build Fails: "vite: command not found"
**Solution:** Dependencies not installed
- Check `npm install` runs in build command
- Verify `package.json` exists in root
- Try: `npm install --legacy-peer-deps && npm run build`

### App Starts but Shows 404
**Solution:** SPA router not configured
- Ensure `vite.config.ts` has preview server config
- Add fallback route in Vite or Render
- Check `public/` directory if using index.html

### Environment Variables Not Loading
**Solution:** VITE_* prefix required
- Only variables prefixed `VITE_` are exposed to frontend
- Render Dashboard must have exact keys
- Redeploy after adding env vars

### Service Keeps Restarting
**Solution:** Out of memory or crash loop
- Check logs for JavaScript errors
- Reduce initial memory load
- Verify `npm start` command in package.json

---

## Post-Deployment Checks

```bash
# 1. Test the deployed app
curl -I https://quantumnex-dashboard.onrender.com

# Expected: HTTP 200 OK

# 2. Check for build artifacts
# Should see index.html, assets/, etc. in Render logs

# 3. Verify in browser
# - Open DevTools (F12)
# - Check Console tab for errors
# - Test all interactive elements
```

---

## Rollback Procedure

If deployment is broken:

```bash
# Revert to previous commit
git revert HEAD --no-edit
git push origin main

# Render will auto-redeploy
# Check dashboard for new build status
```

---

## Continuous Deployment

Once connected, Render will:
- Auto-deploy on every push to `main`
- Skip builds if only README changed (optional)
- Run health check at `/` endpoint
- Restart service if health check fails

To disable auto-deploy temporarily:
1. Service → Settings
2. Toggle "Auto-Deploy" to OFF

---

## Next Steps

1. [ ] Run `git push origin main`
2. [ ] Verify GitHub shows latest commits
3. [ ] Connect to Render (if not already)
4. [ ] Set environment variables
5. [ ] Monitor build logs
6. [ ] Test deployed URL
7. [ ] Set up custom domain (optional)

---

**Questions?** Check Render docs: https://render.com/docs/deploy-vite
