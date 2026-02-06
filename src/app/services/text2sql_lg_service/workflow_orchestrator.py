"""Workflow orchestrator for LangGraph text2sql workflow."""

from typing import Literal, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from src.utils.logging import get_logger
from .models import Text2SQLState
from .metadata_loader import MetadataLoader
from .sql_generator import SQLGenerator
from .sql_validator import SQLValidator
from .sql_executor import SQLExecutor
from .summary_generator import SummaryGenerator
from .followup_generator import FollowupQuestionGenerator
from .exceptions import WorkflowException

logger = get_logger(__name__)


class WorkflowOrchestrator:
    """Orchestrator for Text2SQL LangGraph workflow."""
    
    def __init__(
        self,
        metadata_loader: Optional[MetadataLoader] = None,
        sql_generator: Optional[SQLGenerator] = None,
        sql_validator: Optional[SQLValidator] = None,
        sql_executor: Optional[SQLExecutor] = None,
        summary_generator: Optional[SummaryGenerator] = None,
        followup_generator: Optional[FollowupQuestionGenerator] = None,
    ):
        """
        Initialize workflow orchestrator.

        Args:
            metadata_loader: Metadata loader instance (creates new one if not provided)
            sql_generator: SQL generator instance (creates new one if not provided)
            sql_validator: SQL validator instance (creates new one if not provided)
            sql_executor: SQL executor instance (creates new one if not provided)
            summary_generator: Summary generator instance (creates new one if not provided)
            followup_generator: Followup question generator instance (creates new one if not provided)
        """
        self.metadata_loader = metadata_loader or MetadataLoader()
        self.sql_generator = sql_generator or SQLGenerator()
        self.sql_validator = sql_validator or SQLValidator()
        self.sql_executor = sql_executor or SQLExecutor()
        self.summary_generator = summary_generator or SummaryGenerator()
        self.followup_generator = followup_generator or FollowupQuestionGenerator()
        
        self._workflow = None
        self._build_workflow()
        logger.debug("Workflow orchestrator initialized")
    
    def _get_metadata(self, state: Text2SQLState) -> Dict[str, Any]:
        """Node function to get metadata."""
        try:
            logger.debug("Getting metadata")
            metadata = self.metadata_loader.load_metadata()
            return {"metadata": metadata}
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            raise WorkflowException(
                f"Failed to load metadata: {str(e)}",
                step="get_metadata",
            ) from e
    
    def _generate_sql(self, state: Text2SQLState) -> Dict[str, Any]:
        """Node function to generate SQL."""
        try:
            logger.debug("Generating SQL")
            return self.sql_generator.generate_sql(state)
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise WorkflowException(
                f"Failed to generate SQL: {str(e)}",
                step="generate_sql",
            ) from e
    
    def _validate_sql_query(self, state: Text2SQLState) -> Dict[str, Any]:
        """Node function to validate SQL."""
        try:
            logger.debug("Validating SQL query")
            result = self.sql_validator.validate_sql_query(state)
            # Increment retry count
            retry_count = state.get("retry_count", 0) + 1
            result["retry_count"] = retry_count
            return result
        except Exception as e:
            logger.error(f"Error validating SQL: {e}")
            raise WorkflowException(
                f"Failed to validate SQL: {str(e)}",
                step="validate_sql_query",
            ) from e
    
    def _execute_sql(self, state: Text2SQLState) -> Dict[str, Any]:
        """Node function to execute SQL."""
        try:
            logger.debug("Executing SQL query")
            return self.sql_executor.execute_sql(state)
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            raise WorkflowException(
                f"Failed to execute SQL: {str(e)}",
                step="execute_sql",
            ) from e
    
    def _generate_summary(self, state: Text2SQLState) -> Dict[str, Any]:
        """Node function to generate summary."""
        try:
            logger.debug("Generating summary")
            return self.summary_generator.generate_summary(state)
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise WorkflowException(
                f"Failed to generate summary: {str(e)}",
                step="generate_summary",
            ) from e
    
    def _generate_chart(self, state: Text2SQLState) -> Dict[str, Any]:
        """Node function to generate chart (placeholder)."""
        try:
            logger.debug("Generating chart (placeholder)")
            # Placeholder for chart generation
            return {"chart": ""}
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            raise WorkflowException(
                f"Failed to generate chart: {str(e)}",
                step="generate_chart",
            ) from e
    
    def _get_followup_que(self, state: Text2SQLState) -> Dict[str, Any]:
        """Node function to get followup questions."""
        try:
            logger.debug("Generating followup questions")
            return self.followup_generator.generate_followup_questions(state)
        except Exception as e:
            logger.error(f"Error generating followup questions: {e}")
            raise WorkflowException(
                f"Failed to generate followup questions: {str(e)}",
                step="get_followup_que",
            ) from e
    
    def _check_condition(self, state: Text2SQLState) -> Literal["execute_sql", "generate_sql", "handle_unanswerable"]:
        """
        Conditional edge function to check if SQL is valid.

        Args:
            state: Current workflow state

        Returns:
            Next node name based on validation result
        """
        # Check if query is unanswerable
        if state.get("is_unanswerable", False):
            logger.info("Query marked as unanswerable, skipping SQL execution")
            return "handle_unanswerable"

        is_valid = state.get("is_valid_sql", False)
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_iterations", 3)

        logger.debug(f"SQL validation check: {'VALID' if is_valid else 'INVALID'} (retry {retry_count}/{max_retries})")

        # Always proceed to execute after max retries, even if invalid
        if is_valid or retry_count >= max_retries:
            if not is_valid:
                logger.warning(f"Proceeding with potentially invalid SQL after {retry_count} retries")
            return "execute_sql"
        else:
            return "generate_sql"

    def _handle_unanswerable(self, state: Text2SQLState) -> Dict[str, Any]:
        """Node function to handle unanswerable queries."""
        reason = state.get("unanswerable_reason", "The requested data is not available in the database.")
        logger.info(f"Handling unanswerable query: {reason}")
        return {
            "data": [],
            "summary": f"I cannot answer this question because: {reason}\n\nThe database contains information about: sales, products, stores, inventory, forecasts, promotions, and pricing. Please try asking about one of these topics.",
        }
    
    def _build_workflow(self) -> None:
        """Build the LangGraph workflow."""
        try:
            graph = StateGraph(Text2SQLState)

            # Add nodes
            graph.add_node("get_metadata", self._get_metadata)
            graph.add_node("generate_sql", self._generate_sql)
            graph.add_node("validate_sql_query", self._validate_sql_query)
            graph.add_node("execute_sql", self._execute_sql)
            graph.add_node("generate_summary", self._generate_summary)
            graph.add_node("generate_chart", self._generate_chart)
            graph.add_node("get_followup_que", self._get_followup_que)
            graph.add_node("handle_unanswerable", self._handle_unanswerable)

            # Add edges
            graph.add_edge(START, "get_metadata")
            graph.add_edge("get_metadata", "get_followup_que")
            graph.add_edge("get_metadata", "generate_sql")
            graph.add_edge("generate_sql", "validate_sql_query")
            graph.add_conditional_edges("validate_sql_query", self._check_condition)
            graph.add_edge("execute_sql", "generate_chart")
            graph.add_edge("execute_sql", "generate_summary")
            graph.add_edge("generate_chart", END)
            graph.add_edge("generate_summary", END)
            graph.add_edge("get_followup_que", END)
            graph.add_edge("handle_unanswerable", END)

            # Compile workflow
            self._workflow = graph.compile()
            logger.debug("Workflow built and compiled successfully")
        
        except Exception as e:
            logger.error(f"Error building workflow: {e}")
            raise WorkflowException(
                f"Failed to build workflow: {str(e)}",
                step="build_workflow",
            ) from e
    
    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the workflow with initial state.
        
        Args:
            initial_state: Initial state dictionary
            
        Returns:
            Final state after workflow execution
            
        Raises:
            WorkflowException: If workflow execution fails
        """
        if not self._workflow:
            raise WorkflowException("Workflow not initialized")
        
        try:
            logger.info(f"Invoking workflow with input: {initial_state.get('input_text', '')[:100]}...")
            result = self._workflow.invoke(initial_state)
            logger.info("Workflow executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error invoking workflow: {e}")
            raise WorkflowException(
                f"Workflow execution failed: {str(e)}",
                step="invoke",
            ) from e
    
    @property
    def workflow(self):
        """Get the compiled workflow."""
        return self._workflow

