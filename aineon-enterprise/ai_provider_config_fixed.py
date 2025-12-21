#!/usr/bin/env python3
"""
AI Provider Configuration Fixed for Flash Loan Engines
Reduces context window size to prevent "context window exceeds limit (2013)" errors
"""

from ai_provider_error_handler import AIProviderErrorHandler
import logging

# Configure the AI provider error handler with safer settings
def configure_ai_provider():
    """Configure AI provider with safe context window limits"""
    
    # Initialize the error handler
    handler = AIProviderErrorHandler()
    
    # Set a much lower context window limit to prevent 2013 token errors
    handler.max_context_window = 1500  # Reduced from 8192 to 1500 for safety
    handler.context_warning_threshold = 0.7  # 70% warning threshold
    
    logging.info("AI Provider Error Handler configured with safe context window limits")
    logging.info(f"Context window limit set to: {handler.max_context_window} tokens")
    logging.info(f"Warning threshold: {handler.context_warning_threshold:.0%}")
    
    return handler

# Global configuration
AI_PROVIDER_CONFIG = {
    "max_context_window": 1500,
    "context_warning_threshold": 0.7,
    "cooldown_period": 60,
    "safe_mode": True
}

# Test the configuration
if __name__ == "__main__":
    configure_ai_provider()
    
    # Test error handling with the new configuration
    from ai_provider_error_handler import handle_ai_provider_error
    
    # Simulate the original error that was occurring
    test_error = "Provider error: 400 invalid params, context window exceeds limit (2013)"
    recovery_plan = handle_ai_provider_error(test_error, provider="openai")
    
    print("Recovery Plan for Context Window Error:")
    print(f"- Error Type: {recovery_plan['error_type']}")
    print(f"- Immediate Action: {recovery_plan['immediate_action']}")
    print(f"- Safe Context Available: {'Yes' if recovery_plan['safe_context'] else 'No'}")
    print(f"- Retry Recommended: {recovery_plan['retry_recommended']}")