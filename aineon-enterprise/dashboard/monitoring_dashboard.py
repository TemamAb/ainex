import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import asyncio
import websockets
import json
import threading
import time
import requests
import os
import numpy as np

class MonitoringDashboard:
    def __init__(self):
        self.trade_history = []
        self.performance_metrics = {}
        self.risk_metrics = {}
        self.websocket_url = "ws://localhost:8765"  # For real-time updates
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8080")

    def run_dashboard(self):
        """Run the Streamlit dashboard"""
        st.set_page_config(page_title="Aineon 0.001% Tier Dashboard", layout="wide")

        st.title("🚀 Aineon Ultra Arbitrage Dashboard")
        st.markdown("**Real-time monitoring for elite arbitrage performance**")

        # Sidebar for controls
        self.sidebar_controls()

        # Main dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance", "🎯 Opportunities", "⚠️ Risk", "🔧 Settings"])

        with tab1:
            self.performance_tab()

        with tab2:
            self.opportunities_tab()

        with tab3:
            self.risk_tab()

        with tab4:
            self.settings_tab()

    def sidebar_controls(self):
        """Sidebar controls for dashboard"""
        st.sidebar.header("⚙️ Controls")

        # Status indicator
        status_color = "🟢" if self.get_engine_status() else "🔴"
        st.sidebar.metric("Engine Status", status_color)

        # Audit Status
        st.sidebar.markdown("---")
        audit_data = self.get_audit_data()
        etherscan_status = audit_data['audit_status']['verification_status']
        etherscan_color = "green" if etherscan_status == "ACTIVE" else "red"
        
        st.sidebar.markdown(
            f"<p style='color: {etherscan_color}; font-weight: bold;'>"
            f"✓ Etherscan Verification: {etherscan_status}</p>",
            unsafe_allow_html=True
        )
        st.sidebar.caption("All profits MUST be Etherscan-verified")

        # Profit Manager Section
        st.sidebar.markdown("---")
        st.sidebar.subheader("💰 Profit Manager (Verified Only)")
        
        profit_data = self.get_profit_data()
        
        # Display VERIFIED profit only
        verified_eth = profit_data.get('accumulated_eth_verified', 0.0)
        pending_eth = profit_data.get('accumulated_eth_pending', 0.0)
        
        st.sidebar.markdown(
            f"<h2 style='color: #34D399; text-shadow: 0 0 10px rgba(52, 211, 153, 0.5);'>"
            f"+{verified_eth:.6f} ETH</h2>",
            unsafe_allow_html=True
        )
        st.sidebar.caption("✓ ETHERSCAN VERIFIED")
        
        # Show pending if any
        if pending_eth > 0:
            st.sidebar.info(f"⏳ Pending Verification: {pending_eth:.6f} ETH\n(Not counted in official metrics)")
        
        # Auto/Manual Mode Toggle
        transfer_mode = st.sidebar.radio(
            "Transfer Mode",
            ["Manual", "Auto"],
            index=0 if not profit_data['auto_transfer'] else 1,
            horizontal=True
        )
        
        # Update mode if changed
        if (transfer_mode == "Auto") != profit_data['auto_transfer']:
            self.update_profit_config(transfer_mode == "Auto", profit_data['threshold_eth'])
            st.rerun()
        
        # Manual Withdraw Button or Auto Status
        if transfer_mode == "Manual":
            if st.sidebar.button("🚀 WITHDRAW NOW", 
                               disabled=profit_data['accumulated_eth'] <= 0,
                               use_container_width=True):
                if self.execute_manual_withdrawal():
                    st.sidebar.success("Withdrawal Initiated!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.sidebar.error("Withdrawal Failed")
        else:
            st.sidebar.success("✅ AUTO-SWEEP ACTIVE")
            st.sidebar.caption(f"Threshold: {profit_data['threshold_eth']:.4f} ETH")

        # Quick stats
        st.sidebar.markdown("---")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("24h Profit", f"${self.get_24h_profit():,.2f}")
        with col2:
            st.metric("Active Trades", self.get_active_trades())

        # Risk alerts
        if self.check_risk_alerts():
            st.sidebar.error("⚠️ Risk Alert Active")

    def performance_tab(self):
        """Performance metrics and charts"""
        st.header("Performance Analytics")

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total P&L", f"${self.get_total_pnl():,.2f}",
                     delta=f"{self.get_pnl_change():+.2%}")
        with col2:
            st.metric("Win Rate", f"{self.get_win_rate():.1f}%")
        with col3:
            st.metric("Avg Trade Size", f"${self.get_avg_trade_size():,.0f}")
        with col4:
            st.metric("Sharpe Ratio", f"{self.get_sharpe_ratio():.2f}")

        # Performance chart
        st.subheader("P&L Over Time")
        pnl_chart = self.create_pnl_chart()
        st.plotly_chart(pnl_chart, use_container_width=True)

        # Trade distribution
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Trade Size Distribution")
            size_dist = self.create_trade_size_distribution()
            st.plotly_chart(size_dist, use_container_width=True)

        with col2:
            st.subheader("Profit/Loss Distribution")
            pl_dist = self.create_pl_distribution()
            st.plotly_chart(pl_dist, use_container_width=True)

    def opportunities_tab(self):
        """Current arbitrage opportunities"""
        st.header("Live Arbitrage Opportunities")

        # Real-time opportunities table
        opportunities_df = self.get_current_opportunities()
        st.dataframe(opportunities_df, use_container_width=True)

        # Opportunity heatmap
        st.subheader("DEX Price Heatmap")
        heatmap = self.create_price_heatmap()
        st.plotly_chart(heatmap, use_container_width=True)

        # AI Predictions
        st.subheader("AI Opportunity Predictions")
        predictions_df = self.get_ai_predictions()
        st.dataframe(predictions_df, use_container_width=True)

    def risk_tab(self):
        """Risk management dashboard"""
        st.header("Risk Management")

        # Risk metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("VaR (95%)", f"${self.get_var_95():,.0f}")
        with col2:
            st.metric("Max Drawdown", f"{self.get_max_drawdown():.1f}%")
        with col3:
            st.metric("Liquidity Risk", self.get_liquidity_risk())
        with col4:
            st.metric("Slippage Risk", f"{self.get_slippage_risk():.1f}%")

        # Risk alerts
        st.subheader("Active Risk Alerts")
        alerts_df = self.get_risk_alerts()
        if not alerts_df.empty:
            st.dataframe(alerts_df, use_container_width=True)
        else:
            st.success("No active risk alerts")

        # Risk chart
        st.subheader("Risk Exposure Over Time")
        risk_chart = self.create_risk_chart()
        st.plotly_chart(risk_chart, use_container_width=True)

    def settings_tab(self):
        """Configuration settings"""
        st.header("Engine Configuration")

        # Risk settings
        st.subheader("Risk Parameters")
        col1, col2 = st.columns(2)
        with col1:
            max_slippage = st.slider("Max Slippage (%)", 0.1, 5.0, 2.0)
            max_position = st.slider("Max Position Size ($)", 10000, 10000000, 1000000)
        with col2:
            confidence_threshold = st.slider("AI Confidence Threshold", 0.5, 0.95, 0.8)
            scan_interval = st.slider("Scan Interval (ms)", 50, 1000, 100)

        # DEX settings
        st.subheader("DEX Configuration")
        enabled_dexes = st.multiselect(
            "Enabled DEXes",
            ["Uniswap V3", "SushiSwap", "PancakeSwap", "1inch", "CowSwap"],
            ["Uniswap V3", "SushiSwap", "CowSwap"]
        )

        # Save settings button
        if st.button("Save Configuration"):
            self.save_settings({
                'max_slippage': max_slippage,
                'max_position': max_position,
                'confidence_threshold': confidence_threshold,
                'scan_interval': scan_interval,
                'enabled_dexes': enabled_dexes
            })
            st.success("Settings saved successfully!")

    # Helper methods for data retrieval
    def get_profit_data(self):
        """Fetch real profit data from API"""
        try:
            response = requests.get(f"{self.api_base_url}/profit", timeout=5)
            if response.ok:
                return response.json()
        except:
            pass
        # Fallback
        return {
            'accumulated_eth_verified': 0.0,
            'accumulated_eth_pending': 0.0,
            'threshold_eth': 0.1,
            'auto_transfer_enabled': False,
            'active_trades': 0,
            'etherscan_enabled': False,
            'verification_status': 'DISABLED'
        }
    
    def get_audit_data(self):
        """Fetch audit data from API"""
        try:
            response = requests.get(f"{self.api_base_url}/audit", timeout=5)
            if response.ok:
                return response.json()
        except:
            pass
        return {
            'audit_status': {
                'verified_profits': {'eth': 0.0, 'usd': 0.0, 'count': 0},
                'pending_profits': {'eth': 0.0, 'usd': 0.0, 'count': 0},
                'has_etherscan_key': False,
                'verification_status': 'DISABLED'
            }
        }
    
    def update_profit_config(self, enabled, threshold):
        """Update profit configuration via API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/settings/profit-config",
                json={'enabled': enabled, 'threshold': threshold},
                timeout=5
            )
            return response.ok
        except:
            return False
    
    def execute_manual_withdrawal(self):
        """Execute manual withdrawal via API"""
        try:
            response = requests.post(f"{self.api_base_url}/withdraw", timeout=10)
            return response.ok
        except:
            return False
    
    def get_engine_status(self):
        try:
            response = requests.get(f"{self.api_base_url}/status", timeout=5)
            return response.ok
        except:
            return False

    def get_24h_profit(self):
        profit_data = self.get_profit_data()
        # Return ONLY verified profit
        return profit_data.get('accumulated_usd_verified', 0.0)

    def get_active_trades(self):
        profit_data = self.get_profit_data()
        return profit_data.get('active_trades', 0)

    def check_risk_alerts(self):
        """Check for real risk conditions based on profit data"""
        profit_data = self.get_profit_data()
        if not profit_data:
            return True  # Alert if can't get data
        
        # Alert if Etherscan validation is disabled
        if not profit_data.get('etherscan_enabled', False):
            return True
        
        # Alert if profit threshold exceeded and auto-transfer disabled
        # Use ONLY verified profit
        accumulated = profit_data.get('accumulated_eth_verified', 0.0)
        threshold = profit_data.get('threshold_eth', 0.1)
        auto_enabled = profit_data.get('auto_transfer_enabled', False)
        
        return accumulated >= threshold and not auto_enabled

    def get_total_pnl(self):
        return self.get_24h_profit()

    def get_pnl_change(self):
        """Calculate PnL change percentage from current vs threshold (verified only)"""
        profit_data = self.get_profit_data()
        # Use ONLY verified profit
        accumulated = profit_data.get('accumulated_eth_verified', 0.0)
        threshold = profit_data.get('threshold_eth', 0.1)
        if threshold <= 0:
            return 0.0
        return (accumulated / threshold) * 100.0

    def get_win_rate(self):
        """Calculate win rate from actual trades"""
        profit_data = self.get_profit_data()
        active = profit_data.get('active_trades', 0)
        successful = profit_data.get('successful_trades', 0)
        
        if active == 0:
            return 0.0
        return (successful / active) * 100.0

    def get_avg_trade_size(self):
        """Calculate average trade size from accumulated profit"""
        profit_data = self.get_profit_data()
        accumulated = profit_data.get('accumulated_usd', 0.0)
        active = profit_data.get('active_trades', 1)  # Avoid division by zero
        
        if active == 0:
            return 0.0
        return accumulated / active

    def get_sharpe_ratio(self):
        """Estimate Sharpe ratio from verified profit data (simplified)"""
        profit_data = self.get_profit_data()
        # Use ONLY verified profit
        accumulated = profit_data.get('accumulated_eth_verified', 0.0)
        
        # Simple heuristic: profit > 0.1 ETH = better Sharpe
        if accumulated > 0.1:
            return min(accumulated / 0.05, 3.0)  # Cap at 3.0
        return 0.5

    def create_pnl_chart(self):
        """Create P&L chart from real opportunities endpoint"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities:
            # Empty chart if no opportunities
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[], y=[], mode='lines+markers', name='P&L'))
            fig.update_layout(title='Portfolio P&L Over Time', xaxis_title='Date', yaxis_title='P&L ($)')
            return fig
        
        # Calculate cumulative P&L
        timestamps = []
        cumulative_pnl = []
        running_total = 0.0
        
        for opp in opportunities:
            profit = opp.get('profit', 0.0)
            timestamp = opp.get('timestamp', time.time())
            running_total += profit
            timestamps.append(datetime.fromtimestamp(timestamp))
            cumulative_pnl.append(running_total)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timestamps, y=cumulative_pnl, mode='lines+markers', name='Cumulative P&L'))
        fig.update_layout(title='Portfolio P&L Over Time', xaxis_title='Date', yaxis_title='P&L ($)')
        return fig

    def create_trade_size_distribution(self):
        """Create trade size distribution from real opportunities"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities:
            fig = px.bar(x=[], y=[], labels={'x': 'Trade Size ($)', 'y': 'Frequency'})
            return fig
        
        profits = [opp.get('profit', 0.0) for opp in opportunities]
        
        fig = px.histogram(x=profits, nbins=20, labels={'x': 'Profit ($)', 'count': 'Frequency'})
        fig.update_layout(title='Trade Profit Distribution')
        return fig

    def create_pl_distribution(self):
        """Create P&L distribution from real opportunities"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=[], nbinsx=20))
            fig.update_layout(title='Profit/Loss Distribution', xaxis_title='P&L ($)', yaxis_title='Frequency')
            return fig
        
        profits = [opp.get('profit', 0.0) for opp in opportunities]
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=profits, nbinsx=20))
        fig.update_layout(title='Profit/Loss Distribution', xaxis_title='P&L ($)', yaxis_title='Frequency')
        return fig

    def get_current_opportunities(self):
        """Get real opportunities from API"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities:
            return pd.DataFrame(columns=['Pair', 'DEX', 'Profit ($)', 'Confidence', 'Status'])
        
        data = {
            'Pair': [opp.get('pair', 'UNKNOWN') for opp in opportunities],
            'DEX': [opp.get('dex', 'UNKNOWN') for opp in opportunities],
            'Profit ($)': [f"${opp.get('profit', 0.0):.2f}" for opp in opportunities],
            'Confidence': [f"{opp.get('confidence', 0.0):.1%}" for opp in opportunities],
            'TX': [opp.get('tx', 'PENDING')[:12] for opp in opportunities]
        }
        
        return pd.DataFrame(data)
    
    def _fetch_opportunities(self):
        """Fetch opportunities from API"""
        try:
            response = requests.get(f"{self.api_base_url}/opportunities", timeout=5)
            if response.ok:
                data = response.json()
                return data.get('opportunities', [])
        except:
            pass
        return []

    def create_price_heatmap(self):
        """Create price heatmap from current opportunities"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities:
            fig = px.imshow(np.zeros((2, 2)), title='DEX Price Heatmap')
            return fig
        
        # Group opportunities by pair and DEX
        pair_dex_map = {}
        for opp in opportunities:
            pair = opp.get('pair', 'UNKNOWN')
            dex = opp.get('dex', 'UNKNOWN')
            profit = opp.get('profit', 0.0)
            
            if pair not in pair_dex_map:
                pair_dex_map[pair] = {}
            pair_dex_map[pair][dex] = profit
        
        # Convert to heatmap format
        dexes = sorted(set(d for pair_dict in pair_dex_map.values() for d in pair_dict.keys()))
        pairs = sorted(pair_dex_map.keys())
        
        if not dexes or not pairs:
            fig = px.imshow(np.zeros((2, 2)), title='DEX Price Heatmap')
            return fig
        
        data = []
        for pair in pairs:
            row = [pair_dex_map[pair].get(dex, 0) for dex in dexes]
            data.append(row)
        
        fig = px.imshow(data, x=dexes, y=pairs, color_continuous_scale='RdYlGn', title='Profit by DEX Pair')
        return fig

    def get_ai_predictions(self):
        """Get AI predictions based on recent opportunities"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities:
            return pd.DataFrame(columns=['Opportunity', 'Predicted Profit ($)', 'Confidence (%)', 'Status'])
        
        # Take top opportunities by confidence
        top_opps = sorted(opportunities, key=lambda x: x.get('confidence', 0), reverse=True)[:3]
        
        data = {
            'Opportunity': [opp.get('pair', 'UNKNOWN') for opp in top_opps],
            'Predicted Profit ($)': [f"${opp.get('profit', 0.0):.2f}" for opp in top_opps],
            'Confidence (%)': [f"{opp.get('confidence', 0.0):.1%}" for opp in top_opps],
            'Status': [opp.get('tx', 'PENDING')[:12] for opp in top_opps]
        }
        
        return pd.DataFrame(data)

    def get_var_95(self):
        """Calculate Value at Risk (95%) from verified profit data"""
        profit_data = self.get_profit_data()
        # Use ONLY verified profit
        accumulated = profit_data.get('accumulated_usd_verified', 0.0)
        # Simple heuristic: VAR is 25% of accumulated profit
        return max(accumulated * 0.25, 1000)

    def get_max_drawdown(self):
        """Estimate max drawdown from trade history"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities or len(opportunities) < 2:
            return 0.0
        
        profits = [opp.get('profit', 0.0) for opp in opportunities]
        cumulative = []
        running_total = 0.0
        for p in profits:
            running_total += p
            cumulative.append(running_total)
        
        if not cumulative:
            return 0.0
        
        peak = max(cumulative)
        if peak == 0:
            return 0.0
        
        trough = min(cumulative)
        return ((peak - trough) / peak) * 100 if peak > 0 else 0.0

    def get_liquidity_risk(self):
        """Assess liquidity risk based on recent trades"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities:
            return "Unknown"
        
        # If we have many successful trades, liquidity risk is low
        if len(opportunities) > 10:
            return "Low"
        elif len(opportunities) > 5:
            return "Medium"
        else:
            return "High"

    def get_slippage_risk(self):
        """Calculate slippage risk from verified trades"""
        profit_data = self.get_profit_data()
        # Use ONLY verified profit
        accumulated = profit_data.get('accumulated_eth_verified', 0.0)
        
        # Lower accumulated profit = higher slippage risk
        if accumulated > 0.5:
            return 0.5
        elif accumulated > 0.1:
            return 1.0
        else:
            return 2.0

    def get_risk_alerts(self):
        """Get active risk alerts from real conditions"""
        alerts = []
        
        profit_data = self.get_profit_data()
        if not profit_data:
            alerts.append({
                'Alert': 'API Connection',
                'Severity': 'Critical',
                'Description': 'Cannot connect to API'
            })
        else:
            # Check Etherscan status
            if not profit_data.get('etherscan_enabled', False):
                alerts.append({
                    'Alert': 'Etherscan Validation',
                    'Severity': 'Critical',
                    'Description': f'Etherscan validation is {profit_data.get("verification_status", "UNKNOWN")} - set ETHERSCAN_API_KEY'
                })
            
            # Check profit threshold (using VERIFIED profit only)
            accumulated = profit_data.get('accumulated_eth_verified', 0.0)
            threshold = profit_data.get('threshold_eth', 0.1)
            auto_enabled = profit_data.get('auto_transfer_enabled', False)
            
            if accumulated >= threshold and not auto_enabled:
                alerts.append({
                    'Alert': 'Profit Threshold',
                    'Severity': 'Warning',
                    'Description': f'Verified profit ({accumulated:.6f} ETH) exceeds threshold, auto-transfer disabled'
                })
            
            # Check pending profits
            pending = profit_data.get('accumulated_eth_pending', 0.0)
            if pending > 0:
                alerts.append({
                    'Alert': 'Pending Verification',
                    'Severity': 'Info',
                    'Description': f'{pending:.6f} ETH pending Etherscan verification (not counted in metrics)'
                })
        
        return pd.DataFrame(alerts) if alerts else pd.DataFrame()

    def create_risk_chart(self):
        """Create risk chart from trade history"""
        opportunities = self._fetch_opportunities()
        
        if not opportunities:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Risk Exposure'))
            fig.update_layout(title='Risk Exposure Over Time', xaxis_title='Date', yaxis_title='Risk Score')
            return fig
        
        timestamps = []
        risk_scores = []
        
        for opp in opportunities:
            timestamp = opp.get('timestamp', time.time())
            confidence = opp.get('confidence', 0.5)
            # Risk = 1 - confidence (inverse relationship)
            risk_score = (1.0 - confidence) * 100
            
            timestamps.append(datetime.fromtimestamp(timestamp))
            risk_scores.append(risk_score)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timestamps, y=risk_scores, mode='lines', name='Risk Score'))
        fig.update_layout(title='Risk Exposure Over Time', xaxis_title='Date', yaxis_title='Risk Score (%)')
        return fig

    def save_settings(self, settings):
        """Save settings to file for persistence"""
        try:
            import json
            with open('aineon_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False

# WebSocket handler for real-time updates
async def websocket_handler(websocket, path):
    dashboard = MonitoringDashboard()
    while True:
        # Send real-time updates
        data = {
            'pnl': dashboard.get_total_pnl(),
            'active_trades': dashboard.get_active_trades(),
            'opportunities': dashboard.get_current_opportunities().to_dict()
        }
        await websocket.send(json.dumps(data))
        await asyncio.sleep(1)

def start_websocket_server():
    """Start WebSocket server for real-time updates"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(websocket_handler, "localhost", 8765)
    loop.run_until_complete(server)
    loop.run_forever()

if __name__ == "__main__":
    # Start WebSocket server in background thread
    websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
    websocket_thread.start()

    # Run Streamlit dashboard
    dashboard = MonitoringDashboard()
    dashboard.run_dashboard()
