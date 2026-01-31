"""
Centralized Logging Configuration

Provides consistent logging format and levels across the application.
Includes request ID tracking for distributed tracing.
"""

import json
import logging
import sys
from contextvars import ContextVar, Token
from typing import Optional

# Context variable for request ID tracking (thread-safe)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDFilter(logging.Filter):
    """
    Logging filter that adds request_id to log records.

    Usage in log format: %(request_id)s
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production.

    Properly escapes message content to avoid JSON injection.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, 'request_id', '-'),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def configure_logging(
    level: str = "INFO",
    include_request_id: bool = True,
    json_format: bool = False,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_request_id: Include request ID in log format
        json_format: Use JSON structured logging (for production)
    """
    try:
        # Validate log level
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {level}')

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)

        # Create formatter
        if json_format:
            formatter = JSONFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        elif include_request_id:
            format_str = "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s"
            formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
        else:
            format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")

        console_handler.setFormatter(formatter)

        if include_request_id:
            console_handler.addFilter(RequestIDFilter())

        root_logger.addHandler(console_handler)

        # Reduce noise from third-party libraries
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("playwright").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

        # Log startup
        logging.info("Logging configured: level=%s, request_id=%s, json=%s", level, include_request_id, json_format)

    except Exception as e:
        # Fallback to basic config if custom config fails
        logging.basicConfig(level=logging.INFO)
        logging.error("Failed to configure logging: %s, using defaults", e)


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_ctx.get() or ""


def set_request_id(request_id: str) -> Token[str]:
    """Set request ID in context. Returns token for reset."""
    return request_id_ctx.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    """Reset request ID to previous value using token."""
    request_id_ctx.reset(token)
