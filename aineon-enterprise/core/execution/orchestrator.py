"""
AINEON Execution Orchestrator
Unified control layer for transaction execution with error handling and recovery.

Integrates:
- Bundler client (Pimlico)
- Transaction executor
- MEV protection
- Error recovery
- Profit tracking
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any
from decimal import Decimal
from datetime import datetime

from core.execution.transaction_executor import (
    TransactionExecutor, ExecutionResult, ExecutionStatus
)
from core.execution.mev_protection import MEVProtectionEngine
from core.execution.error_recovery import ErrorRecoveryEngine, RecoveryStrategy
from core.bundler.pimlico_bundler_client import PimlicoBundlerClient

logger = logging.getLogger(__name__)


class ExecutionOrchestrator:
    """
    Central orchestrator for transaction execution with comprehensive
    error handling, MEV protection, and recovery strategies.
    
    Orchestrates:
    - UserOperation building
    - MEV protection
    - Bundler submission
    - Error detection and recovery
    - Transaction verification
    - Profit recording
    """
    
    def __init__(
        self,
        bundler_client: PimlicoBundlerClient,
        transaction_executor: TransactionExecutor,
        mev_protection: MEVProtectionEngine,
        error_recovery: ErrorRecoveryEngine,
        profit_ledger=None,
    ):
        """
        Initialize execution orchestrator.
        
        Args:
            bundler_client: Pimlico bundler client
            transaction_executor: Transaction executor
            mev_protection: MEV protection engine
            error_recovery: Error recovery engine
            profit_ledger: Profit ledger for recording
        """
        self.bundler = bundler_client
        self.executor = transaction_executor
        self.mev_protection = mev_protection
        self.error_recovery = error_recovery
        self.profit_ledger = profit_ledger
        
        # Execution tracking
        self.executions = []
        self.total_profit = Decimal(0)
        self.total_loss = Decimal(0)
        
        logger.info("Execution orchestrator initialized")
    
    async def execute_opportunity(
        self,
        user_operation: Dict[str, Any],
        opportunity_data: Dict[str, Any],
        entry_point: str,
        max_retry_attempts: int = 3,
    ) -> ExecutionResult:
        """
        Execute opportunity with full error handling and recovery.
        
        Args:
            user_operation: Signed ERC-4337 UserOperation
            opportunity_data: Opportunity details (amounts, strategy, etc.)
            entry_point: EntryPoint contract address
            max_retry_attempts: Maximum retry attempts
            
        Returns:
            ExecutionResult with outcome
        """
        logger.info(f"\n[ORCHESTRATION] Starting opportunity execution")
        logger.info(f"  Strategy: {opportunity_data.get('strategy', 'unknown')}")
        logger.info(f"  Expected Profit: {opportunity_data.get('expected_profit', 'N/A')} ETH")
        
        attempt = 1
        adjusted_user_op = user_operation.copy()
        
        while attempt <= max_retry_attempts:
            try:
                logger.info(f"\n  ─ Attempt {attempt}/{max_retry_attempts}")
                
                # Step 1: Apply MEV protection
                logger.debug("Step 1: Applying MEV protection...")
                success, tx_hash, mev_error = await self.mev_protection.submit_with_mev_protection(
                    transaction_data=adjusted_user_op,
                    expected_output=Decimal(str(opportunity_data.get("expected_profit", 0))),
                )
                
                if not success:
                    logger.error(f"MEV protection failed: {mev_error}")
                    raise Exception(f"MEV protection: {mev_error}")
                
                # Step 2: Execute transaction with bundler
                logger.debug("Step 2: Executing via bundler...")
                result = await self.executor.execute_arbitrage(
                    user_operation=adjusted_user_op,
                    opportunity_data=opportunity_data,
                    entry_point=entry_point,
                )
                
                # Check if successful
                if result.status == ExecutionStatus.PROFIT_CAPTURED:
                    logger.info(f"\n✅ EXECUTION SUCCESSFUL")
                    logger.info(f"  Transaction Hash: {result.transaction_hash}")
                    logger.info(f"  Profit: {result.actual_profit} ETH")
                    logger.info(f"  Gas Used: {result.gas_used}")
                    
                    # Record profit
                    self.total_profit += result.actual_profit
                    self.executions.append(result)
                    
                    # Record in ledger
                    if self.profit_ledger:
                        await self._record_profit(result, opportunity_data)
                    
                    # Signal success to error recovery
                    self.error_recovery.record_success()
                    
                    return result
                
                elif result.status == ExecutionStatus.REVERTED:
                    # Transaction reverted - try recovery
                    logger.warning(f"⚠️  Transaction reverted: {result.error}")
                    raise Exception(f"Revert: {result.error}")
                
                else:
                    # Other error status
                    logger.warning(f"⚠️  Execution status: {result.status.value}")
                    raise Exception(f"Status: {result.status.value}")
            
            except Exception as e:
                logger.error(f"❌ Execution failed (attempt {attempt}): {e}")
                
                # Handle error and determine recovery
                recovery_strategy, adjusted_user_op = await self.error_recovery.handle_error(
                    error=e,
                    transaction_data=adjusted_user_op,
                    attempt_number=attempt,
                )
                
                if recovery_strategy is None or adjusted_user_op is None:
                    logger.error(f"❌ No recovery strategy available - aborting")
                    break
                
                logger.info(f"↻ Recovery strategy: {recovery_strategy.value}")
                
                # Apply backoff before retry
                if attempt < max_retry_attempts:
                    await self.error_recovery.apply_backoff(attempt)
                
                attempt += 1
        
        # All retries exhausted
        logger.error(f"❌ EXECUTION FAILED after {max_retry_attempts} attempts")
        
        return ExecutionResult(
            transaction_hash="",
            status=ExecutionStatus.FAILED,
            block_number=None,
            gas_used=None,
            actual_profit=Decimal(0),
            expected_profit=Decimal(str(opportunity_data.get("expected_profit", 0))),
            profit_captured=False,
            timestamp=datetime.now(),
            error="Max retries exceeded",
        )
    
    async def _record_profit(
        self,
        result: ExecutionResult,
        opportunity_data: Dict[str, Any],
    ):
        """
        Record execution result to profit ledger.
        
        Args:
            result: Execution result
            opportunity_data: Opportunity details
        """
        try:
            if hasattr(self.profit_ledger, 'record_trade'):
                await self.profit_ledger.record_trade(
                    transaction_hash=result.transaction_hash,
                    strategy=opportunity_data.get("strategy", "unknown"),
                    token_in=opportunity_data.get("token_in", "unknown"),
                    token_out=opportunity_data.get("token_out", "unknown"),
                    amount_in=Decimal(str(opportunity_data.get("amount_in", 0))),
                    amount_out=Decimal(str(opportunity_data.get("amount_out", 0))),
                    profit=result.actual_profit,
                    gas_cost=Decimal(result.gas_used or 0) if result.gas_used else Decimal(0),
                    block_number=result.block_number,
                    timestamp=result.timestamp,
                )
                
                logger.debug(f"Profit recorded to ledger")
        
        except Exception as e:
            logger.error(f"Failed to record profit: {e}")
    
    async def execute_batch(
        self,
        opportunities: List[Dict[str, Any]],
        max_concurrent: int = 6,
    ) -> List[ExecutionResult]:
        """
        Execute multiple opportunities concurrently.
        
        Args:
            opportunities: List of opportunities to execute
            max_concurrent: Maximum concurrent executions
            
        Returns:
            List of execution results
        """
        logger.info(f"\n[ORCHESTRATION] Executing batch of {len(opportunities)} opportunities")
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(opp):
            async with semaphore:
                # Build UserOperation (simplified - would use real builder)
                user_op = {
                    "callData": opp.get("calldata", "0x"),
                    "maxFeePerGas": opp.get("max_fee_per_gas", "1000000000"),
                    "maxPriorityFeePerGas": opp.get("max_priority_fee", "100000000"),
                }
                
                return await self.execute_opportunity(
                    user_operation=user_op,
                    opportunity_data=opp,
                    entry_point=opp.get("entry_point", "0x"),
                )
        
        # Execute all opportunities
        tasks = [execute_with_semaphore(opp) for opp in opportunities]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        successful_results = [
            r for r in results
            if isinstance(r, ExecutionResult)
        ]
        
        failed_count = len(results) - len(successful_results)
        profit_sum = sum(r.actual_profit for r in successful_results)
        
        logger.info(f"\n[BATCH COMPLETE]")
        logger.info(f"  Executed: {len(successful_results)}")
        logger.info(f"  Failed: {failed_count}")
        logger.info(f"  Total Profit: {profit_sum} ETH")
        
        return successful_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics."""
        total_executed = len(self.executions)
        successful = sum(1 for e in self.executions if e.profit_captured)
        
        return {
            "total_executed": total_executed,
            "successful": successful,
            "failed": total_executed - successful,
            "success_rate": (successful / total_executed) if total_executed > 0 else 0,
            "total_profit": float(self.total_profit),
            "avg_profit": float(
                self.total_profit / max(1, successful)
            ),
            "bundler_stats": self.bundler.get_stats(),
            "mev_stats": self.mev_protection.get_stats(),
            "error_recovery_stats": self.error_recovery.get_stats(),
        }
    
    def log_stats(self):
        """Log orchestration statistics."""
        stats = self.get_stats()
        logger.info("=" * 70)
        logger.info("EXECUTION ORCHESTRATION STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total Executed: {stats['total_executed']}")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Success Rate: {stats['success_rate']:.2%}")
        logger.info(f"Total Profit: {stats['total_profit']} ETH")
        logger.info(f"Average Profit: {stats['avg_profit']} ETH")
        logger.info("=" * 70)
        
        # Log subsystems
        self.bundler.log_stats()
        self.mev_protection.log_stats()
        self.error_recovery.log_stats()


# Singleton instance
_execution_orchestrator: Optional[ExecutionOrchestrator] = None


def initialize_execution_orchestrator(
    bundler_client: PimlicoBundlerClient,
    transaction_executor: TransactionExecutor,
    mev_protection: MEVProtectionEngine,
    error_recovery: ErrorRecoveryEngine,
    profit_ledger=None,
) -> ExecutionOrchestrator:
    """Initialize execution orchestrator."""
    global _execution_orchestrator
    _execution_orchestrator = ExecutionOrchestrator(
        bundler_client, transaction_executor, mev_protection, error_recovery, profit_ledger
    )
    return _execution_orchestrator


def get_execution_orchestrator() -> ExecutionOrchestrator:
    """Get current execution orchestrator instance."""
    if _execution_orchestrator is None:
        raise RuntimeError("Execution orchestrator not initialized")
    return _execution_orchestrator
