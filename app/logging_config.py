"""Structured logging configuration for the Library application.

PG-004: Monitoring - Structured logging implementation
"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
            
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # Add any extra fields from record
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith("_") and key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "message",
                "module", "msecs", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            ):
                log_data[key] = value
                
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output."""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        # Build the log message
        parts = [
            f"{color}[{timestamp}]{reset}",
            f"{color}[{record.levelname:8}]{reset}",
            f"[{record.name}]",
            record.getMessage(),
        ]
        
        # Add extra context if present
        extras = []
        if hasattr(record, "request_id"):
            extras.append(f"req={record.request_id}")
        if hasattr(record, "duration_ms"):
            extras.append(f"{record.duration_ms}ms")
        if hasattr(record, "endpoint"):
            extras.append(f"{record.method} {record.endpoint}")
        if hasattr(record, "status_code"):
            extras.append(f"status={record.status_code}")
            
        if extras:
            parts.append(f"({', '.join(extras)})")
            
        # Add exception info if present
        if record.exc_info:
            parts.append(f"\n{self.formatException(record.exc_info)}")
            
        return " ".join(parts)


def setup_logging(
    level: str = "INFO",
    format_type: str = "console",
    log_file: str | None = None,
) -> None:
    """Configure application logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 'console' for human-readable, 'json' for structured
        log_file: Optional file path for file logging
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = ConsoleFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding structured context to logs."""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.handler = None
        
    def __enter__(self):
        class ContextFilter(logging.Filter):
            def filter(self, record):
                for key, value in self.context.items():
                    setattr(record, key, value)
                return True
                
        self.handler = ContextFilter()
        self.logger.addFilter(self.handler)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            self.logger.removeFilter(self.handler)
