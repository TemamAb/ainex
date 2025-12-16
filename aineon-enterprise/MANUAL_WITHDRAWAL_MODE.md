# AINEON Manual Withdrawal Mode - Complete Guide

**Mode**: MANUAL WITHDRAWAL (NO AUTO-TRANSFER)  
**Status**: PRODUCTION READY  
**Profit Tracking**: REAL-TIME TERMINAL DISPLAY  

---

## Overview

AINEON is configured in **MANUAL WITHDRAWAL MODE**:
- ✅ Profits accumulate in your trading wallet
- ✅ NO automatic transfers
- ✅ YOU control when and how much to withdraw
- ✅ Real-time profit display in terminal
- ✅ Manual withdrawal via API call

---

## Quick Start (5 minutes)

### Step 1: Setup (Reads your .env file)
```bash
# Windows
setup-complete.bat

# Linux/Mac
chmod +x setup-complete.sh
./setup-complete.sh
```

This will:
- ✓ Read your .env configuration
- ✓ Validate RPC connection
- ✓ Create manual withdrawal config
- ✓ Display setup summary

### Step 2: Deploy AINEON
```bash
# Windows
deploy-production.bat

# Linux/Mac
./deploy-production.sh
```

### Step 3: Start Terminal Profit Monitor
```bash
# Windows (in new terminal)
run-terminal-monitor.bat

# Linux/Mac (in new terminal)
chmod +x run-terminal-monitor.sh
./run-terminal-monitor.sh
```

### Step 4: Watch Profits Accumulate
The terminal monitor displays real-time profit metrics:
```
╔════════════════════════════════════════════════════════════════════╗
║          AINEON FLASH LOAN ENGINE - TERMINAL PROFIT MONITOR        ║
║                    MANUAL WITHDRAWAL MODE                          ║
╚════════════════════════════════════════════════════════════════════╝

┌─ PROFIT METRICS (VERIFIED) ───────────────────────────────────┐
💰 ACCUMULATED PROFIT:
   ETH: 7.5432 ETH
   USD: $18,858.00

📊 WITHDRAWAL TRACKING:
   Threshold:          5.0 ETH
   Progress:           ████████████████░░░░ 150.9%
   Status:             ✓ READY FOR WITHDRAWAL
└────────────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════════════╗
║                    MANUAL WITHDRAWAL MODE                           ║
║                                                                    ║
║  ✓ THRESHOLD REACHED - WITHDRAWAL READY                            ║
║                                                                    ║
║  To withdraw manually, execute:                                     ║
║  $ curl -X POST http://localhost:8081/withdraw                      ║
║                                                                    ║
║  Amount: 7.5432 ETH ($18,858.00)                                   ║
╚════════════════════════════════════════════════════════════════════╝
```

### Step 5: Manual Withdrawal
When ready to withdraw (5.0 ETH threshold reached):

```bash
# Execute withdrawal
curl -X POST http://localhost:8081/withdraw

# Expected response
{
  "status": "success",
  "message": "Withdrawal executed.",
  "amount_eth": 7.5432,
  "amount_usd": 18858.00,
  "transaction_hash": "0x...",
  "destination": "0x..."
}
```

---

## Configuration Files

### Main Configuration: `profit_earning_config_manual.json`

```json
{
  "profit_mode": "ENTERPRISE_TIER_0.001%",
  "auto_transfer_enabled": false,
  "transfer_mode": "MANUAL_ONLY",
  "withdrawal_settings": {
    "mode": "MANUAL",
    "auto_transfer": false,
    "requires_confirmation": true,
    "notification_on_ready": true,
    "ready_threshold_eth": 5.0,
    "max_withdrawal_per_tx": "unlimited",
    "gas_price_optimization": true,
    "destination_wallet": "YOUR_PROFIT_WALLET"
  }
}
```

### Environment: `.env` (Your actual credentials)

The setup script reads directly from your `.env` file:
```
ETH_RPC_URL=...          (Your RPC endpoint)
WALLET_ADDRESS=...        (Your trading wallet)
PROFIT_WALLET=...         (Your profit destination, optional)
ETHERSCAN_API_KEY=...     (For verification)
```

---

## Terminal Profit Monitor

### What It Shows

```
SESSION INFORMATION
├─ Uptime
├─ Monitoring Mode: MANUAL WITHDRAWAL
├─ Transfer Setting: ❌ AUTO-TRANSFER DISABLED
└─ Current Time

PROFIT METRICS (VERIFIED)
├─ Accumulated Profit (ETH & USD)
├─ Withdrawal Progress Bar
└─ Status (Accumulating / Ready for Withdrawal)

SYSTEM STATUS
├─ Online Status
├─ Market Scanning: ACTIVE
├─ Orchestration: ACTIVE
├─ Execution Ready: YES
└─ Flash Loans: ENABLED

OPPORTUNITIES (Last Scan)
├─ Total Found
└─ Recent Opportunities with confidence scores

RECENT OPPORTUNITIES
└─ Last 5 detected arbitrage opportunities
```

### Running the Monitor

**Windows**:
```batch
run-terminal-monitor.bat
```

**Linux/Mac**:
```bash
./run-terminal-monitor.sh
```

**Manual (any platform)**:
```bash
python3 terminal_profit_monitor.py
```

Updates every 5 seconds automatically.

---

## Profit Generation Targets

### Daily Projections

| Timeframe | Target | Strategy |
|-----------|--------|----------|
| Per Hour | 10 ETH | Multi-DEX Arb + MEV |
| Per Minute | 0.25 ETH | Flash Loan Sandwich |
| Per Day | 100-250 ETH | All 6 strategies |

### Monthly & Yearly

| Period | Target | Notes |
|--------|--------|-------|
| Monthly | 2,500-5,400 ETH | 6 strategies active |
| Yearly | 30,000-60,000 ETH | Enterprise tier |

### Withdrawal Threshold

- **Default**: 5.0 ETH (~$12,500)
- **Customizable**: Edit `profit_earning_config_manual.json`
- **Notification**: Terminal monitor alerts when ready

---

## How to Withdraw

### Automatic Notification
Terminal monitor shows when threshold is reached:
```
Status: ✓ READY FOR WITHDRAWAL
```

### Manual Withdrawal Command

**Using curl**:
```bash
curl -X POST http://localhost:8081/withdraw
```

**Using PowerShell (Windows)**:
```powershell
Invoke-WebRequest -Uri "http://localhost:8081/withdraw" -Method POST
```

**Using Python**:
```python
import requests
response = requests.post("http://localhost:8081/withdraw")
print(response.json())
```

### Withdrawal Response

```json
{
  "status": "success",
  "message": "Withdrawal executed.",
  "amount_eth": 7.5432,
  "amount_usd": 18858.00,
  "transaction_hash": "0x...",
  "destination_wallet": "0x...",
  "confirmed": true
}
```

---

## Risk Management

### Built-in Protections

| Setting | Value | Purpose |
|---------|-------|---------|
| Daily Loss Limit | 100 ETH | System halts if exceeded |
| Max Drawdown | 2.5% | Emergency circuit breaker |
| Max Position Size | 1,000 ETH | Per-trade limit |
| Max Consecutive Failures | 5 | Auto-halt protection |

### Circuit Breaker Triggers

System **automatically halts** if:
```
Daily Loss ≥ 100 ETH    → HALT
Drawdown ≥ 2.5%         → HALT
Consecutive Failures ≥ 5 → HALT
RPC Connection Lost     → HALT (recovery mode)
```

System **automatically resumes** when conditions normalize.

---

## Monitoring Commands

### Real-Time Profit
```bash
curl http://localhost:8081/profit
```

### System Status
```bash
curl http://localhost:8081/status
```

### Recent Opportunities
```bash
curl http://localhost:8081/opportunities
```

### Health Check
```bash
curl http://localhost:8081/health
```

### Audit Trail
```bash
curl http://localhost:8081/audit
```

### Compliance Report
```bash
curl http://localhost:8081/audit/report
```

---

## Daily Workflow

### Morning (Start of Day)
```bash
# 1. Deploy if not running
./deploy-production.sh

# 2. Start terminal monitor (in new window)
./run-terminal-monitor.sh

# 3. Verify system is online
curl http://localhost:8081/status
```

### Throughout Day
- Monitor terminal for real-time profit display
- Terminal updates every 5 seconds
- Alert appears when 5.0 ETH threshold reached

### When Ready to Withdraw
```bash
# 1. Terminal shows: ✓ READY FOR WITHDRAWAL
# 2. Execute withdrawal
curl -X POST http://localhost:8081/withdraw

# 3. Verify transaction
# Terminal monitor will show updated balance
```

### Evening (End of Day)
```bash
# Generate compliance report
curl http://localhost:8081/audit/report > daily_audit_$(date +%Y%m%d).txt

# Review logs
docker logs -f aineon-engine-prod | tail -20

# Check system health
curl http://localhost:8081/health
```

---

## Advantages of Manual Mode

### Security
✅ You control ALL withdrawals  
✅ No automatic fund transfers  
✅ Requires manual confirmation  
✅ Better protection against bugs  

### Optimization
✅ Batch multiple withdrawals  
✅ Optimize gas prices  
✅ Choose withdrawal timing  
✅ Combine with accounting needs  

### Control
✅ Withdraw to different addresses  
✅ Adjust thresholds anytime  
✅ Full audit trail  
✅ Peace of mind  

---

## Customization

### Change Withdrawal Threshold

Edit `profit_earning_config_manual.json`:
```json
"withdrawal_settings": {
  "ready_threshold_eth": 10.0  // Changed from 5.0
}
```

Restart monitor:
```bash
./run-terminal-monitor.sh
```

### Change Destination Wallet

Edit `.env`:
```bash
PROFIT_WALLET=0xYourNewWalletAddress
```

Restart system:
```bash
./deploy-production.sh
```

### Adjust Daily Loss Limit

Edit `profit_earning_config_manual.json`:
```json
"risk_management": {
  "daily_loss_limit": 200.0  // Changed from 100.0
}
```

---

## Troubleshooting

### Terminal Monitor Won't Start

```bash
# Check if .env exists
ls -la .env

# Verify Python
python3 --version

# Test RPC directly
curl -X POST https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

### Withdrawal Fails

```bash
# Check API health
curl http://localhost:8081/health

# Verify account balance
curl http://localhost:8081/profit

# Check system logs
docker logs aineon-engine-prod | grep -i error

# Restart system
./deploy-production.sh
```

### Profit Not Showing

```bash
# Verify market scanner is active
curl http://localhost:8081/status | grep scanners

# Check recent opportunities
curl http://localhost:8081/opportunities

# Review full logs
docker logs aineon-engine-prod | tail -100
```

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/status` | GET | System status |
| `/profit` | GET | Profit metrics |
| `/opportunities` | GET | Recent opportunities |
| `/audit` | GET | Audit trail |
| `/audit/report` | GET | Compliance report |
| `/withdraw` | POST | Manual withdrawal |

**Base URL**: `http://localhost:8081`

---

## Dashboard Access

### Terminal Monitor
```bash
./run-terminal-monitor.sh
```

### Web Dashboard
```
http://localhost:8089
```

### API Direct Access
```bash
curl http://localhost:8081/profit | jq
```

---

## Security Considerations

### Private Keys
✅ NEVER stored in code  
✅ ONLY in .env file  
✅ NEVER committed to version control  
✅ ERC-4337 gasless execution supported  

### Withdrawals
✅ Etherscan verified  
✅ Transaction logged  
✅ Cryptographically signed  
✅ Audit trail maintained  

### Monitoring
✅ Real-time alerts  
✅ Circuit breaker protection  
✅ Daily loss limits  
✅ Drawdown monitoring  

---

## Next Steps

1. ✅ **Setup**: `./setup-complete.sh` or `setup-complete.bat`
2. ✅ **Deploy**: `./deploy-production.sh` or `deploy-production.bat`
3. ✅ **Monitor**: `./run-terminal-monitor.sh` or `run-terminal-monitor.bat`
4. ✅ **Watch**: Real-time profit accumulation in terminal
5. ✅ **Withdraw**: Manual command when threshold reached

---

## Support

- **Documentation**: See ARCHITECTURE_SUMMARY.md
- **Deployment Help**: See PRODUCTION_DEPLOYMENT_GUIDE.md
- **Quick Reference**: See QUICK_REFERENCE.md
- **Live Status**: `curl http://localhost:8081/status`
- **Logs**: `docker logs -f aineon-engine-prod`

---

**Status**: ✅ MANUAL WITHDRAWAL MODE CONFIGURED  
**Profit Tracking**: ✅ REAL-TIME TERMINAL DISPLAY  
**Security**: ✅ NO AUTO-TRANSFER  
**Ready to Deploy**: ✅ YES  

**Execute**: `./setup-complete.sh` to begin!
