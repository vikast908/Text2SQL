"""SQL query validator using LLM."""

import re
from typing import Dict, Any, Optional
from src.utils.logging import get_logger
from .llm_client import LLMClient
from .exceptions import LLMClientException, SQLValidationException
from .models import Text2SQLState

logger = get_logger(__name__)

# Maximum rows to return from any query (safety limit)
MAX_QUERY_ROWS = 1000


class SQLValidator:
    """Validator for SQL queries using LLM."""
    
    SYSTEM_PROMPT = """
    You are an expert SQL validator. Your task is to validate SQL queries against a database schema.
    
    Analyze the provided SQL query and check:
    1. Syntax correctness (valid SQL syntax)
    2. Schema compliance (tables and columns exist in the metadata)
    3. Schema qualification (tables use causal_inference schema)
    4. Column existence (all referenced columns exist in their respective tables)
    5. Join correctness (joins are valid based on relationships)
    6. Data type compatibility (operations are compatible with column types)
    
    Respond with ONLY a single word: "VALID" if the query is valid, or "INVALID" if it has any issues.
    Do not provide explanations, just the single word response.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize SQL validator.
        
        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()
        logger.debug("SQL validator initialized")
    
    def _ensure_limit(self, sql_query: str, max_rows: int = MAX_QUERY_ROWS) -> str:
        """
        Ensure SQL query has a LIMIT clause to prevent huge result sets.

        Args:
            sql_query: SQL query string
            max_rows: Maximum rows to return

        Returns:
            SQL query with LIMIT clause added or adjusted
        """
        if not sql_query:
            return sql_query

        # Remove trailing semicolon for processing
        working_query = sql_query.rstrip().rstrip(';').rstrip()

        # Check if query already has a LIMIT clause (case-insensitive)
        limit_pattern = re.compile(r'\bLIMIT\s+(\d+)\s*$', re.IGNORECASE)
        match = limit_pattern.search(working_query)

        if match:
            # Query has LIMIT, ensure it's not too high
            existing_limit = int(match.group(1))
            if existing_limit > max_rows:
                logger.warning(f"Query LIMIT {existing_limit} exceeds max {max_rows}, reducing")
                working_query = limit_pattern.sub(f'LIMIT {max_rows}', working_query)
        else:
            # No LIMIT clause, add one
            working_query = f"{working_query} LIMIT {max_rows}"
            logger.debug(f"Added LIMIT {max_rows} to query")

        return working_query

    def clean_sql_query(self, sql_query: str) -> str:
        """
        Clean SQL query by removing markdown formatting and ensuring safety limits.

        Args:
            sql_query: Raw SQL query (may contain markdown)

        Returns:
            Cleaned SQL query string with LIMIT safeguard
        """
        if not sql_query or not isinstance(sql_query, str):
            return ""

        cleaned_query = sql_query.strip()

        # Remove markdown code fences (```sql, ```, etc.)
        if cleaned_query.startswith('```'):
            # Find the first newline after ```
            first_newline = cleaned_query.find('\n')
            if first_newline != -1:
                cleaned_query = cleaned_query[first_newline + 1:]
            else:
                # No newline, just remove the ```
                cleaned_query = cleaned_query[3:]

        # Remove closing ```
        if cleaned_query.endswith('```'):
            cleaned_query = cleaned_query[:-3]

        # Strip whitespace
        cleaned_query = cleaned_query.strip()

        # Add LIMIT safeguard to prevent huge result sets
        cleaned_query = self._ensure_limit(cleaned_query)

        return cleaned_query
    
    def validate_sql_query(self, state: Text2SQLState) -> Dict[str, Any]:
        """
        Validate a SQL query using LLM and return binary result (True/False).
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with 'is_valid_sql' and 'cleaned_query' keys
            
        Raises:
            SQLValidationException: If validation fails
        """
        try:
            sql_query = state.get("generated_sql_query", "")
            
            if not sql_query or not isinstance(sql_query, str):
                return {"is_valid_sql": False, "cleaned_query": ""}
            
            # Clean the SQL query
            cleaned_query = self.clean_sql_query(sql_query)
            
            # Basic validation - check if query is empty
            if not cleaned_query:
                return {"is_valid_sql": False, "cleaned_query": cleaned_query}
            
            # Get metadata for validation
            metadata = state.get("metadata", "")
            if not metadata:
                logger.warning("No metadata available for validation, performing basic validation only")
                return {"is_valid_sql": True, "cleaned_query": cleaned_query}
            
            user_prompt = f"""
            Database schema metadata:
            {metadata}
            
            SQL Query to validate:
            {cleaned_query}
            
            Is this SQL query valid? Respond with only "VALID" or "INVALID".
            """
            
            logger.debug(f"Validating SQL query: {cleaned_query[:100]}...")
            
            validation_result = self.llm_client.generate_completion(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model="gpt-4o-mini",
                temperature=0.1,  # Low temperature for consistent validation
            )
            
            validation_result = validation_result.strip().upper()
            
            # Check if response indicates valid query
            is_valid = "VALID" in validation_result and "INVALID" not in validation_result
            
            logger.debug(f"SQL validation result: {'VALID' if is_valid else 'INVALID'}")
            
            return {"is_valid_sql": is_valid, "cleaned_query": cleaned_query}
        
        except LLMClientException as e:
            logger.error(f"LLM error during validation: {e}")
            # Fallback: return False if LLM validation fails
            cleaned_query = self.clean_sql_query(state.get("generated_sql_query", ""))
            return {"is_valid_sql": False, "cleaned_query": cleaned_query}
        
        except Exception as e:
            logger.error(f"Unexpected error during SQL validation: {e}")
            raise SQLValidationException(
                f"Unexpected error during SQL validation: {str(e)}",
                sql_query=state.get("generated_sql_query", ""),
                details={"error_type": type(e).__name__},
            ) from e

