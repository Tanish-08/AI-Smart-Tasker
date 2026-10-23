"""FastAPI application entry point."""
import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.utils.database import init_database, create_tables, close_database
from backend.app.utils.llm_client import LLMClient
from backend.app.dependencies import load_config, set_llm_client
from backend.app.endpoint import (
    task_routes,
    summary_routes,
    analytics_routes,
    deadline_routes,
)

# Load local development settings before configuring CORS.
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting AI Task Manager backend...")

    try:
        # Load configuration
        config = load_config()

        # Initialize database
        init_database(config)
        create_tables()
        logger.info("Database initialized")

        # Initialize LLM client
        llm_client = LLMClient(config)
        set_llm_client(llm_client)
        logger.info("LLM client initialized")

        # Check LLM health
        if llm_client.health_check():
            logger.info("LLM service is healthy")
        else:
            logger.warning("LLM service health check failed, but continuing...")

        logger.info("Application startup complete")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI Task Manager backend...")

    try:
        # Close database connections
        close_database()
        logger.info("Database connections closed")

        logger.info("Application shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="AI Task Manager API",
    description="Backend API for AI-powered task management with deadline motivation",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.

    Args:
        request: Request object
        exc: Exception instance

    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "service": "AI Task Manager API", "version": "1.0.0"}


# Include routers
app.include_router(task_routes.router)
app.include_router(summary_routes.router)
app.include_router(analytics_routes.router)
app.include_router(deadline_routes.router)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        API information
    """
    return {
        "service": "AI Task Manager API",
        "version": "1.0.0",
        "description": "Backend API for AI-powered task management",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    bind_host = os.getenv("BIND_HOST", "127.0.0.1")
    bind_port = int(os.getenv("BIND_PORT", "8000"))
    is_development = os.getenv("APP_ENV", "development") == "development"

    uvicorn.run(
        "backend.app.main:app",
        host=bind_host,
        port=bind_port,
        reload=is_development,
        log_level="info",
    )
