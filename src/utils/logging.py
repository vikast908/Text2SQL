import logging
import sys
from typing import Optional, Dict, Any
from fastapi import Request
from src.logging import InterceptHandler
from src.settings import settings
from contextvars import ContextVar
from pydantic import BaseModel

# Context variable to store the current request
REQUEST_CONTEXT: ContextVar[Optional[Request]] = ContextVar('REQUEST_CONTEXT', default=None)

def is_debug_mode() -> bool:
    """Check if the application is running in debug mode."""
    return settings.log_level.upper() == 'DEBUG'

class CustomFormatter(logging.Formatter):
    """Custom formatter to include conversation_id and question_id from request context."""
    
    def format(self, record):
        log_entry = f"{self.formatTime(record)} - {record.name} - {record.levelname} - {record.getMessage()}"
        extra_fields = []
        
        # Extract conversation_id and question_id from request context
        request = REQUEST_CONTEXT.get()
        conversation_id = None
        question_id = None
        
        if request:
            try:
                body = request.state.user_query  # Access UserQuery from request.state
                conversation_id = body.conversation_id
                question_id = body.question_id
            except AttributeError:
                # Fallback to headers if body parsing fails
                conversation_id = request.headers.get("X-Conversation-ID")
                question_id = request.headers.get("X-Question-ID")
            
            if not conversation_id or not question_id:
                # Set flag to indicate missing IDs
                record.missing_ids = True
            else:
                extra_fields.append(f"conversation_id={conversation_id}")
                extra_fields.append(f"question_id={question_id}")
        
        # Add other extra fields
        for key, value in record.__dict__.items():
            if key not in ['conversation_id', 'question_id', 'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info', 'missing_ids']:
                extra_fields.append(f"{key}={value}")
        
        if extra_fields:
            log_entry += f" | {' '.join(extra_fields)}"
        
        return log_entry

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger with structured logging capabilities.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Always set propagate to False to prevent duplicate logs
    # The loguru InterceptHandler will handle all logging
    logger.propagate = False

    root_logger = logging.getLogger()
    intercept_configured = any(
        isinstance(h, InterceptHandler) for h in root_logger.handlers
    )

    if not logger.handlers and not intercept_configured:
        log_level = settings.log_level.upper() if isinstance(settings.log_level, str) else 'INFO'
        log_level = getattr(logging, log_level, logging.INFO)
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = CustomFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if is_debug_mode():
            logger.debug(f"Logger '{name}' configured with level {logging.getLevelName(log_level)}")
    
    return logger
