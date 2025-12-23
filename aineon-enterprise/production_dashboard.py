#!/usr/bin/env python3
"""
AINEON Production Dashboard - Streamlit
Real-time monitoring dashboard for Render deployment
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta
import time
import os
from typing import Dict, List, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="AINEON Flash Loan Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
    .danger-metric {
        border-left-color: #dc3545;
    }
    .profit-positive {
        color: #28a745;
        font-weight: bold;
    }
    .profit-negative {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# ============================================================================

===
# API Configurationdef get_api_base_url():
    """Get API base URL for production"""
    # Check environment variable first
    api_url = os.getenv("API_BASE_URL")
    if api_url:
        return api_url
    
    # Check if running locally vs production
    if os.getenv("ENVIRONMENT") == "production":
        # In production, use relative URL to Render service
        return "https://aineon-engine-api.onrender.com"
    else:
        # Local development
        return "http://0.0.0.0:8000"

# ============================================================================
# Data Fetching Functions
# ============================================================================

@st.cache_data(ttl=30)  # Cache for 30 seconds
def fetch_api_data(endpoint: str) -> Optional[Dict]:
    """Fetch data from API with caching"""
    try:
        base_url = get_api_base_url()
        url = f"{base_url}{endpoint}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from API: {e}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {e}")
        return None

def fetch_health_status() -> Optional[Dict]:
    """Fetch health status"""
    return fetch_api_data("/api/health")

def fetch_engine_status() -> Optional[Dict]:
    """Fetch engine status"""
    return fetch_api_data("/api/status")

def fetch_profit_metrics() -> Optional[Dict]:
    """Fetch profit metrics"""
    return fetch_api_data("/api/profit-metrics")

def fetch_recent_transactions(limit: int = 20) -> Optional[List[Dict]]:
    """Fetch recent transactions"""
    return fetch_api_data(f"/api/transactions?limit={limit}")

def fetch_active_opportunities() -> Optional[List[Dict]]:
    """Fetch active opportunities"""
    return fetch_api_data("/api/opportunities")

# ============================================================================
# Dashboard Components
# ============================================================================

def display_header():
    """Display main header"""
    st.markdown('<h1 class="main-header">⚡ AINEON Flash Loan Engine</h1>', unsafe_allow_html=True)
    st.markdown("---")

def display_health_status():
    """Display system health status"""
    st.subheader("🏥 System Health")
    
    health_data = fetch_health_status()
    if health_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Status", 
                health_data.get("status", "Unknown"),
                delta=None
            )
        
        with col2:
            uptime = health_data.get("uptime_seconds", 0)
            uptime_hours = uptime / 3600
            st.metric(
                "Uptime", 
                f"{uptime_hours:.1f}h",
                delta=None
            )
        
        with col3:
            st.metric(
                "Environment", 
                health_data.get("environment", "Unknown"),
                delta=None
            )
        
        with col4:
            st.metric(
                "Version", 
                health_data.get("version", "Unknown"),
                delta=None
            )
    else:
        st.error("Unable to fetch health status")

def display_profit_metrics():
    """Display profit metrics"""
    st.subheader("💰 Profit Metrics")
    
    metrics = fetch_profit_metrics()
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_usd = metrics.get("total_profit_usd", 0)
            st.metric(
                "Total Profit (USD)", 
                f"${total_usd:,.2f}",
                delta=None
            )
        
        with col2:
            total_eth = metrics.get("total_profit_eth", 0)
            st.metric(
                "Total Profit (ETH)", 
                f"{total_eth:.6f} ETH",
                delta=None
            )
        
        with col3:
            successful = metrics.get("successful_transactions", 0)
            st.metric(
                "Successful Trades", 
                f"{successful:,}",
                delta=None
            )
        
        with col4:
            success_rate = metrics.get("success_rate", 0)
            st.metric(
                "Success Rate", 
                f"{success_rate:.1f}%",
                delta=None
            )
    else:
        st.error("Unable to fetch profit metrics")

def display_engine_status():
    """Display current engine status"""
    st.subheader("🔧 Engine Status")
    
    status = fetch_engine_status()
    if status:
        col1, col2 = st.columns(2)
        
        with col1:
            engine_status = status.get("status", "Unknown")
            if engine_status == "ACTIVE":
                st.success(f"Engine Status: {engine_status}")
            elif engine_status == "STOPPED":
                st.warning(f"Engine Status: {engine_status}")
            else:
                st.info(f"Engine Status: {engine_status}")
        
        with col2:
            active_ops = status.get("active_opportunities", 0)
            st.metric("Active Opportunities", active_ops)
    else:
        st.error("Unable to fetch engine status")

def display_transaction_chart():
    """Display transaction history chart"""
    st.subheader("📈 Transaction History")
    
    transactions = fetch_recent_transactions(50)
    if transactions and len(transactions) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        if not df.empty and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Create profit over time chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['profit_usd'],
                mode='lines+markers',
                name='Profit per Transaction',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title="Profit per Transaction Over Time",
                xaxis_title="Time",
                yaxis_title="Profit (USD)",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transaction data available for charting")
    else:
        st.info("No recent transactions to display")

def display_recent_transactions():
    """Display recent transactions table"""
    st.subheader("🧾 Recent Transactions")
    
    transactions = fetch_recent_transactions(20)
    if transactions:
        df = pd.DataFrame(transactions)
        
        if not df.empty:
            # Format the data for display
            display_df = df.copy()
            display_df['profit_usd'] = display_df['profit_usd'].apply(lambda x: f"${x:.2f}")
            display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.1%}")
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Select columns to display
            columns_to_show = ['timestamp', 'pair', 'profit_usd', 'confidence', 'status']
            display_df = display_df[columns_to_show]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No transactions to display")
    else:
        st.error("Unable to fetch transactions")

def display_opportunities():
    """Display active opportunities"""
    st.subheader("🎯 Active Opportunities")
    
    opportunities = fetch_active_opportunities()
    if opportunities:
        df = pd.DataFrame(opportunities)
        
        if not df.empty:
            # Format the data for display
            display_df = df.copy()
            display_df['profit_usd'] = display_df['profit_usd'].apply(lambda x: f"${x:.2f}")
            display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.1%}")
            display_df['execution_time_ms'] = display_df['execution_time_ms'].apply(lambda x: f"{x:.1f}ms")
            
            # Select columns to display
            columns_to_show = ['pair', 'profit_usd', 'confidence', 'execution_time_ms', 'status']
            display_df = display_df[columns_to_show]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No active opportunities")
    else:
        st.error("Unable to fetch opportunities")

def display_control_panel():
    """Display engine control panel"""
    st.subheader("🎛️ Engine Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start Engine", type="primary"):
            try:
                base_url = get_api_base_url()
                response = requests.post(f"{base_url}/api/start-engine")
                if response.status_code == 200:
                    st.success("Engine start command sent!")
                else:
                    st.error(f"Failed to start engine: {response.status_code}")
            except Exception as e:
                st.error(f"Error starting engine: {e}")
    
    with col2:
        if st.button("🛑 Stop Engine", type="secondary"):
            try:
                base_url = get_api_base_url()
                response = requests.post(f"{base_url}/api/stop-engine")
                if response.status_code == 200:
                    st.success("Engine stop command sent!")
                else:
                    st.error(f"Failed to stop engine: {response.status_code}")
            except Exception as e:
                st.error(f"Error stopping engine: {e}")
    
    with col3:
        if st.button("🆘 Emergency Stop", type="secondary"):
            try:
                base_url = get_api_base_url()
                response = requests.post(f"{base_url}/api/emergency-stop")
                if response.status_code == 200:
                    st.warning("Emergency stop activated!")
                else:
                    st.error(f"Failed emergency stop: {response.status_code}")
            except Exception as e:
                st.error(f"Error with emergency stop: {e}")

def display_sidebar():
    """Display sidebar with controls"""
    st.sidebar.header("⚡ AINEON Engine")
    st.sidebar.markdown("---")
    
    # Refresh rate control
    refresh_rate = st.sidebar.slider(
        "Auto Refresh Rate (seconds)",
        min_value=5,
        max_value=60,
        value=30,
        step=5
    )
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.experimental_rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### API Information")
    
    api_url = get_api_base_url()
    st.sidebar.markdown(f"**API Base URL:**")
    st.sidebar.code(api_url)
    
    # Environment info
    env = os.getenv("ENVIRONMENT", "development")
    st.sidebar.markdown(f"**Environment:** {env}")
    
    # Last update time
    st.sidebar.markdown(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")

# ============================================================================
# Main Dashboard
# ============================================================================

def main():
    """Main dashboard function"""
    try:
        display_header()
        display_sidebar()
        
        # Create tabs for organization
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", 
            "💰 Profit Metrics", 
            "🧾 Transactions", 
            "🎯 Opportunities"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                display_health_status()
                display_engine_status()
            
            with col2:
                display_control_panel()
        
        with tab2:
            display_profit_metrics()
            display_transaction_chart()
        
        with tab3:
            display_recent_transactions()
        
        with tab4:
            display_opportunities()
        
        # Auto-refresh using JavaScript
        st.markdown(f"""
        <script>
            setTimeout(function(){{
                window.location.reload();
            }}, {refresh_rate * 1000});
        </script>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Dashboard error: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()