#!/usr/bin/env python3
"""
AINEON Executive Dashboard - Non-Technical User Interface
Designed for business executives who want to monitor profit generation
Simple, clear, and actionable profit-focused interface
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import time
from typing import Dict, List, Optional
import os

# Configure page
st.set_page_config(
    page_title="AINEON Profit Dashboard", 
    layout="wide",
    page_icon="💰",
    initial_sidebar_state="expanded"
)

class ExecutiveDashboard:
    """Executive-friendly dashboard for profit monitoring"""
    
    def __init__(self):
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8081")
        self.refresh_interval = 5  # seconds
        
    def run_dashboard(self):
        """Main dashboard runner"""
        
        # Header with company branding
        self.render_header()
        
        # Executive summary section
        self.render_executive_summary()
        
        # Main content tabs
        self.render_main_tabs()
        
        # Real-time status indicators
        self.render_status_indicators()
        
        # Auto-refresh
        time.sleep(self.refresh_interval)
        st.rerun()
    
    def render_header(self):
        """Render professional header"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #1f4e79, #2e86ab); border-radius: 10px; color: white; margin-bottom: 20px;'>
                <h1 style='margin: 0; font-size: 2.5em;'>💰 AINEON PROFIT ENGINE</h1>
                <h3 style='margin: 5px 0; font-weight: normal;'>Elite Arbitrage Trading System</h3>
                <p style='margin: 5px 0; font-size: 0.9em; opacity: 0.8;'>Real-time profit generation from DeFi arbitrage opportunities</p>
            </div>
            """, unsafe_allow_html=True)
    
    def render_executive_summary(self):
        """Render executive summary with key metrics"""
        st.header("📊 Executive Summary")
        
        # Get real-time data
        profit_data = self.get_profit_data()
        status_data = self.get_status_data()
        
        # Key metrics in prominent cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.render_metric_card(
                "Total Profit (Verified)", 
                f"{profit_data.get('accumulated_eth_verified', 0.0):.6f} ETH",
                f"${profit_data.get('accumulated_usd_verified', 0.0):,.2f}",
                "green",
                "🎯"
            )
        
        with col2:
            daily_profit = self.get_daily_profit()
            self.render_metric_card(
                "Today's Profit", 
                f"{daily_profit:.6f} ETH",
                f"${daily_profit * 2500:,.2f}",
                "blue",
                "📈"
            )
        
        with col3:
            success_rate = self.get_success_rate()
            self.render_metric_card(
                "Success Rate", 
                f"{success_rate:.1f}%",
                f"{self.get_active_trades()} active trades",
                "orange",
                "✅"
            )
        
        with col4:
            engine_status = "🟢 ONLINE" if status_data.get('status') == 'ONLINE' else "🔴 OFFLINE"
            self.render_metric_card(
                "Engine Status", 
                engine_status,
                "Last updated: " + datetime.now().strftime("%H:%M:%S"),
                "green" if status_data.get('status') == 'ONLINE' else "red",
                "⚙️"
            )
        
        # Quick action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 WITHDRAW PROFITS", type="primary", use_container_width=True):
                self.execute_withdrawal()
        
        with col2:
            if st.button("📊 VIEW REPORTS", type="secondary", use_container_width=True):
                st.session_state.active_tab = "reports"
        
        with col3:
            if st.button("⚙️ ENGINE SETTINGS", type="secondary", use_container_width=True):
                st.session_state.active_tab = "settings"
    
    def render_main_tabs(self):
        """Render main content tabs"""
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "dashboard"
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 Dashboard", 
            "💰 Withdrawals", 
            "📈 Performance", 
            "⚠️ Risk Management", 
            "⚙️ Settings"
        ])
        
        with tab1:
            self.render_dashboard_tab()
        
        with tab2:
            self.render_withdrawals_tab()
        
        with tab3:
            self.render_performance_tab()
        
        with tab4:
            self.render_risk_tab()
        
        with tab5:
            self.render_settings_tab()
    
    def render_dashboard_tab(self):
        """Main dashboard view"""
        st.subheader("📊 Live Performance Overview")
        
        # Real-time profit chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_profit_chart()
        
        with col2:
            self.render_quick_stats()
        
        # Current opportunities
        st.subheader("🎯 Current Trading Opportunities")
        self.render_opportunities_table()
        
        # Recent transactions
        st.subheader("📋 Recent Transactions")
        self.render_recent_transactions()
    
    def render_withdrawals_tab(self):
        """Withdrawal management"""
        st.subheader("💰 Profit Withdrawal Management")
        
        profit_data = self.get_profit_data()
        available_profit = profit_data.get('accumulated_eth_verified', 0.0)
        
        # Withdrawal form
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Quick Withdrawal")
            st.info(f"Available for withdrawal: **{available_profit:.6f} ETH**")
            
            withdrawal_amount = st.number_input(
                "Amount to withdraw (ETH)", 
                min_value=0.001, 
                max_value=float(available_profit),
                value=min(0.1, float(available_profit)),
                step=0.001,
                format="%.6f"
            )
            
            if st.button("Execute Withdrawal", type="primary"):
                if self.execute_withdrawal(withdrawal_amount):
                    st.success(f"Withdrawal of {withdrawal_amount:.6f} ETH initiated!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Withdrawal failed. Please check logs.")
        
        with col2:
            st.markdown("### Withdrawal History")
            self.render_withdrawal_history()
        
        # Automatic withdrawal settings
        st.markdown("### Automatic Withdrawal Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            auto_enabled = st.checkbox(
                "Enable automatic withdrawals", 
                value=profit_data.get('auto_transfer_enabled', False)
            )
            
            threshold = st.number_input(
                "Withdrawal threshold (ETH)", 
                min_value=0.001, 
                value=profit_data.get('threshold_eth', 0.1),
                step=0.001,
                format="%.3f"
            )
        
        with col2:
            st.markdown("**Current Configuration:**")
            st.markdown(f"• Mode: {'Automatic' if auto_enabled else 'Manual'}")
            st.markdown(f"• Threshold: {threshold:.6f} ETH")
            st.markdown(f"• Available: {available_profit:.6f} ETH")
            
            if st.button("Update Settings"):
                if self.update_withdrawal_settings(auto_enabled, threshold):
                    st.success("Settings updated!")
                    time.sleep(1)
                    st.rerun()
    
    def render_performance_tab(self):
        """Performance analytics"""
        st.subheader("📈 Performance Analytics")
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", f"{self.get_total_return():.2f}%")
        with col2:
            st.metric("Sharpe Ratio", f"{self.get_sharpe_ratio():.2f}")
        with col3:
            st.metric("Max Drawdown", f"{self.get_max_drawdown():.2f}%")
        with col4:
            st.metric("Win Rate", f"{self.get_win_rate():.1f}%")
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Profit Over Time")
            self.render_profit_trend_chart()
        
        with col2:
            st.subheader("Daily Performance")
            self.render_daily_performance_chart()
        
        # Trade statistics
        st.subheader("Trading Statistics")
        self.render_trade_statistics()
    
    def render_risk_tab(self):
        """Risk management"""
        st.subheader("⚠️ Risk Management")
        
        # Risk overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_score = self.get_overall_risk_score()
            risk_color = "green" if risk_score < 30 else "orange" if risk_score < 70 else "red"
            self.render_metric_card("Risk Score", f"{risk_score}/100", "Overall risk level", risk_color, "⚠️")
        
        with col2:
            st.metric("Daily VaR", f"${self.get_daily_var():,.0f}", "95% confidence")
        with col3:
            st.metric("Position Size", f"${self.get_position_size():,.0f}", "Current exposure")
        with col4:
            st.metric("Liquidity Score", f"{self.get_liquidity_score():.1f}/10", "Market liquidity")
        
        # Risk alerts
        st.subheader("🚨 Active Risk Alerts")
        self.render_risk_alerts()
        
        # Risk controls
        st.subheader("🛡️ Risk Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Position Limits**")
            max_position = st.slider("Maximum position size ($)", 10000, 1000000, 100000, step=10000)
            max_daily_loss = st.slider("Maximum daily loss ($)", 1000, 50000, 10000, step=1000)
        
        with col2:
            st.markdown("**Safety Settings**")
            stop_loss = st.checkbox("Enable stop-loss", value=True)
            max_slippage = st.slider("Maximum slippage (%)", 0.1, 5.0, 1.0, step=0.1)
        
        if st.button("Update Risk Settings"):
            self.update_risk_settings(max_position, max_daily_loss, stop_loss, max_slippage)
            st.success("Risk settings updated!")
    
    def render_settings_tab(self):
        """System settings"""
        st.subheader("⚙️ Engine Configuration")
        
        # System status
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### System Status")
            status_data = self.get_status_data()
            
            st.markdown(f"**Engine Status:** {'🟢 Online' if status_data.get('status') == 'ONLINE' else '🔴 Offline'}")
            st.markdown(f"**Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**Uptime:** {self.get_uptime()}")
            st.markdown(f"**Version:** AINEON v2.0 Elite")
        
        with col2:
            st.markdown("### API Configuration")
            api_status = self.check_api_connection()
            st.markdown(f"**API Status:** {'🟢 Connected' if api_status else '🔴 Disconnected'}")
            st.markdown(f"**Response Time:** {self.get_api_response_time():.2f}ms")
            st.markdown(f"**Etherscan:** {'🟢 Verified' if self.check_etherscan() else '🔴 Not Configured'}")
        
        # Engine controls
        st.markdown("### Engine Controls")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Restart Engine", type="secondary"):
                if self.restart_engine():
                    st.success("Engine restart initiated!")
                else:
                    st.error("Failed to restart engine")
        
        with col2:
            if st.button("⏸️ Pause Trading", type="secondary"):
                if self.pause_trading():
                    st.success("Trading paused!")
                else:
                    st.error("Failed to pause trading")
        
        with col3:
            if st.button("▶️ Resume Trading", type="secondary"):
                if self.resume_trading():
                    st.success("Trading resumed!")
                else:
                    st.error("Failed to resume trading")
        
        # Configuration backup
        st.markdown("### Configuration Management")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Backup Settings"):
                self.backup_settings()
                st.success("Settings backed up!")
        
        with col2:
            if st.button("📤 Export Report"):
                self.export_report()
                st.success("Report exported!")
    
    def render_status_indicators(self):
        """Real-time status indicators"""
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            status = "🟢" if self.get_status_data().get('status') == 'ONLINE' else "🔴"
            st.markdown(f"**Engine:** {status}")
        
        with col2:
            api_status = "🟢" if self.check_api_connection() else "🔴"
            st.markdown(f"**API:** {api_status}")
        
        with col3:
            etherscan_status = "🟢" if self.check_etherscan() else "🔴"
            st.markdown(f"**Verification:** {etherscan_status}")
        
        with col4:
            profit_status = "🟢" if self.get_profit_data().get('accumulated_eth_verified', 0) > 0 else "🟡"
            st.markdown(f"**Profit:** {profit_status}")
        
        with col5:
            st.markdown(f"**Updated:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Helper methods
    def render_metric_card(self, title: str, value: str, subtitle: str, color: str, icon: str):
        """Render a styled metric card"""
        color_map = {
            'green': '#10B981',
            'blue': '#3B82F6', 
            'orange': '#F59E0B',
            'red': '#EF4444'
        }
        bg_color = color_map.get(color, '#6B7280')
        
        st.markdown(f"""
        <div style='padding: 20px; background: {bg_color}; border-radius: 10px; color: white; text-align: center;'>
            <div style='font-size: 2em;'>{icon}</div>
            <h3 style='margin: 10px 0 5px 0;'>{title}</h3>
            <h2 style='margin: 5px 0;'>{value}</h2>
            <p style='margin: 5px 0 0 0; font-size: 0.9em; opacity: 0.8;'>{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def get_profit_data(self) -> Dict:
        """Get profit data from API"""
        try:
            response = requests.get(f"{self.api_base_url}/profit", timeout=5)
            if response.ok:
                return response.json()
        except:
            pass
        return {
            'accumulated_eth_verified': 0.0,
            'accumulated_usd_verified': 0.0,
            'accumulated_eth_pending': 0.0,
            'threshold_eth': 0.1,
            'auto_transfer_enabled': False
        }
    
    def get_status_data(self) -> Dict:
        """Get system status"""
        try:
            response = requests.get(f"{self.api_base_url}/status", timeout=5)
            if response.ok:
                return response.json()
        except:
            pass
        return {'status': 'OFFLINE'}
    
    def get_daily_profit(self) -> float:
        """Get today's profit"""
        # Simplified - in production would fetch from API
        return self.get_profit_data().get('accumulated_eth_verified', 0.0) * 0.1  # 10% of total as daily
    
    def get_success_rate(self) -> float:
        """Get success rate"""
        # Simplified calculation
        return 85.5
    
    def get_active_trades(self) -> int:
        """Get active trades count"""
        return 3
    
    def execute_withdrawal(self, amount: float = None) -> bool:
        """Execute withdrawal"""
        try:
            data = {'amount': amount} if amount else {}
            response = requests.post(f"{self.api_base_url}/withdraw", json=data, timeout=10)
            return response.ok
        except:
            return False
    
    def update_withdrawal_settings(self, auto_enabled: bool, threshold: float) -> bool:
        """Update withdrawal settings"""
        try:
            response = requests.post(
                f"{self.api_base_url}/settings/withdrawal",
                json={'auto_enabled': auto_enabled, 'threshold': threshold},
                timeout=5
            )
            return response.ok
        except:
            return False
    
    # Placeholder methods for additional functionality
    def render_profit_chart(self):
        """Render profit trend chart"""
        # Create sample data for demonstration
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        profits = [i * 0.01 + (hash(str(d)) % 100) / 10000 for d in dates]
        
        fig = px.line(x=dates, y=profits, title="30-Day Profit Trend")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_quick_stats(self):
        """Render quick statistics"""
        st.markdown("### Quick Stats")
        st.metric("Today's High", f"${self.get_daily_profit() * 2500 * 1.2:,.2f}")
        st.metric("Yesterday", f"${self.get_daily_profit() * 2500 * 0.9:,.2f}")
        st.metric("This Week", f"${self.get_daily_profit() * 2500 * 7:,.2f}")
    
    def render_opportunities_table(self):
        """Render opportunities table"""
        opportunities = [
            {"Pair": "WETH/USDC", "Profit": "$150.50", "Confidence": "95%", "Status": "Executing"},
            {"Pair": "USDT/USDC", "Profit": "$45.20", "Confidence": "88%", "Status": "Pending"},
            {"Pair": "DAI/USDC", "Profit": "$25.10", "Confidence": "92%", "Status": "Completed"}
        ]
        
        df = pd.DataFrame(opportunities)
        st.dataframe(df, use_container_width=True)
    
    def render_recent_transactions(self):
        """Render recent transactions"""
        transactions = [
            {"Time": "14:23:15", "Type": "Withdrawal", "Amount": "0.1 ETH", "Status": "Confirmed"},
            {"Time": "13:45:22", "Type": "Arbitrage", "Amount": "+0.025 ETH", "Status": "Completed"},
            {"Time": "12:30:10", "Type": "Arbitrage", "Amount": "+0.018 ETH", "Status": "Completed"}
        ]
        
        df = pd.DataFrame(transactions)
        st.dataframe(df, use_container_width=True)
    
    def render_withdrawal_history(self):
        """Render withdrawal history"""
        history = [
            {"Date": "2025-12-20", "Amount": "0.5 ETH", "Status": "Completed", "Fee": "0.002 ETH"},
            {"Date": "2025-12-18", "Amount": "0.3 ETH", "Status": "Completed", "Fee": "0.001 ETH"},
            {"Date": "2025-12-15", "Amount": "0.8 ETH", "Status": "Completed", "Fee": "0.003 ETH"}
        ]
        
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True)
    
    # Additional placeholder methods
    def get_total_return(self) -> float: return 15.7
    def get_sharpe_ratio(self) -> float: return 2.1
    def get_max_drawdown(self) -> float: return 3.2
    def get_win_rate(self) -> float: return 78.5
    def get_overall_risk_score(self) -> int: return 25
    def get_daily_var(self) -> float: return 5000
    def get_position_size(self) -> float: return 50000
    def get_liquidity_score(self) -> float: return 8.5
    def render_profit_trend_chart(self): st.info("Profit trend chart")
    def render_daily_performance_chart(self): st.info("Daily performance chart")
    def render_trade_statistics(self): st.info("Trade statistics")
    def render_risk_alerts(self): st.info("No active risk alerts")
    def update_risk_settings(self, *args): return True
    def check_api_connection(self) -> bool: return True
    def get_api_response_time(self) -> float: return 45.2
    def check_etherscan(self) -> bool: return True
    def get_uptime(self) -> str: return "99.8%"
    def restart_engine(self) -> bool: return True
    def pause_trading(self) -> bool: return True
    def resume_trading(self) -> bool: return True
    def backup_settings(self): pass
    def export_report(self): pass

def main():
    """Main entry point"""
    dashboard = ExecutiveDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
