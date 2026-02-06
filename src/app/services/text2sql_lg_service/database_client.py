"""Database client for PostgreSQL connections."""

from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import psycopg2
from psycopg2 import OperationalError, DatabaseError, pool
from psycopg2.extras import RealDictCursor

from src.settings import settings
from src.utils.logging import get_logger
from .exceptions import DatabaseConnectionException, SQLExecutionException

logger = get_logger(__name__)


class DatabaseClient:
    """Client for PostgreSQL database operations."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[str] = None,
        dbname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 5,
    ):
        """
        Initialize database client.
        
        Args:
            host: Database host (defaults to settings)
            port: Database port (defaults to settings)
            dbname: Database name (defaults to settings)
            user: Database user (defaults to settings)
            password: Database password (defaults to settings)
            min_connections: Minimum connection pool size
            max_connections: Maximum connection pool size
        """
        self.host = host or settings.db.POSTGRES_DB_HOST
        self.port = port or settings.db.POSTGRES_DB_PORT or "5432"
        self.dbname = dbname or settings.db.POSTGRES_DB_NAME
        self.user = user or settings.db.POSTGRES_DB_USERNAME
        self.password = password or settings.db.POSTGRES_DB_PASSWORD
        
        self._connection_pool: Optional[pool.ThreadedConnectionPool] = None
        self._initialize_connection_pool(min_connections, max_connections)
    
    def _initialize_connection_pool(
        self,
        min_connections: int,
        max_connections: int,
    ) -> None:
        """Initialize connection pool."""
        try:
            # Password is optional (can be empty string or None for passwordless auth)
            if not all([self.host, self.dbname, self.user]):
                missing_vars = []
                if not self.host:
                    missing_vars.append("POSTGRES_HOST")
                if not self.dbname:
                    missing_vars.append("POSTGRES_DB")
                if not self.user:
                    missing_vars.append("POSTGRES_USER")
                
                raise DatabaseConnectionException(
                    f"Missing required database configuration: {', '.join(missing_vars)}",
                    details={"missing_variables": missing_vars},
                )
            
            # Use empty string if password is None
            password = self.password if self.password is not None else ""
            
            self._connection_pool = pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                host=self.host,
                port=int(self.port),
                dbname=self.dbname,
                user=self.user,
                password=password,
            )
            logger.debug("Database connection pool initialized successfully")
        
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionException(
                f"Failed to connect to database: {str(e)}",
                details={"error_type": "operational_error"},
            ) from e
        
        except Exception as e:
            logger.error(f"Unexpected error initializing connection pool: {e}")
            raise DatabaseConnectionException(
                f"Unexpected error initializing connection pool: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e
    
    @contextmanager
    def get_connection(self):
        """
        Get a database connection from the pool.
        
        Yields:
            psycopg2 connection object
            
        Raises:
            DatabaseConnectionException: If connection cannot be obtained
        """
        if not self._connection_pool:
            raise DatabaseConnectionException("Connection pool not initialized")
        
        conn = None
        try:
            conn = self._connection_pool.getconn()
            if not conn:
                raise DatabaseConnectionException("Failed to get connection from pool")
            yield conn
        except pool.PoolError as e:
            logger.error(f"Pool error: {e}")
            raise DatabaseConnectionException(
                f"Failed to get connection from pool: {str(e)}",
                details={"error_type": "pool_error"},
            ) from e
        finally:
            if conn:
                self._connection_pool.putconn(conn)
    
    def execute_query(
        self,
        sql_query: str,
        fetch_all: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            sql_query: SQL query to execute
            fetch_all: Whether to fetch all results (default: True)
            
        Returns:
            List of dictionaries representing rows
            
        Raises:
            SQLExecutionException: If query execution fails
        """
        if not sql_query or not sql_query.strip():
            raise SQLExecutionException("SQL query cannot be empty", sql_query=sql_query)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    logger.debug(f"Executing SQL query: {sql_query[:100]}...")
                    cursor.execute(sql_query)
                    
                    if fetch_all:
                        rows = cursor.fetchall()
                        results = [dict(row) for row in rows]
                    else:
                        results = []
                    
                    conn.commit()
                    logger.debug(f"Query executed successfully. Rows returned: {len(results)}")
                    return results
        
        except DatabaseError as e:
            logger.error(f"Database error executing query: {e}")
            raise SQLExecutionException(
                f"Database error executing query: {str(e)}",
                sql_query=sql_query,
                details={"error_type": "database_error", "pgcode": getattr(e, "pgcode", None)},
            ) from e
        
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise SQLExecutionException(
                f"Unexpected error executing query: {str(e)}",
                sql_query=sql_query,
                details={"error_type": type(e).__name__},
            ) from e
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is successful
            
        Raises:
            DatabaseConnectionException: If connection test fails
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            logger.debug("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise DatabaseConnectionException(
                f"Database connection test failed: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e
    
    def close(self) -> None:
        """Close all connections in the pool."""
        if self._connection_pool:
            try:
                self._connection_pool.closeall()
                logger.debug("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")

