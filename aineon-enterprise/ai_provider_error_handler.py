#!/usr/bin/env python3
"""
Enhanced AI Provider Error Handler
Handles "Provider error: 400 invalid params, context window exceeds limit" issues
with intelligent recovery and fallback mechanisms
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Context information for error handling"""
    error_type: str
    error_message: str
    timestamp: datetime
    retry_count: int = 0
    provider: Optional[str] = None
    context_window_size: Optional[int] = None
    resolved: bool = False

@dataclass
class RecoveryStrategy:
    """Recovery strategy configuration"""
    name: str
    max_retries: int
    base_delay: float
    backoff_multiplier: float
    max_delay: float
    fallback_available: bool

class AIProviderErrorHandler:
    """
    Advanced error handler for AI provider issues
    Specifically designed to handle context window limit errors
    """
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies = self._initialize_strategies()
        self.fallback_providers = self._initialize_fallbacks()
        self.context_window_tracker = {}
        self.consecutive_failures = 0
        self.last_successful_call = time.time()
        
        # Configuration
        self.max_context_window = 8192  # Default limit
        self.context_warning_threshold = 0.8  # 80% of limit
        self.cooldown_period = 60  # 1 minute cooldown after errors
        
        logger.info("AI Provider Error Handler initialized")
    
    def _initialize_strategies(self) -> Dict[str, RecoveryStrategy]:
        """Initialize recovery strategies for different error types"""
        return {
            "context_window_exceeded": RecoveryStrategy(
                name="context_window_recovery",
                max_retries=3,
                base_delay=2.0,
                backoff_multiplier=2.0,
                max_delay=30.0,
                fallback_available=True
            ),
            "rate_limit": RecoveryStrategy(
                name="rate_limit_recovery",
                max_retries=5,
                base_delay=5.0,
                backoff_multiplier=1.5,
                max_delay=60.0,
                fallback_available=True
            ),
            "provider_unavailable": RecoveryStrategy(
                name="provider_failover",
                max_retries=2,
                base_delay=1.0,
                backoff_multiplier=3.0,
                max_delay=15.0,
                fallback_available=True
            ),
            "invalid_params": RecoveryStrategy(
                name="parameter_validation",
                max_retries=2,
                base_delay=1.0,
                backoff_multiplier=2.0,
                max_delay=10.0,
                fallback_available=False
            )
        }
    
    def _initialize_fallbacks(self) -> Dict[str, List[str]]:
        """Initialize fallback provider chains"""
        return {
            "openai": ["anthropic", "google", "local"],
            "anthropic": ["openai", "google", "local"],
            "google": ["openai", "anthropic", "local"],
            "local": ["openai", "anthropic", "google"]
        }
    
    def detect_error_type(self, error_message: str) -> str:
        """Detect the type of error from the message"""
        error_lower = error_message.lower()
        
        if "context window" in error_lower or "context window exceeds" in error_lower:
            return "context_window_exceeded"
        elif "rate limit" in error_lower or "too many requests" in error_lower:
            return "rate_limit"
        elif "provider" in error_lower and "unavailable" in error_lower:
            return "provider_unavailable"
        elif "invalid params" in error_lower or "400" in error_lower:
            return "invalid_params"
        else:
            return "unknown"
    
    def extract_context_window_size(self, error_message: str) -> Optional[int]:
        """Extract context window size from error message"""
        try:
            import re
            # Look for numbers in the error message
            numbers = re.findall(r'\d+', error_message)
            for num in numbers:
                size = int(num)
                if size > 1000:  # Reasonable context window size
                    return size
            return None
        except:
            return None
    
    def calculate_optimal_context_size(self, provider: str, current_size: int) -> int:
        """Calculate optimal context size to avoid limit errors"""
        # Use 75% of the current limit as safety margin
        optimal_size = int(current_size * 0.75)
        
        # Track usage patterns
        if provider not in self.context_window_tracker:
            self.context_window_tracker[provider] = []
        
        self.context_window_tracker[provider].append({
            "timestamp": time.time(),
            "size": current_size,
            "success": True
        })
        
        # Keep only recent entries
        cutoff_time = time.time() - 3600  # 1 hour
        self.context_window_tracker[provider] = [
            entry for entry in self.context_window_tracker[provider]
            if entry["timestamp"] > cutoff_time
        ]
        
        return optimal_size
    
    def should_attempt_recovery(self, error_context: ErrorContext) -> bool:
        """Determine if recovery should be attempted"""
        # Check cooldown period
        if time.time() - self.last_successful_call < self.cooldown_period:
            return False
        
        # Check retry limit
        strategy = self.recovery_strategies.get(error_context.error_type)
        if not strategy or error_context.retry_count >= strategy.max_retries:
            return False
        
        # Check for too many consecutive failures
        if self.consecutive_failures >= 10:
            logger.warning("Too many consecutive failures, entering cooldown")
            return False
        
        return True
    
    def get_recovery_delay(self, error_context: ErrorContext) -> float:
        """Calculate delay before next retry"""
        strategy = self.recovery_strategies.get(error_context.error_type)
        if not strategy:
            return 5.0
        
        # Exponential backoff
        delay = strategy.base_delay * (strategy.backoff_multiplier ** error_context.retry_count)
        return min(delay, strategy.max_delay)
    
    def get_fallback_provider(self, current_provider: str) -> Optional[str]:
        """Get next fallback provider in the chain"""
        fallbacks = self.fallback_providers.get(current_provider, [])
        
        for fallback in fallbacks:
            if self._is_provider_healthy(fallback):
                return fallback
        
        return None
    
    def _is_provider_healthy(self, provider: str) -> bool:
        """Check if a provider is currently healthy"""
        # Simple health check - in production this would be more sophisticated
        provider_errors = [
            error for error in self.error_history[-50:]  # Last 50 errors
            if error.provider == provider and 
            (time.time() - error.timestamp.timestamp()) < 300  # Last 5 minutes
        ]
        
        # If provider has more than 5 errors in 5 minutes, mark as unhealthy
        return len(provider_errors) <= 5
    
    def create_safe_context(self, prompt: str, max_tokens: int = None) -> str:
        """Create a safe context that won't exceed limits"""
        if not max_tokens:
            max_tokens = self.max_context_window
        
        # Estimate tokens (rough approximation)
        estimated_tokens = len(prompt.split()) * 1.3  # Rough token estimation
        
        if estimated_tokens > max_tokens * 0.8:  # 80% threshold
            # Truncate the prompt to fit
            target_length = int(max_tokens * 0.7)  # Use 70% for safety
            words = prompt.split()
            
            if len(words) > target_length:
                # Keep the beginning and end, truncate middle
                keep_start = target_length // 2
                keep_end = target_length - keep_start
                
                truncated = (
                    " ".join(words[:keep_start]) +
                    " ... [content truncated] ... " +
                    " ".join(words[-keep_end:])
                )
                return truncated
        
        return prompt
    
    def handle_error(self, error_message: str, provider: str = None, prompt: str = None) -> Dict[str, Any]:
        """
        Main error handling function
        Returns recovery plan and suggestions
        """
        error_type = self.detect_error_type(error_message)
        context_size = self.extract_context_window_size(error_message)
        
        error_context = ErrorContext(
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now(),
            provider=provider,
            context_window_size=context_size
        )
        
        self.error_history.append(error_context)
        self.consecutive_failures += 1
        
        logger.error(f"AI Provider Error Detected: {error_type} - {error_message}")
        
        # Generate recovery plan
        recovery_plan = {
            "error_type": error_type,
            "immediate_action": self._get_immediate_action(error_type),
            "recovery_suggestions": self._get_recovery_suggestions(error_type, context_size),
            "fallback_provider": self.get_fallback_provider(provider) if provider else None,
            "safe_context": self._get_safe_context_suggestion(prompt) if prompt else None,
            "retry_recommended": self.should_attempt_recovery(error_context),
            "retry_delay": self.get_recovery_delay(error_context) if self.should_attempt_recovery(error_context) else None
        }
        
        # Log recovery plan
        logger.info(f"Recovery Plan Generated: {json.dumps(recovery_plan, indent=2, default=str)}")
        
        return recovery_plan
    
    def _get_immediate_action(self, error_type: str) -> str:
        """Get immediate action for the error type"""
        actions = {
            "context_window_exceeded": "Reduce prompt length or split into smaller chunks",
            "rate_limit": "Wait for rate limit to reset or reduce request frequency",
            "provider_unavailable": "Switch to fallback provider immediately",
            "invalid_params": "Validate and fix request parameters",
            "unknown": "Check provider status and retry with reduced load"
        }
        return actions.get(error_type, "Review error details and adjust request")
    
    def _get_recovery_suggestions(self, error_type: str, context_size: Optional[int]) -> List[str]:
        """Get detailed recovery suggestions"""
        suggestions = []
        
        if error_type == "context_window_exceeded":
            suggestions.extend([
                "Split large prompts into smaller chunks",
                "Use context summarization to reduce token count",
                "Implement streaming responses to manage context better",
                "Consider using more efficient prompt engineering techniques"
            ])
            
            if context_size:
                optimal_size = self.calculate_optimal_context_size("default", context_size)
                suggestions.append(f"Limit prompts to ~{optimal_size} tokens for safety")
        
        elif error_type == "rate_limit":
            suggestions.extend([
                "Implement exponential backoff retry logic",
                "Add request queuing to control throughput",
                "Monitor rate limit headers from provider",
                "Consider upgrading to higher tier for increased limits"
            ])
        
        elif error_type == "provider_unavailable":
            suggestions.extend([
                "Switch to backup provider immediately",
                "Implement health checking for providers",
                "Set up automatic failover mechanisms",
                "Monitor provider status externally"
            ])
        
        return suggestions
    
    def _get_safe_context_suggestion(self, prompt: str) -> Optional[str]:
        """Get a safe version of the prompt if provided"""
        if not prompt:
            return None
        
        return self.create_safe_context(prompt, self.max_context_window)
    
    def record_success(self, provider: str = None):
        """Record a successful operation"""
        self.last_successful_call = time.time()
        self.consecutive_failures = max(0, self.consecutive_failures - 1)
        
        logger.info(f"AI Provider operation successful for provider: {provider}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and trends"""
        now = time.time()
        recent_errors = [
            error for error in self.error_history
            if (now - error.timestamp.timestamp()) < 3600  # Last hour
        ]
        
        error_types = {}
        for error in recent_errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors_1h": len(recent_errors),
            "error_types_1h": error_types,
            "consecutive_failures": self.consecutive_failures,
            "last_success": self.last_successful_call,
            "providers_healthy": {
                provider: self._is_provider_healthy(provider)
                for provider in self.fallback_providers.keys()
            }
        }

# Global instance for easy access
ai_error_handler = AIProviderErrorHandler()

def handle_ai_provider_error(error_message: str, provider: str = None, prompt: str = None) -> Dict[str, Any]:
    """Convenience function to handle AI provider errors"""
    return ai_error_handler.handle_error(error_message, provider, prompt)

def safe_ai_call(func: Callable, *args, provider: str = None, **kwargs) -> Any:
    """
    Wrapper for AI calls with automatic error handling
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            result = func(*args, **kwargs)
            ai_error_handler.record_success(provider)
            return result
            
        except Exception as e:
            error_message = str(e)
            recovery_plan = handle_ai_provider_error(error_message, provider)
            
            if not recovery_plan["retry_recommended"]:
                logger.error(f"AI call failed permanently: {error_message}")
                raise e
            
            retry_count += 1
            delay = recovery_plan["retry_delay"] or (2 ** retry_count)
            
            logger.warning(f"AI call failed, retrying in {delay}s (attempt {retry_count}/{max_retries})")
            time.sleep(delay)
    
    logger.error(f"AI call failed after {max_retries} retries")
    raise Exception(f"AI call failed after {max_retries} retries: {error_message}")

if __name__ == "__main__":
    # Test the error handler
    print("Testing AI Provider Error Handler...")
    
    # Test context window error
    test_error = "Provider error: 400 invalid params, context window exceeds limit (8192)"
    recovery_plan = handle_ai_provider_error(test_error, provider="openai")
    print(f"Recovery Plan: {json.dumps(recovery_plan, indent=2)}")
    
    # Test safe context creation
    long_prompt = "This is a very long prompt " * 1000
    safe_prompt = ai_error_handler.create_safe_context(long_prompt)
    print(f"Original length: {len(long_prompt)}, Safe length: {len(safe_prompt)}")
    
    # Get statistics
    stats = ai_error_handler.get_error_statistics()
    print(f"Error Statistics: {json.dumps(stats, indent=2)}")