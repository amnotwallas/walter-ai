import os
import sys
import logging
import json
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="N/A")

class JsonFormatter(logging.Formatter):
    """Custom formatter for structured JSON output."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "trace_id": trace_id_var.get()
        }
        # Extract dynamic metrics
        fields = [
            "method", "path", "status_code", "latency_ms", 
            "client_ip", "input_tokens", "output_tokens", "total_tokens"
        ]
        for field in fields:
            if hasattr(record, field):
                log_record[field] = getattr(record, field)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored and concise console output."""
    
    GREY = "\x1b[38;20m"
    BLUE = "\x1b[34;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"
    
    # Static format string to avoid re-creation
    FORMAT = "%(color)s%(trace_prefix)s[%(levelname)s] %(name)s: %(message)s%(reset)s"

    LEVEL_COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: BLUE,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED
    }

    def __init__(self):
        super().__init__(self.FORMAT)

    def format(self, record):
        """Optimized format that injects attributes into the record instead of creating new formatters."""
        record.color = self.LEVEL_COLORS.get(record.levelno, self.GREY)
        record.reset = self.RESET
        trace_id = trace_id_var.get()
        record.trace_prefix = f"[{trace_id}] " if trace_id and trace_id != "N/A" else ""
        return super().format(record)

class ServerLogger:
    """Global logging configuration for the server."""
    _initialized = False
    
    @classmethod
    def setup(cls, log_level=logging.INFO, log_file='server.log'):
        if cls._initialized:
            return
            
        logger = logging.getLogger()
        logger.setLevel(log_level)

        if logger.hasHandlers():
            logger.handlers.clear()

        # Silence noisy external libraries
        noisy_loggers = ["httpx", "urllib3", "requests", "uvicorn.access", "uvicorn.error", "groq", "LiteLLM"]
        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        # Console Handler with ColoredFormatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)

        # File Handler - Disabled on Vercel
        if log_file and os.getenv("VERCEL") != "1":
            try:
                file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
                file_handler.setFormatter(JsonFormatter())
                logger.addHandler(file_handler)
            except Exception as e:
                # Fallback if file system is still read-only for any reason
                logging.warning(f"Could not initialize file logger: {e}")

        cls._initialized = True
        logging.info("Logging system initialized successfully.")

def get_logger(name: str):
    return logging.getLogger(name)
