"""SQL query executor."""

from typing import Dict, Any, Optional, List
from src.utils.logging import get_logger
from .database_client import DatabaseClient
from .exceptions import SQLExecutionException
from .models import Text2SQLState

logger = get_logger(__name__)


class SQLExecutor:
    """Executor for SQL queries."""
    
    def __init__(self, database_client: Optional[DatabaseClient] = None):
        """
        Initialize SQL executor.
        
        Args:
            database_client: Database client instance (creates new one if not provided)
        """
        self.database_client = database_client or DatabaseClient()
        logger.debug("SQL executor initialized")
    
    def execute_sql(self, state: Text2SQLState) -> Dict[str, Any]:
        """
        Execute a SQL query and return the results.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with 'data' key containing query results
            
        Raises:
            SQLExecutionException: If query execution fails
        """
        try:
            # Use cleaned_query if available, otherwise fall back to generated_sql_query
            sql_to_execute = state.get("cleaned_query") or state.get("generated_sql_query")
            
            if not sql_to_execute:
                raise SQLExecutionException(
                    "No SQL query available to execute",
                    sql_query=None,
                )
            
            logger.debug(f"Executing SQL query: {sql_to_execute[:100]}...")
            
            results = self.database_client.execute_query(sql_to_execute, fetch_all=True)
            
            logger.debug(f"SQL query executed successfully. Rows returned: {len(results)}")
            
            return {"data": results}
        
        except SQLExecutionException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing SQL: {e}")
            sql_query = state.get("cleaned_query") or state.get("generated_sql_query")
            raise SQLExecutionException(
                f"Unexpected error executing SQL query: {str(e)}",
                sql_query=sql_query,
                details={"error_type": type(e).__name__},
            ) from e

