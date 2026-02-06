"""Custom exceptions for Text2SQL service."""

from typing import Optional, Dict, Any
from src.middleware.exception import APIException
from src.utils.logging import get_logger

logger = get_logger(__name__)


class Text2SQLException(APIException):
    """Base exception for Text2SQL service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        logger.error(
            f"Text2SQLException raised: {message}",
            extra={
                "error_code": error_code,
                "status_code": status_code,
                "details": details,
            }
        )
        super().__init__(
            message=message,
            error_code=error_code,
            details=details or {},
            status_code=status_code,
        )


class LLMClientException(Text2SQLException):
    """Exception raised when LLM client operations fail."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = 502):
        super().__init__(
            message=message,
            error_code="LLM_CLIENT_ERROR",
            details=details,
            status_code=status_code,
        )


class DatabaseConnectionException(Text2SQLException):
    """Exception raised when database connection fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = 503):
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR",
            details=details,
            status_code=status_code,
        )


class SQLExecutionException(Text2SQLException):
    """Exception raised when SQL execution fails."""
    
    def __init__(self, message: str, sql_query: Optional[str] = None, details: Optional[Dict[str, Any]] = None, status_code: int = 400):
        details = details or {}
        if sql_query:
            details["sql_query"] = sql_query
        super().__init__(
            message=message,
            error_code="SQL_EXECUTION_ERROR",
            details=details,
            status_code=status_code,
        )


class MetadataLoadException(Text2SQLException):
    """Exception raised when metadata loading fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, details: Optional[Dict[str, Any]] = None, status_code: int = 500):
        details = details or {}
        if file_path:
            details["file_path"] = file_path
        super().__init__(
            message=message,
            error_code="METADATA_LOAD_ERROR",
            details=details,
            status_code=status_code,
        )


class SQLValidationException(Text2SQLException):
    """Exception raised when SQL validation fails."""
    
    def __init__(self, message: str, sql_query: Optional[str] = None, details: Optional[Dict[str, Any]] = None, status_code: int = 400):
        details = details or {}
        if sql_query:
            details["sql_query"] = sql_query
        super().__init__(
            message=message,
            error_code="SQL_VALIDATION_ERROR",
            details=details,
            status_code=status_code,
        )


class WorkflowException(Text2SQLException):
    """Exception raised when workflow execution fails."""
    
    def __init__(self, message: str, step: Optional[str] = None, details: Optional[Dict[str, Any]] = None, status_code: int = 500):
        details = details or {}
        if step:
            details["workflow_step"] = step
        super().__init__(
            message=message,
            error_code="WORKFLOW_ERROR",
            details=details,
            status_code=status_code,
        )

