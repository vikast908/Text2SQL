from fastapi import Request, HTTPException
from pydantic import ValidationError, BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.settings import settings
from src.utils.logging import get_logger

import json

logger = get_logger(__name__)


class APIException(Exception):
    def __init__(self, message: str, error_code: str | None = None, details: dict | None = None, status_code: int = 500):
        self.message = message.lower()
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "status_code": self.status_code
        }


class ErrorResponseModel(BaseModel):
    """Standardized error response model."""
    success: bool = False
    exception_type: str
    message: str
    error_code: str | None = None
    stack: str | None = None

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions with standardized responses."""
    
    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        # Read and store the request body
        body_bytes = await request.body()
        request.state.body_bytes = body_bytes 
        try:
            request.state.body_json = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except json.JSONDecodeError:
            request.state.body_json = {}

        # Extract email/email_id and store in state
        body_json = request.state.body_json
        email_value = body_json.get("email") or body_json.get("email_id") or ""
        request.state.email_value = email_value

        try:
            return await call_next(request)
        except Exception as e:
            # Initialize stack trace for dev environment
            stack_trace = None
            if settings.app.environment == "dev":
                import traceback
                stack_trace = traceback.format_exc()

            # Map exception types to status codes, log levels, messages, and error codes
            exception_map = {
                APIException: {
                    "status_code": lambda exc: exc.status_code if hasattr(exc, 'status_code') else 400,
                    "log_func": logger.warning,
                    "message": lambda exc: exc.message if hasattr(exc, 'message') else str(exc),
                    "error_code": lambda exc: exc.error_code if hasattr(exc, 'error_code') else "API_ERROR",
                },
                ValidationError: {
                    "status_code": 422,
                    "log_func": logger.warning,
                    "message": lambda exc: "Validation error occurred",
                    "error_code": "VALIDATION_ERROR",
                },
                HTTPException: {
                    "status_code": lambda exc: exc.status_code,
                    "log_func": logger.info,
                    "message": lambda exc: exc.detail,
                    "error_code": None,
                },
            }

            # Find matching exception type or use default
            # Check for exact type match first
            config = exception_map.get(type(e))
            
            # If no exact match, check for isinstance matches (for subclasses)
            if config is None:
                for exc_type, exc_config in exception_map.items():
                    if isinstance(e, exc_type):
                        config = exc_config
                        break
            
            # Use default if still no match
            if config is None:
                config = {
                "status_code": 500,
                "log_func": logger.error,
                "message": lambda exc: "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
            }

            # Log the exception
            config["log_func"](f"{e.__class__.__name__}: {config['message'](e)}", extra={
                "request_path": request.url.path,
                "request_method": request.method,
                "exception_type": e.__class__.__name__,
            })

            # Get status code, message, and error code
            status_code = config["status_code"](e) if callable(config["status_code"]) else config["status_code"]
            message = config["message"](e) if callable(config["message"]) else config["message"]
            error_code = config["error_code"](e) if callable(config["error_code"]) else config["error_code"]
            
            # Build response
            response = ErrorResponseModel(
                exception_type=e.__class__.__name__,
                message=message,
                error_code=error_code,
                stack=stack_trace,
            )

            # Use cached email
            # sdk.log_error(user_id=request.state.email_value, error_details=response.dict())
            return JSONResponse(status_code=status_code, content=response.dict())

# Backward compatibility alias
ExceptionResponseModel = ErrorResponseModel