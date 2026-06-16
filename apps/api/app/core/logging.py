"""
================================================================================
Logging Configuration for Acadexa API
================================================================================

Standard Python logging setup with JSON format for production.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import json
import logging
import logging.config
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production.
    
    Formats log records as JSON for better log aggregation.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # Handle extra kwargs from logging.debug/error calls
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for development console output.
    
    Adds colors to log levels for better readability.
    """
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{log_message}{self.RESET}"


def setup_logging(environment: str = "development", log_level: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        environment: Environment name (development, staging, production)
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Basic configuration
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Choose formatter based on environment
    if environment == "production":
        # JSON format for production (log aggregation)
        console_handler.setFormatter(JSONFormatter())
    else:
        # Human-readable format with colors for development
        formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
    
    handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Get app logger
    logger = logging.getLogger("acadexa")
    logger.setLevel(level)
    
    # Log startup
    logger.info(f"Logging initialized - Environment: {environment}, Level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Setup logging with default values (called when module is imported)
# This allows from app.core.logging import setup_logging to work
_default_setup_done = False


def ensure_logging_initialized():
    """Ensure logging is initialized with defaults (called on import)."""
    global _default_setup_done
    if not _default_setup_done:
        setup_logging(environment="development", log_level="INFO")
        _default_setup_done = True


# Auto-initialize when module is imported
ensure_logging_initialized()