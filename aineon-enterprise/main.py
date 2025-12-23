"""
AINEON Flash Loan Engine - Web Service Entry Point
Enterprise-grade blockchain arbitrage engine with FastAPI web interface
Target: github.com/TemamAb/myneon deployment to Render
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import AINEON core components
try:
    from core.blockchain_connector import EthereumMainnetConnector
    from core.live_arbitrage_engine import get_arbitrage_engine
    from core.profit_tracker import get_profit_tracker
    from core.manual_withdrawal import get_manual_withdrawal_system
    from core.auto_withdrawal import get_auto_withdrawal_system
    CORE_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Core components not available: {e}")
    CORE_COMPONENTS_AVAILABLE = False

# Create FastAPI application
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

# Global application state
_app_instance = None
_engine_running = False
_start_time = None

class AINEONWebApp:
    """AINEON Web Application wrapper"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self.load_config()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.blockchain_connector = None
        self.arbitrage_engine = None
        self.profit_tracker = None
        self.manual_withdrawal = None
        self.auto_withdrawal = None
        
        # Application state
        self.running = False
        self.start_time = None
        
        # Setup logging
        self.setup_logging()
        
        self.logger.info("🚀 AINEON Web Application initialized")
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from environment or defaults"""
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
            'auto_withdrawal_enabled': os.getenv('AUTO_WITHDRAWAL_ENABLED', 'true').lower() == 'true',
            'auto_withdrawal_threshold': float(os.getenv('AUTO_WITHDRAWAL_THRESHOLD', '10.0')),
            'auto_withdrawal_percentage': float(os.getenv('AUTO_WITHDRAWAL_PERCENTAGE', '0.8')),
            'auto_check_interval': int(os.getenv('AUTO_CHECK_INTERVAL', '3600')),
            'daily_withdrawal_limit': float(os.getenv('DAILY_WITHDRAWAL_LIMIT', '100.0')),
            
            # System Configuration
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'environment': os.getenv('ENVIRONMENT', 'production')
        }
        
    def setup_logging(self):
        """Setup application logging"""
        log_level = getattr(logging, self.config['log_level'].upper())
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/aineon_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

# Create global app instance
def get_web_app(config: Dict[str, Any] = None) -> AINEONWebApp:
    """Get or create global web application instance"""
    global _app_instance
    if _app_instance is None:
        _app_instance = AINEONWebApp(config)
    return _app_instance

# =============================================================================
# FASTAPI ROUTES
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AINEON Flash Loan Engine - Enterprise Blockchain Arbitrage",
        "version": "1.0.0",
        "status": "running" if _engine_running else "stopped",
        "start_time": _start_time.isoformat() if _start_time else None,
        "environment": os.getenv('ENVIRONMENT', 'production')
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "engine_running": _engine_running,
        "uptime_seconds": (datetime.now() - _start_time).total_seconds() if _start_time else 0
    }

@app.get("/status", tags=["Status"])
async def get_status():
    """Get comprehensive system status"""
    try:
        if not CORE_COMPONENTS_AVAILABLE:
            return {
                "status": "running",
                "mode": "demo",
                "message": "Core components not available, running in demo mode",
                "components": {
                    "blockchain_connector": "unavailable",
                    "arbitrage_engine": "unavailable",
                    "profit_tracker": "unavailable"
                }
            }
        
        web_app = get_web_app()
        status = await web_app.get_system_status()
        return status
        
    except Exception as e:
        logging.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start", tags=["Control"])
async def start_engine():
    """Start the arbitrage engine"""
    global _engine_running, _start_time
    
    if _engine_running:
        return {"message": "Engine already running", "status": "already_running"}
    
    try:
        if not CORE_COMPONENTS_AVAILABLE:
            _engine_running = True
            _start_time = datetime.now()
            return {"message": "Engine started in demo mode", "status": "started"}
        
        web_app = get_web_app()
        await web_app.initialize_components()
        
        # Start engine in background
        asyncio.create_task(web_app.start_profit_generation())
        
        _engine_running = True
        _start_time = datetime.now()
        
        return {"message": "Engine started successfully", "status": "started"}
        
    except Exception as e:
        logging.error(f"Error starting engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop", tags=["Control"])
async def stop_engine():
    """Stop the arbitrage engine"""
    global _engine_running
    
    if not _engine_running:
        return {"message": "Engine already stopped", "status": "already_stopped"}
    
    try:
        _engine_running = False
        
        if CORE_COMPONENTS_AVAILABLE:
            web_app = get_web_app()
            await web_app.shutdown()
        
        return {"message": "Engine stopped successfully", "status": "stopped"}
        
    except Exception as e:
        logging.error(f"Error stopping engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config", tags=["Configuration"])
async def get_config():
    """Get current configuration (non-sensitive)"""
    web_app = get_web_app()
    config = web_app.config.copy()
    
    # Remove sensitive information
    sensitive_keys = ['alchemy_api_key', 'infura_api_key', 'private_key']
    for key in sensitive_keys:
        if key in config:
            config[key] = "***REDACTED***"
    
    return {"configuration": config}

@app.get("/metrics", tags=["Metrics"])
async def get_metrics():
    """Get performance metrics"""
    try:
        if not CORE_COMPONENTS_AVAILABLE:
            return {
                "status": "demo_mode",
                "metrics": {
                    "total_profit_eth": 0.0,
                    "successful_trades": 0,
                    "failed_trades": 0,
                    "success_rate": "0%",
                    "profit_per_hour": 0.0
                }
            }
        
        web_app = get_web_app()
        if web_app.arbitrage_engine:
            stats = web_app.arbitrage_engine.get_performance_stats()
            return {"metrics": stats}
        else:
            return {"metrics": {}}
            
    except Exception as e:
        logging.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    print("AINEON Flash Loan Engine - Web Service")
    print("Enterprise-Grade Blockchain Arbitrage Engine")
    print("Target: github.com/TemamAb/myneon")
    print("=" * 60)
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Get port from environment
    port = int(os.getenv("PORT", 10000))
    
    # Start the web service
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )