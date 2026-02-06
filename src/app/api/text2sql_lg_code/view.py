"""API endpoints for Text2SQL LangGraph service."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.utils.logging import get_logger
from src.core.lifetime import get_text2sql_service, get_database_client
from src.app.services.text2sql_lg_service.exceptions import Text2SQLException, DatabaseConnectionException

logger = get_logger(__name__)

router = APIRouter()

# Thread pool for running sync operations
_executor = ThreadPoolExecutor(max_workers=4)


class Text2SQLRequestModel(BaseModel):
    """Request model for Text2SQL API endpoint."""
    
    input_text: str = Field(
        ...,
        description="Natural language question/query to convert to SQL",
        min_length=1,
        max_length=1000,
        example="How do historical sales compare to current year sales for the Beverages category?"
    )
    max_iterations: Optional[int] = Field(
        default=3,
        description="Maximum number of SQL generation iterations",
        ge=1,
        le=10,
        example=3
    )
    metadata_path: Optional[str] = Field(
        default=None,
        description="Optional path to metadata file (defaults to default metadata)",
        example=None
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_text": "How do historical sales compare to current year sales for the Beverages category?",
                "max_iterations": 3,
                "metadata_path": None
            }
        }


class Text2SQLResponseModel(BaseModel):
    """Response model for Text2SQL API endpoint."""
    
    success: bool = Field(..., description="Whether the request was successful")
    sql_query: str = Field(..., description="Generated SQL query")
    data: List[Dict[str, Any]] = Field(..., description="Query execution results")
    summary: str = Field(..., description="Summary of the query results")
    followup_questions: List[str] = Field(..., description="Suggested followup questions")
    chart: Optional[str] = Field(default=None, description="Chart data (placeholder)")
    metadata: Optional[str] = Field(default=None, description="Database metadata used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "sql_query": "SELECT * FROM causal_inference.sales WHERE category = 'Beverages'",
                "data": [{"sales": 1000, "category": "Beverages"}],
                "summary": "The query returned sales data for Beverages category...",
                "followup_questions": [
                    "What are the top performing products?",
                    "How do sales vary by store?",
                    "What is the sales trend over time?"
                ],
                "chart": None,
                "metadata": None
            }
        }


@router.post(
    "/text2sql",
    response_model=Text2SQLResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Convert natural language to SQL and execute query",
    description="""
    This endpoint converts a natural language question into a SQL query,
    validates it, executes it against the database, and returns the results
    along with a summary and followup questions.
    
    The workflow includes:
    1. Loading database metadata
    2. Generating SQL from natural language
    3. Validating the SQL query
    4. Executing the query
    5. Generating a summary of results
    6. Generating followup questions
    """,
    responses={
        200: {
            "description": "Successful response",
            "model": Text2SQLResponseModel
        },
        400: {
            "description": "Bad request - Invalid input or SQL execution error"
        },
        422: {
            "description": "Validation error"
        },
        500: {
            "description": "Internal server error"
        },
        502: {
            "description": "LLM service error"
        },
        503: {
            "description": "Database connection error"
        }
    }
)
async def text2sql(request: Text2SQLRequestModel) -> Text2SQLResponseModel:
    """
    Convert natural language to SQL and execute query.

    Args:
        request: Text2SQL request containing input text and optional parameters

    Returns:
        Text2SQLResponseModel with SQL query, results, summary, and followup questions

    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(
            f"Received Text2SQL request: {request.input_text[:100]}...",
            extra={
                "max_iterations": request.max_iterations,
                "has_metadata_path": request.metadata_path is not None
            }
        )

        # Get singleton service instance
        service = get_text2sql_service()

        # Run sync operation in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            _executor,
            lambda: service.process_query(
                input_text=request.input_text,
                max_iterations=request.max_iterations or 3,
                metadata_path=request.metadata_path,
            )
        )

        # Convert to response model
        result = Text2SQLResponseModel(
            success=True,
            sql_query=response.sql_query,
            data=response.data,
            summary=response.summary,
            followup_questions=response.followup_questions,
            chart=response.chart,
            metadata=response.metadata,
        )
        
        logger.info(
            "Text2SQL request processed successfully",
            extra={
                "sql_query_length": len(response.sql_query),
                "data_rows": len(response.data),
                "followup_questions_count": len(response.followup_questions)
            }
        )
        
        return result
    
    except Text2SQLException as e:
        logger.error(
            f"Text2SQL error: {e.message}",
            extra={
                "error_code": e.error_code,
                "status_code": e.status_code,
                "details": e.details
            }
        )
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error processing Text2SQL request: {e}",
            extra={"error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "An unexpected error occurred while processing the request",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check if the Text2SQL service is available"
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Dictionary with service status including database connectivity
    """
    try:
        logger.debug("Health check requested")

        # Check database connectivity
        db_status = "unknown"
        try:
            db_client = get_database_client()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(_executor, db_client.test_connection)
            db_status = "connected"
        except DatabaseConnectionException as e:
            db_status = f"disconnected: {e.message}"
        except RuntimeError:
            db_status = "not initialized"
        except Exception as e:
            db_status = f"error: {str(e)}"

        # Check service availability
        service_status = "unknown"
        try:
            get_text2sql_service()
            service_status = "available"
        except RuntimeError:
            service_status = "not initialized"

        is_healthy = db_status == "connected" and service_status == "available"

        return {
            "status": "healthy" if is_healthy else "degraded",
            "service": "text2sql_lg_code",
            "version": "1.0",
            "checks": {
                "database": db_status,
                "text2sql_service": service_status,
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Service unavailable", "details": str(e)}
        )
