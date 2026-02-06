import sys
import uvicorn
from src.settings import settings
from src.utils.logging import get_logger
from src.logging import configure_logging

# Configure logging first to prevent duplicates
configure_logging()

# Initialize logger
logger = get_logger(__name__)

def log_system_info() -> None:
    """Log detailed system information at startup."""
    logger.info("Starting IRIS LangGraph Backend Service")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Workers: {settings.workers_count}")
    logger.info(f"Log Level: {settings.log_level.lower()}")

def main() -> None:
    """Entrypoint of the application."""
    try:
        log_system_info()
                 
        uvicorn.run(
            "src.core.application:get_app",
            workers=settings.workers_count,
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            reload_dirs=["/usr/local/lib/python3.10/site-packages", "./src"],
            log_level=settings.log_level.lower(),
            factory=True,
            access_log=False,  # Disable uvicorn access logs to prevent duplicates
            server_header=False,  # Hide server header for security
        )
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()