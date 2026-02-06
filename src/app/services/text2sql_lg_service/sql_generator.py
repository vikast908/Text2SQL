"""SQL query generator using LLM."""

from typing import Dict, Any, Optional
from src.utils.logging import get_logger
from .llm_client import LLMClient
from .exceptions import LLMClientException
from .models import Text2SQLState

logger = get_logger(__name__)


class SQLGenerator:
    """Generator for SQL queries from natural language."""
    
    SYSTEM_PROMPT = """
    You are an expert SQL query generator for PostgreSQL.
    You will be given:
    - A natural language question
    - Database metadata (tables, columns, data types, relationships)

    Your task is to generate only a single valid SQL query that answers the question.

    CRITICAL - Schema Compliance:
    - ONLY use tables and columns that are EXPLICITLY defined in the provided metadata
    - If the question asks about data that does NOT exist in the schema (e.g., customers, acquisition channels, users, etc.), respond with EXACTLY:
      UNANSWERABLE: [brief explanation of what data is missing]
    - NEVER invent or assume tables/columns that are not in the metadata
    - Check the metadata carefully before generating SQL

    Mandatory Rules:
    - Always fully qualify table names using the causal_inference schema
      (e.g., causal_inference.table_name)
    - Never assume or use the public schema
    - Use only tables and columns explicitly defined in the metadata
    - Infer joins strictly from provided relationships
    - Do not add assumptions or fabricate fields
    - Do not include explanations, comments, markdown, or extra text
    - Output only executable SQL (or UNANSWERABLE message)
    - Use PostgreSQL syntax

    IMPORTANT - Date Handling:
    - Date columns are stored as VARCHAR in 'MM/DD/YYYY' format (US date format)
    - When working with date columns, ALWAYS use TO_DATE(column_name, 'MM/DD/YYYY')
    - For date comparisons: TO_DATE(date_column, 'MM/DD/YYYY') >= CURRENT_DATE - INTERVAL '1 month'
    - For date grouping/truncation: DATE_TRUNC('month', TO_DATE(date_column, 'MM/DD/YYYY'))
    - Never use CAST(date_column AS DATE) directly - it will fail
    """
    
    def __init__(self):
        """
        Initialize SQL generator.
        
        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = LLMClient()
        logger.debug("SQL generator initialized")
    
    def generate_sql(self, state: Text2SQLState) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with 'generated_sql_query' key
            
        Raises:
            LLMClientException: If SQL generation fails
        """
        try:
            input_text = state.get("input_text", "")
            metadata = state.get("metadata", "")
            
            if not input_text:
                raise ValueError("input_text is required in state")
            
            if not metadata:
                raise ValueError("metadata is required in state")
            
            user_prompt = f"""
            Question: {input_text}
            Database schema metadata: {metadata}
            """
            
            logger.debug(f"Generating SQL for question: {input_text[:100]}...")
            
            generated_sql_query = self.llm_client.generate_completion(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model="gpt-4o-mini",
                temperature=0.3,  # Lower temperature for more consistent SQL
            )

            # Check if the query is unanswerable
            if generated_sql_query.strip().upper().startswith("UNANSWERABLE"):
                logger.info(f"Query cannot be answered: {generated_sql_query}")
                return {
                    "generated_sql_query": "",
                    "is_unanswerable": True,
                    "unanswerable_reason": generated_sql_query.replace("UNANSWERABLE:", "").strip(),
                }

            logger.debug(f"SQL generated successfully: {generated_sql_query[:100]}...")

            return {"generated_sql_query": generated_sql_query}
        
        except LLMClientException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating SQL: {e}")
            raise LLMClientException(
                f"Failed to generate SQL query: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e

