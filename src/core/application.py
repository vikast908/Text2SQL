import os
import toml
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.settings import settings
from src.utils.logging import get_logger
from src.app.api.router import api_router
from src.core.lifetime import LifecycleManager
from src.middleware import ExceptionHandlerMiddleware
from src.middleware.exception import ExceptionResponseModel


logger = get_logger(__name__)

def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This factory function constructs and configures the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    try:
        logger.info("Initializing FastAPI application")
        
        # Load version from pyproject.toml
        file_path = "pyproject.toml"
        with open(file_path, "r") as toml_file:
            data = toml.loads(toml_file.read())
        
        # Create FastAPI app with version from pyproject.toml
        app = FastAPI(
            title="IRIS langgraph codebase",
            version=data["project"]["version"],
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            openapi_url="/api/openapi.json",
        )

        # Register startup and shutdown events 
        LifecycleManager.register_startup_event(app)
        LifecycleManager.register_shutdown_event(app)

        # Add middleware
        app.add_middleware(ExceptionHandlerMiddleware)

        # Include API router
        app.include_router(
            router=api_router,
            prefix="/api",
            responses={
                400: {
                    "model": ExceptionResponseModel,
                    "description": "Bad Request",
                },
                500: {
                    "model": ExceptionResponseModel,
                    "description": "Internal Server Error",
                },
            },
        )

        # Serve static files from the static directory (built React app)
        static_dir = Path(__file__).parent.parent.parent / "static"
        if static_dir.exists():
            # Mount assets directory (JS, CSS bundles from Vite build)
            assets_dir = static_dir / "assets"
            if assets_dir.exists():
                app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            
            # Catch-all route for SPA: serve index.html for all non-API routes
            # This must be added last to not interfere with API routes
            @app.get("/{full_path:path}")
            async def serve_spa(request: Request, full_path: str):
                """
                Serve the React app for all non-API routes.
                This enables client-side routing with React Router.
                """
                # Don't interfere with API routes or assets
                if full_path.startswith("api/") or full_path.startswith("assets/"):
                    return None
                
                # Check if it's a static file request (favicon, robots.txt, etc.)
                static_file = static_dir / full_path
                if static_file.exists() and static_file.is_file():
                    return FileResponse(str(static_file))
                
                # Serve index.html for all other routes (SPA routing)
                index_path = static_dir / "index.html"
                if index_path.exists():
                    return FileResponse(str(index_path))
                return {"message": "Frontend not built. Run 'cd frontend && npm run build'"}
            
            logger.info(f"Static files mounted from {static_dir}")
        else:
            logger.warning(f"Static directory not found at {static_dir}. Frontend not built yet.")

        logger.info("FastAPI application initialized successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to initialize FastAPI application: {str(e)}")
        raise