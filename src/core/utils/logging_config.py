"""Logging Configuration - Centralized logging setup for the application"""

import json
import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request_id if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class RequestIdFilter(logging.Filter):
    """Filter to add request_id to log records."""

    def __init__(self, request_id: str = None):
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to log record."""
        record.request_id = self.request_id
        return True


def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    enable_console: bool = False,
    enable_file: bool = False,
    enable_audit: bool = False,
) -> None:
    """Setup comprehensive logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_audit: Enable audit logging
    """

    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Define loggers
    loggers = {
        "": {"level": log_level, "handlers": [], "propagate": False},  # Root logger
        "apps": {  # Application modules
            "level": log_level,
            "handlers": [],
            "propagate": False,
        },
        "apps.document_intake": {  # Document intake module
            "level": log_level,
            "handlers": [],
            "propagate": False,
        },
        "apps.ai_extraction": {  # AI extraction module
            "level": log_level,
            "handlers": [],
            "propagate": False,
        },
        "apps.ai_extraction.services": {  # AI extraction services
            "level": log_level,
            "handlers": [],
            "propagate": False,
        },
        "core": {  # Core modules
            "level": log_level,
            "handlers": [],
            "propagate": False,
        },
    }

    # Define handlers
    handlers = {}

    if enable_console:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "structured",
            "stream": "ext://sys.stdout",
        }

    if enable_file and log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "structured",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }

    if enable_audit and log_file:
        audit_log_file = str(Path(log_file).parent / "audit.log")
        handlers["audit"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "audit",
            "filename": audit_log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
        }

    # Define formatters
    formatters = {
        "structured": {"()": "core.utils.logging_config.StructuredFormatter"},
        "audit": {"()": "core.utils.logging_config.StructuredFormatter"},
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }

    # Add handlers to loggers
    for logger_name in loggers:
        if enable_console:
            loggers[logger_name]["handlers"].append("console")
        if enable_file and log_file:
            loggers[logger_name]["handlers"].append("file")
        if enable_audit and "audit" in handlers:
            loggers[logger_name]["handlers"].append("audit")

    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": loggers,
    }

    logging.config.dictConfig(logging_config)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging system initialized",
        extra={
            "extra_fields": {
                "log_level": log_level,
                "console_enabled": enable_console,
                "file_enabled": enable_file,
                "audit_enabled": enable_audit,
                "log_file": log_file,
            }
        },
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_with_request_id(
    logger: logging.Logger, request_id: str, level: str, message: str, **kwargs
) -> None:
    """Log a message with request ID context.

    Args:
        logger: Logger instance
        request_id: Request correlation ID
        level: Log level
        message: Log message
        **kwargs: Additional fields to include in log
    """
    extra_fields = {"request_id": request_id}
    if kwargs:
        extra_fields.update(kwargs)

    log_record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        message,
        (),
        None,
        func="log_with_request_id",
    )
    log_record.extra_fields = extra_fields
    logger.handle(log_record)


def log_audit_event(
    logger: logging.Logger,
    event_type: str,
    request_id: str,
    user_id: str = None,
    resource: str = None,
    action: str = None,
    status: str = None,
    details: Dict[str, Any] = None,
) -> None:
    """Log an audit event with structured data.

    Args:
        logger: Logger instance
        event_type: Type of audit event
        request_id: Request correlation ID
        user_id: User ID (optional)
        resource: Resource being accessed (optional)
        action: Action performed (optional)
        status: Status of the action (optional)
        details: Additional details (optional)
    """
    audit_data = {
        "event_type": event_type,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if user_id:
        audit_data["user_id"] = user_id
    if resource:
        audit_data["resource"] = resource
    if action:
        audit_data["action"] = action
    if status:
        audit_data["status"] = status
    if details:
        audit_data["details"] = details

    log_record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"AUDIT: {event_type}",
        (),
        None,
        func="log_audit_event",
    )
    log_record.extra_fields = audit_data
    logger.handle(log_record)


def log_performance_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: str,
    request_id: str = None,
    tags: Dict[str, str] = None,
) -> None:
    """Log a performance metric.

    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        request_id: Request correlation ID (optional)
        tags: Additional tags (optional)
    """
    metric_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if request_id:
        metric_data["request_id"] = request_id
    if tags:
        metric_data["tags"] = tags

    log_record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"METRIC: {metric_name} = {value} {unit}",
        (),
        None,
        func="log_performance_metric",
    )
    log_record.extra_fields = metric_data
    logger.handle(log_record)


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    request_id: str = None,
    context: Dict[str, Any] = None,
    level: str = "ERROR",
) -> None:
    """Log an error with context information.

    Args:
        logger: Logger instance
        error: Exception to log
        request_id: Request correlation ID (optional)
        context: Additional context (optional)
        level: Log level (default: ERROR)
    """
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if request_id:
        error_data["request_id"] = request_id
    if context:
        error_data["context"] = context

    log_record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        f"ERROR: {type(error).__name__}: {str(error)}",
        (),
        error,
        func="log_error_with_context",
    )
    log_record.extra_fields = error_data
    logger.handle(log_record)


# Initialize default logging configuration
def init_default_logging() -> None:
    """Initialize default logging configuration."""
    setup_logging(
        log_level="INFO",
        log_file="logs/app.log",
        enable_console=False,
        enable_file=False,
        enable_audit=False,
    )
