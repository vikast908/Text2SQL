"""Main Text2SQL service class."""

from typing import Optional, Dict, Any
from src.utils.logging import get_logger

from .workflow_orchestrator import WorkflowOrchestrator
from .models import Text2SQLRequest, Text2SQLResponse
from .exceptions import WorkflowException, Text2SQLException

logger = get_logger(__name__)


class Text2SQLService:
    """Main service class for Text2SQL operations."""
    
    def __init__(
        self,
        workflow_orchestrator: Optional[WorkflowOrchestrator] = None,
    ):
        """
        Initialize Text2SQL service.
        
        Args:
            workflow_orchestrator: Workflow orchestrator instance (creates new one if not provided)
        """
        self.workflow_orchestrator = workflow_orchestrator or WorkflowOrchestrator()
        logger.debug("Text2SQL service initialized")
    
    def process_query(
        self,
        input_text: str,
        max_iterations: int = 3,
        metadata_path: Optional[str] = None,
    ) -> Text2SQLResponse:
        """
        Process a natural language query and return SQL results.
        
        Args:
            input_text: Natural language question/query
            max_iterations: Maximum number of SQL generation iterations
            metadata_path: Optional path to metadata file
            
        Returns:
            Text2SQLResponse with SQL query, data, summary, and followup questions
            
        Raises:
            Text2SQLException: If processing fails
        """
        try:
            if not input_text or not input_text.strip():
                raise ValueError("input_text cannot be empty")
            
            logger.info(f"Processing query: {input_text[:100]}...")
            
            # Create request
            request = Text2SQLRequest(
                input_text=input_text,
                max_iterations=max_iterations,
                metadata_path=metadata_path,
            )
            
            # Convert to initial state
            initial_state = request.to_state()
            
            # Invoke workflow
            final_state = self.workflow_orchestrator.invoke(initial_state)
            
            # Extract results
            sql_query = final_state.get("cleaned_query") or final_state.get("generated_sql_query", "")
            data = final_state.get("data", [])
            summary = final_state.get("summary", "")
            followup_questions = final_state.get("followup_que", [])
            chart = final_state.get("chart", "")
            metadata = final_state.get("metadata", "") 
            
            # Create response
            response = Text2SQLResponse(
                sql_query=sql_query,
                data=data,
                summary=summary,
                followup_questions=followup_questions,
                chart=chart,
                metadata=metadata,
            )
            
            logger.info("Query processed successfully")
            return response
        
        except WorkflowException as e:
            logger.error(f"Workflow error: {e}")
            raise Text2SQLException(
                f"Workflow execution failed: {e.message}",
                error_code=e.error_code,
                details=e.details,
            ) from e
        
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise Text2SQLException(
                f"Invalid input: {str(e)}",
                error_code="VALIDATION_ERROR",
            ) from e
        
        except Exception as e:
            logger.error(f"Unexpected error processing query: {e}")
            raise Text2SQLException(
                f"Unexpected error processing query: {str(e)}",
                error_code="INTERNAL_ERROR",
                details={"error_type": type(e).__name__},
            ) from e
    
    def process_query_dict(
        self,
        input_text: str,
        max_iterations: int = 3,
        metadata_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a natural language query and return results as dictionary.
        
        Args:
            input_text: Natural language question/query
            max_iterations: Maximum number of SQL generation iterations
            metadata_path: Optional path to metadata file
            
        Returns:
            Dictionary with SQL query, data, summary, and followup questions
        """
        response = self.process_query(
            input_text=input_text,
            max_iterations=max_iterations,
            metadata_path=metadata_path,
        )
        return response.to_dict()

