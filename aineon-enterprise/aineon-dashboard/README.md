# AINEON Executive Dashboard

## 🚀 Enterprise-Grade Profit Monitoring Dashboard

AINEON Executive Dashboard is a **user-friendly, non-technical interface** designed for business executives to monitor real-time profit generation from elite arbitrage trading operations.

### 🎯 Key Features

#### **Executive Summary**
- **Real-time profit display** with verified blockchain data
- **One-click profit withdrawal** functionality
- **System status monitoring** with health indicators
- **Key performance metrics** in easy-to-understand format

#### **User-Friendly Interface**
- **No technical jargon** - business language only
- **Color-coded status indicators** (🟢 Healthy, 🟡 Warning, 🔴 Critical)
- **Simple action buttons** for common tasks
- **Auto-refreshing data** every 5 seconds

#### **Profit Management**
- **Manual & Automatic withdrawal modes**
- **Withdrawal threshold configuration**
- **Transaction history with verification status**
- **Gas optimization settings**

#### **Performance Analytics**
- **Daily, weekly, monthly profit trends**
- **Success rate and win/loss ratios**
- **Risk-adjusted returns (Sharpe ratio)**
- **Comparative performance metrics**

#### **Risk Management**
- **Real-time risk scoring**
- **Position limit monitoring**
- **Daily loss limit tracking**
- **Liquidity risk assessment**

#### **System Monitoring**
- **Engine status (Online/Offline)**
- **API connectivity monitoring**
- **Etherscan verification status**
- **System resource usage**

---

## 📊 Dashboard Sections

### 1. **Executive Summary** (Main Page)
- **Total Verified Profit** (ETH + USD)
- **Today's Profit**
- **Success Rate**
- **Engine Status**
- **Quick Action Buttons**

### 2. **Withdrawals**
- Quick withdrawal form
- Withdrawal history
- Automatic withdrawal settings
- Multi-address configuration

### 3. **Performance**
- Profit trends and charts
- Trading statistics
- Comparative analytics
- Return metrics

### 4. **Risk Management**
- Risk score overview
- Active risk alerts
- Position limits
- Safety controls

### 5. **Settings**
- System status
- API configuration
- Engine controls
- Configuration backup

---

## 🛠️ Technical Architecture

### **Frontend**
- **Streamlit** - Python web framework
- **Plotly** - Interactive charts and visualizations
- **Pandas** - Data manipulation and analysis

### **Backend Integration**
- **RESTful API** connection to AINEON engine
- **Real-time WebSocket** updates
- **Blockchain verification** via Etherscan API
- **Error monitoring** and logging

### **Deployment**
- **Render.com** auto-deployment
- **GitHub Actions** CI/CD pipeline
- **Docker containerization**
- **Environment variable configuration**

---

## 🚀 Quick Start

### **Local Development**

1. **Clone the repository**
```bash
git clone https://github.com/TemamAb/myneon.git
cd myneon/aineon-dashboard
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set environment variables**
```bash
export API_BASE_URL="http://localhost:8081"
export ETHERSCAN_API_KEY="your_etherscan_key"
```

4. **Run the dashboard**
```bash
streamlit run user_friendly_dashboard.py
```

5. **Access dashboard**
Open browser to: `http://localhost:8501`

### **Production Deployment**

#### **Option 1: Render.com (Recommended)**

1. **Connect GitHub repository**
   - Go to [Render.com](https://render.com)
   - Connect your GitHub account
   - Import repository: `TemamAb/myneon`

2. **Configure environment variables**
   ```
   API_BASE_URL=https://your-engine.onrender.com
   ETHERSCAN_API_KEY=your_etherscan_key
   WALLET_ADDRESS=your_wallet_address
   ```

3. **Deploy**
   - Render will automatically detect `render.yaml`
   - Deploys both dashboard and engine
   - Provides live URLs

#### **Option 2: Manual Deployment**

1. **Build and push Docker image**
```bash
docker build -t aineon-dashboard .
docker push your-registry/aineon-dashboard
```

2. **Deploy to your platform**
```bash
docker run -p 8501:8501 \
  -e API_BASE_URL="your_api_url" \
  -e ETHERSCAN_API_KEY="your_key" \
  aineon-dashboard
```

---

## 🔧 Configuration

### **Environment Variables**

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `API_BASE_URL` | Backend API URL | Yes | `http://localhost:8081` |
| `ETHERSCAN_API_KEY` | Etherscan API key | Yes | - |
| `WALLET_ADDRESS` | Ethereum wallet address | Yes | - |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `REFRESH_INTERVAL` | Auto-refresh interval (seconds) | No | `5` |
| `ALERT_EMAIL` | Email for alerts | No | - |

### **Dashboard Settings**

#### **Withdrawal Configuration**
- **Manual Mode**: User controls all withdrawals
- **Auto Mode**: Automatic withdrawals above threshold
- **Threshold**: Minimum amount for auto-withdrawal (default: 0.1 ETH)
- **Gas Strategy**: Standard, Fast, Slow, or Optimized

#### **Risk Parameters**
- **Maximum Position Size**: Default $1,000,000
- **Daily Loss Limit**: Default $10,000
- **Stop-Loss**: Enable/disable automatic stop-loss
- **Maximum Slippage**: Default 1.0%

---

## 📈 Monitoring & Alerts

### **System Status Indicators**

- 🟢 **HEALTHY**: All systems operational
- 🟡 **WARNING**: Minor issues detected
- 🔴 **CRITICAL**: Major issues requiring attention

### **Error Handling**

- **Automatic error recovery** for transient issues
- **Comprehensive logging** for debugging
- **Email alerts** for critical errors
- **Performance monitoring** and threshold alerts

### **Health Checks**

- **API connectivity** verification
- **Etherscan integration** status
- **System resource** monitoring
- **Response time** tracking

---

## 🔒 Security Features

### **Data Protection**
- **Environment variable** security
- **No sensitive data** in logs
- **HTTPS-only** communications
- **API key encryption**

### **Access Control**
- **Read-only dashboard** by default
- **Manual withdrawal** requirement
- **Multi-factor** authentication ready
- **Audit trail** for all actions

---

## 🧪 Testing

### **Run Tests**
```bash
# Unit tests
pytest tests/ -v

# Integration tests
pytest tests/integration/ -v

# Dashboard tests
streamlit run user_friendly_dashboard.py --server.headless true
```

### **Test Coverage**
```bash
pytest --cov=. --cov-report=html
```

---

## 📊 Performance

### **Metrics**
- **Page load time**: <2 seconds
- **Data refresh**: 5-second intervals
- **API response time**: <500ms target
- **Uptime**: 99.9% SLA

### **Optimization**
- **Efficient caching** of API responses
- **Minimal data transfer** via compression
- **Lazy loading** of heavy components
- **Background processing** for non-critical tasks

---

## 🐛 Troubleshooting

### **Common Issues**

#### **Dashboard Won't Start**
```bash
# Check dependencies
pip install -r requirements.txt

# Verify Python version
python --version  # Should be 3.9+

# Check port availability
lsof -i :8501
```

#### **API Connection Failed**
- Verify `API_BASE_URL` is correct
- Check backend service is running
- Confirm firewall settings
- Validate API endpoints

#### **No Profit Data Displayed**
- Check `ETHERSCAN_API_KEY` is configured
- Verify wallet address is set
- Confirm blockchain connection
- Check Etherscan rate limits

#### **Withdrawal Failed**
- Verify sufficient ETH balance
- Check gas settings
- Confirm wallet connectivity
- Review transaction history

### **Debug Mode**
```bash
export LOG_LEVEL=DEBUG
streamlit run user_friendly_dashboard.py
```

### **Log Files**
- **Dashboard logs**: `logs/aineon_dashboard.log`
- **Error logs**: `logs/error_handler.log`
- **Access logs**: Available in Render dashboard

---

## 📞 Support

### **Getting Help**

1. **Check the logs** for error messages
2. **Review troubleshooting** section above
3. **Open GitHub issue** for bugs
4. **Contact support** for urgent issues

### **Contact Information**

- **GitHub Repository**: https://github.com/TemamAb/myneon
- **Issues**: https://github.com/TemamAb/myneon/issues
- **Documentation**: See `docs/` folder

---

## 📄 License

**MIT License** - See LICENSE file for details

---

## 🤝 Contributing

### **Development Workflow**

1. **Fork repository**
2. **Create feature branch**
3. **Make changes with tests**
4. **Submit pull request**
5. **Code review process**

### **Code Standards**

- **PEP 8** Python style guide
- **Type hints** for all functions
- **Docstrings** for documentation
- **Unit tests** required
- **Black** code formatting

---

## 🎯 Roadmap

### **Upcoming Features**

- **Mobile responsive** design
- **Dark mode** theme
- **Advanced charting** with more indicators
- **Email notifications** for profit milestones
- **Multi-language** support
- **Advanced risk analytics**

### **Performance Improvements**

- **Real-time WebSocket** data streaming
- **Offline capability** with data caching
- **Progressive web app** (PWA) features
- **Enhanced mobile** optimization

---

**Built with ❤️ for AINEON Elite Trading Operations**
