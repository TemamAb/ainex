import asyncio
import logging

logger = logging.getLogger(__name__)

async def monitor_rpc_health(rpc_manager):
    """Monitor RPC health and send alerts when degradation detected"""
    while True:
        try:
            report = rpc_manager.get_health_report()
            healthy_count = sum(1 for p in report.values() if p["healthy"])
            
            # Critical: Only 1 healthy provider
            if healthy_count < 2:
                await send_alert(
                    "CRITICAL",
                    f"Only {healthy_count} healthy RPC provider(s)!",
                    report
                )
            
            # Warning: Limited redundancy
            elif healthy_count < 3:
                await send_alert(
                    "WARNING",
                    f"Limited RPC redundancy: {healthy_count} healthy providers",
                    report
                )
            
            # Periodic health log
            logger.info(f"RPC Health Report: {healthy_count}/{len(report)} providers healthy")
            for provider_name, health in report.items():
                logger.debug(
                    f"  {provider_name}: {'✅' if health['healthy'] else '❌'} "
                    f"({health['latency_ms']:.1f}ms, "
                    f"success: {health['success_count']}, "
                    f"errors: {health['error_count']})"
                )
            
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"RPC monitoring error: {e}")
            await asyncio.sleep(5)

async def send_alert(level: str, message: str, data: dict = None):
    """Send alert via multiple channels"""
    log_message = f"[{level}] {message}"
    
    if level == "CRITICAL":
        logger.critical(log_message)
    elif level == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)
    
    # TODO: Integrate with external alerting systems
    # - Slack webhook
    # - PagerDuty
    # - Email
    # - Telegram bot
    # - Custom dashboard webhook
    
    if data:
        logger.debug(f"Alert data: {data}")

async def start_rpc_monitoring(rpc_manager):
    """Start the RPC monitoring background task"""
    asyncio.create_task(monitor_rpc_health(rpc_manager))
