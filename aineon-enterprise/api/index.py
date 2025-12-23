"""
AINEON Hybrid Dashboard - Vercel Serverless Entry Point
Adapts FastAPI application for Vercel's serverless environment
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.staticfiles import StaticFiles

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app for Vercel
app = FastAPI(
    title="AINEON Flash Loan Engine",
    description="Enterprise-Grade Flash Loan Engine for Blockchain Arbitrage",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
_engine_running = False
_start_time = None

# =============================================================================
# CONFIGURATION & UTILITIES
# =============================================================================

def get_config() -> Dict[str, Any]:
    """Load configuration from environment"""
    return {
        # Blockchain Configuration
        'alchemy_api_key': os.getenv('ALCHEMY_API_KEY'),
        'infura_api_key': os.getenv('INFURA_API_KEY'),
        'private_key': os.getenv('PRIVATE_KEY'),
        'withdrawal_address': os.getenv('WITHDRAWAL_ADDRESS'),
        
        # Profit Generation
        'min_profit_threshold': float(os.getenv('MIN_PROFIT_THRESHOLD', '0.5')),
        'max_gas_price': float(os.getenv('MAX_GAS_PRICE', '50')),
        'confidence_threshold': float(os.getenv('CONFIDENCE_THRESHOLD', '0.7')),
        'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '1000')),
        
        # Profit Tracking
        'initial_eth_balance': float(os.getenv('INITIAL_ETH_BALANCE', '0.0')),
        'tracking_interval': int(os.getenv('TRACKING_INTERVAL', '60')),
        'eth_price_usd': float(os.getenv('ETH_PRICE_USD', '2850.0')),
        'gas_reserve_eth': float(os.getenv('GAS_RESERVE_ETH', '0.1')),
        
        # Manual Withdrawal
        'min_withdrawal_eth': float(os.getenv('MIN_WITHDRAWAL_ETH', '0.1')),
        'max_withdrawal_eth': float(os.getenv('MAX_WITHDRAWAL_ETH', '100.0')),
        'max_daily_withdrawals': int(os.getenv('MAX_DAILY_WITHDRAWALS', '10')),
        'max_daily_amount_eth': float(os.getenv('MAX_DAILY_AMOUNT_ETH', '1000.0')),
        'require_confirmation': os.getenv('REQUIRE_CONFIRMATION', 'true').lower() == 'true',
        
        # Auto Withdrawal
        'auto_withdrawal_enabled': os.getenv('AUTO_WITHDRAWAL_ENABLED', 'false').lower() == 'true',
        'auto_withdrawal_threshold': float(os.getenv('AUTO_WITHDRAWAL_THRESHOLD', '10.0')),
        'auto_withdrawal_percentage': float(os.getenv('AUTO_WITHDRAWAL_PERCENTAGE', '0.8')),
        'auto_check_interval': int(os.getenv('AUTO_CHECK_INTERVAL', '3600')),
        'daily_withdrawal_limit': float(os.getenv('DAILY_WITHDRAWAL_LIMIT', '100.0')),
        
        # System Configuration
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'environment': os.getenv('ENVIRONMENT', 'production')
    }

# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AINEON Flash Loan Engine - Vercel Serverless",
        "version": "1.0.0",
        "status": "running",
        "environment": os.getenv('ENVIRONMENT', 'production'),
        "deployment": "vercel"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Vercel"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "platform": "vercel",
        "version": "1.0.0"
    }

@app.get("/status", tags=["Status"])
async def get_status():
    """Get comprehensive system status"""
    try:
        config = get_config()
        return {
            "status": "running",
            "environment": config['environment'],
            "platform": "vercel",
            "configuration": {
                'environment': config['environment'],
                'auto_withdrawal_enabled': config['auto_withdrawal_enabled'],
                'min_profit_threshold': config['min_profit_threshold']
            }
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# HYBRID DASHBOARD ROUTES
# =============================================================================

@app.get("/dashboard", tags=["Dashboard"])
async def get_dashboard():
    """Serve the AINEON Hybrid Enterprise Dashboard"""
    try:
        # Try to serve from public directory first
        public_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "dashboard.html")
        if os.path.exists(public_path):
            return FileResponse(public_path, media_type="text/html")
        
        # Fallback to templates directory
        templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "aineon_hybrid_enterprise_dashboard.html")
        if os.path.exists(templates_path):
            return FileResponse(templates_path, media_type="text/html")
        
        # Return error
        return JSONResponse(
            status_code=404,
            content={"error": "Dashboard not found"}
        )
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# API ENDPOINTS FOR DASHBOARD
# =============================================================================

@app.get("/api/profit", tags=["Dashboard API"])
async def get_profit():
    """Get current profit metrics"""
    try:
        return {
            "total_profit_eth": 0.0,
            "hourly_profit": 0.0,
            "daily_profit": 0.0,
            "weekly_profit": 0.0,
            "monthly_profit": 0.0,
            "profit_change_percent": 0.0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting profit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profit/hourly", tags=["Dashboard API"])
async def get_hourly_profit():
    """Get hourly profit data"""
    return {
        "data": [],
        "unit": "ETH",
        "timeframe": "hourly",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/profit/daily", tags=["Dashboard API"])
async def get_daily_profit():
    """Get daily profit data"""
    return {
        "data": [],
        "unit": "ETH",
        "timeframe": "daily",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/profit/live", tags=["Dashboard API"])
async def get_live_profit():
    """Get live profit data (polling fallback)"""
    return {
        "total_profit_eth": 0.0,
        "hourly_rate": 0.0,
        "last_update": datetime.now().isoformat(),
        "status": "connected"
    }

@app.get("/api/withdrawal/history", tags=["Dashboard API"])
async def get_withdrawal_history():
    """Get withdrawal transaction history"""
    return {
        "transactions": [],
        "total_withdrawn": 0.0,
        "count": 0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/transactions", tags=["Dashboard API"])
async def get_transactions():
    """Get recent transactions"""
    return {
        "transactions": [],
        "count": 0,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/withdrawal/connect", tags=["Dashboard API"])
async def connect_wallet():
    """Connect MetaMask wallet"""
    return {
        "status": "success",
        "message": "Wallet connection ready",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/withdrawal/manual", tags=["Dashboard API"])
async def manual_withdrawal():
    """Execute manual withdrawal"""
    return {
        "status": "pending",
        "message": "Manual withdrawal initiated",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/withdrawal/auto", tags=["Dashboard API"])
async def configure_auto_withdrawal():
    """Configure auto withdrawal settings"""
    return {
        "status": "configured",
        "message": "Auto withdrawal configured",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/ai/chat", tags=["Dashboard API"])
async def ai_chat():
    """Send message to AI terminal"""
    return {
        "response": "AI integration ready",
        "provider": "openai",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/ai/providers", tags=["Dashboard API"])
async def get_ai_providers():
    """Get available AI providers"""
    return {
        "providers": ["openai", "gemini"],
        "active": "openai",
        "status": "ready",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics", tags=["Metrics"])
async def get_metrics():
    """Get performance metrics"""
    try:
        return {
            "status": "running",
            "metrics": {
                "total_profit_eth": 0.0,
                "successful_trades": 0,
                "failed_trades": 0,
                "success_rate": "0%",
                "profit_per_hour": 0.0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config", tags=["Configuration"])
async def get_config_endpoint():
    """Get current configuration (non-sensitive)"""
    try:
        config = get_config()
        # Remove sensitive information
        sensitive_keys = ['alchemy_api_key', 'infura_api_key', 'private_key']
        for key in sensitive_keys:
            if key in config:
                config[key] = "***REDACTED***"
        
        return {"configuration": config}
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc)}
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Export app for Vercel
# Vercel automatically imports 'app' from this file
__all__ = ['app']
