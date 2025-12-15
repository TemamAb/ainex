# AINEON Dashboard User Guide

## Overview

The AINEON Enterprise Engine provides two powerful dashboard interfaces for monitoring and controlling your arbitrage operations:

1. **Terminal Dashboard** - Real-time command-line monitoring
2. **Web Dashboard** - Interactive Streamlit-based monitoring interface

---

## 🔥 Terminal Dashboard (Real-Time)

### Launching the Terminal Dashboard

```bash
# Basic usage
python dashboard/terminal_dashboard.py

# Custom API endpoint and refresh rate
python dashboard/terminal_dashboard.py --api-url http://localhost:8081 --refresh 3
```

### Key Features

#### **System Health Monitoring**
- **RPC Connection Status**: Real-time Ethereum network connectivity
- **System Uptime**: Engine running time
- **Error Tracking**: API connection error counter

#### **Performance Metrics**
- **Tier 1 Scans**: Market scanning operations
- **Tier 2 Signals**: AI-generated arbitrage signals  
- **Tier 3 Executions**: Successful trade executions
- **AI Optimizations**: Model retraining cycles

#### **💰 PROFIT VERIFICATION (KEY METRIC)**
The terminal dashboard emphasizes **ETHERSCAN-VERIFIED PROFITS ONLY**:

- **Accumulated ETH**: Total verified profits in ETH
- **Accumulated USD**: Total verified profits in USD
- **Profit Change**: Real-time profit delta tracking
- **ETH Price**: Current market price
- **Auto-Transfer Status**: Whether automated profit sweeping is active
- **Etherscan Validation**: Verification system status

**Profit Status Indicators:**
- `GENERATING PROFIT`: > 0.1 ETH accumulated
- `ACCUMULATING`: < 0.1 ETH accumulated  
- `AWAITING OPPORTUNITIES`: No profits yet

#### **Risk Management**
- **Active Positions**: Currently open arbitrage positions
- **Daily P&L**: Real-time profit/loss tracking
- **Daily Loss Capacity**: Remaining risk budget
- **Risk Status**: Overall risk assessment
- **Circuit Breaker**: Safety system status

#### **Performance Indicators**
- **API Errors**: Connection reliability tracking
- **Dashboard Uptime**: Monitoring system runtime
- **Refresh Interval**: Update frequency

---

## 🌐 Web Dashboard (Interactive)

### Launching the Web Dashboard

```bash
# Install dependencies
pip install streamlit plotly pandas

# Launch dashboard
streamlit run dashboard/monitoring_dashboard.py
```

Access at: `http://localhost:8501`

### Dashboard Sections

#### **📊 Performance Tab**

**Key Metrics Cards:**
- **Total P&L**: Overall profit/loss with percentage change
- **Win Rate**: Percentage of successful trades
- **Average Trade Size**: Mean transaction value
- **Sharpe Ratio**: Risk-adjusted return metric

**Interactive Charts:**
- **P&L Over Time**: Cumulative profit tracking
- **Trade Size Distribution**: Histogram of trade amounts
- **Profit/Loss Distribution**: Performance breakdown

#### **🎯 Opportunities Tab**

**Live Data Tables:**
- **Current Arbitrage Opportunities**: Real-time DEX price spreads
- **AI Opportunity Predictions**: Machine learning forecasts

**Visual Analytics:**
- **DEX Price Heatmap**: Profitability by exchange/token pair
- **Opportunity Ranking**: Confidence-sorted opportunities

#### **⚠️ Risk Tab**

**Risk Metrics:**
- **VaR (95%)**: Value at Risk calculation
- **Max Drawdown**: Largest loss from peak
- **Liquidity Risk**: Market depth assessment
- **Slippage Risk**: Price impact estimation

**Risk Controls:**
- **Active Risk Alerts**: Real-time warning system
- **Risk Exposure Chart**: Historical risk tracking

#### **🔧 Settings Tab**

**Risk Parameters:**
- **Max Slippage**: Acceptable price impact (0.1-5.0%)
- **Max Position Size**: Trade size limits ($10K-$10M)
- **AI Confidence Threshold**: Signal quality filter (50-95%)
- **Scan Interval**: Market scanning frequency (50-1000ms)

**DEX Configuration:**
- **Enabled Exchanges**: Uniswap V3, SushiSwap, PancakeSwap, 1inch, CowSwap
- **Custom Settings**: Per-DEX configuration

---

## 🎛️ Sidebar Controls (Web Dashboard)

### System Status
- **Engine Status**: Real-time connection indicator (🟢/🔴)
- **Etherscan Verification**: Compliance status with color coding

### 💰 Profit Manager
**Verified Profit Display:**
- Large ETH accumulation counter (green, glowing)
- "ETHERSCAN VERIFIED" badge
- Pending verification counter (if applicable)

**Transfer Control:**
- **Manual Mode**: Human-triggered withdrawals
- **Auto Mode**: Automated profit sweeping above threshold
- **WITHDRAW NOW Button**: Immediate fund transfer
- **Threshold Setting**: Customizable auto-transfer level

### Quick Stats
- **24h Profit**: Verified profit in last 24 hours
- **Active Trades**: Currently executing positions

### Risk Alerts
- **Visual Alerts**: Color-coded warning system
- **Critical Issues**: Etherscan validation problems
- **Threshold Alerts**: Profit accumulation notifications

---

## 🔌 API Endpoints

The dashboards connect to these REST API endpoints:

### Core Endpoints
- `GET /health` - System health check
- `GET /status` - Complete system status
- `GET /profit` - Etherscan-verified profit metrics
- `GET /opportunities` - Current arbitrage opportunities
- `GET /audit` - Detailed audit status
- `GET /audit/report` - Compliance report

### Control Endpoints
- `POST /settings/profit-config` - Update profit settings
- `POST /withdraw` - Execute manual withdrawal

### Data Structure
```json
{
  "status": "ONLINE",
  "mode": "EXECUTION_MODE",
  "accumulated_eth_verified": 0.123456,
  "accumulated_usd_verified": 250.50,
  "auto_transfer_enabled": true,
  "etherscan_enabled": true,
  "verification_status": "ACTIVE"
}
```

---

## 🚀 Quick Start Guide

### 1. Start the Engine
```bash
# Ensure PRIVATE_KEY is set for live trading
export PRIVATE_KEY="your_private_key_here"
python core/main.py
```

### 2. Launch Terminal Dashboard
```bash
# In new terminal
python dashboard/terminal_dashboard.py
```

### 3. Launch Web Dashboard
```bash
# In another terminal  
streamlit run dashboard/monitoring_dashboard.py
```

### 4. Monitor Key Metrics
- **Verify Etherscan Status**: Should show "ACTIVE" (green)
- **Check Profit Display**: Only shows verified profits
- **Monitor Risk Alerts**: Address any warnings
- **Configure Auto-Transfer**: Set appropriate thresholds

---

## 📈 Understanding the Data

### Profit Verification
- **VERIFIED (Green)**: Etherscan-confirmed profits count toward metrics
- **PENDING (Yellow)**: Profits awaiting blockchain confirmation
- **UNVERIFIED (Red)**: Profits not validated (not displayed)

### Risk Indicators
- **Green**: Safe operating conditions
- **Yellow**: Moderate risk, monitor closely  
- **Red**: High risk, immediate attention required

### Mode Indicators
- **MONITORING MODE**: Market scanning only, no trading
- **EXECUTION MODE**: Full arbitrage trading active

---

## ⚡ Pro Tips

### Terminal Dashboard
- Use `Ctrl+C` to stop gracefully
- Higher refresh rates (1-3s) for active trading
- Lower refresh rates (10-30s) for monitoring

### Web Dashboard  
- Enable auto-refresh for real-time updates
- Use full-screen mode for better visibility
- Monitor risk alerts proactively
- Set appropriate confidence thresholds

### Performance Optimization
- **Execution Mode**: Higher confidence thresholds (80-95%)
- **Monitoring Mode**: Lower thresholds (60-80%) for signal discovery
- **Scan Frequency**: Balance between opportunity detection and API limits

---

## 🔒 Security Features

### Profit Validation
- **Etherscan Integration**: All profits must be blockchain-verified
- **Audit Trail**: Complete transaction history
- **Compliance Reporting**: Regulatory-ready reports

### Risk Controls
- **Circuit Breakers**: Automatic trading halts on losses
- **Position Limits**: Configurable trade size restrictions
- **Slippage Protection**: Maximum acceptable price impact

### Monitoring
- **Real-time Alerts**: Immediate notification of issues
- **Error Tracking**: Connection and execution failure logging
- **Performance Monitoring**: System health and efficiency metrics

---

## 📞 Support

### Common Issues
1. **"Profit data unavailable"**: Check API connection
2. **"Etherscan validation disabled"**: Set ETHERSCAN_API_KEY
3. **"Risk alert active"**: Review profit thresholds and auto-transfer settings
4. **High API errors**: Check network connectivity and RPC endpoint

### Best Practices
- Always verify Etherscan status before making decisions
- Use appropriate risk settings for your capital level
- Monitor dashboard alerts proactively
- Regular withdrawal of accumulated profits

The AINEON dashboard provides institutional-grade monitoring for professional arbitrage operations, ensuring transparency, compliance, and risk management.